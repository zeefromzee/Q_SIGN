import pytest

from qsign import DetectionEngine, HashChainedLedger, QDSConfig

CFG = dict(n_bits=512, chsh_pairs=2400, channel_noise=0.02)


def run(scenario, seed, engine=None, key_start=None):
    engine = engine or DetectionEngine()
    return engine.evaluate(scenario, QDSConfig(seed=seed, **CFG), key_start=key_start)


def test_honest_signature_is_accepted():
    v = run("honest", 1)
    assert v.decision == "ACCEPT" and v.mismatch < 0.05 and v.chsh > 2.6


def test_noise_free_teleportation_is_exact():
    v = DetectionEngine().evaluate("honest", QDSConfig(n_bits=256, chsh_pairs=800, channel_noise=0.0, seed=2))
    assert v.mismatch == 0.0


@pytest.mark.parametrize("scenario,low,high", [("forgery", 0.18, 0.32), ("impersonation", 0.42, 0.58),
                                               ("rogue_verifier", 0.18, 0.32)])
def test_signature_attacks_are_rejected(scenario, low, high):
    v = run(scenario, 3)
    assert v.decision == "REJECT" and low < v.mismatch < high


@pytest.mark.parametrize("scenario", ["interception", "noise_injection"])
def test_channel_attacks_raise_alert(scenario):
    v = run(scenario, 4)
    assert v.decision == "ALERT" and v.chsh < 2.6


def test_replay_is_caught_by_ledger():
    eng = DetectionEngine()
    assert run("honest", 5, eng).decision == "ACCEPT"
    again = run("replay", 6, eng, key_start=0)
    assert again.decision == "ALERT" and not again.ledger_fresh


def test_ledger_detects_tampering():
    led = HashChainedLedger()
    led.record(0, 10, "ACCEPT"); led.record(10, 10, "REJECT")
    assert led.verify_chain()
    e = led.entries[0]
    led.entries[0] = e.__class__(e.start, e.length, "REJECT", e.prev_hash, e.hash)
    assert not led.verify_chain()
