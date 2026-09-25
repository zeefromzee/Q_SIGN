"""Teleportation based quantum digital signature, simulated with Qiskit Aer.

Qubit layout for every signed bit:
    q0  message qubit prepared by the signer as a Pauli eigenstate
    q1  signer half of the Bell pair (qubit A)
    q2  verifier half of the Bell pair (qubit B)

Signing:      Bell pair on q1, q2; encode bit on q0 in the Z or X basis;
              Bell basis measurement on q0, q1 gives classical bits m1, m2.
Verification: apply X if m2 = 1 and Z if m1 = 1 on q2, then measure q2 in the
              basis committed in the private key. An honest run reproduces the bit.

Bits that share the same (bit, basis, attacker choice) run as one circuit with many
shots, so a 1024 bit signature needs only a handful of simulator calls.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
from qiskit_aer import AerSimulator
from qiskit_aer.noise import depolarizing_error

SCENARIOS = ("honest", "forgery", "impersonation", "replay", "interception", "noise_injection", "rogue_verifier")


@dataclass
class QDSConfig:
    n_bits: int = 1024              # Bell pairs used by the signature
    chsh_pairs: int = 2400          # Bell pairs reserved for the CHSH test
    channel_noise: float = 0.02     # depolarising probability on the verifier half
    attack_noise: float = 0.25      # extra depolarising probability during noise injection
    intercept_fraction: float = 0.5 # share of pairs measured by an eavesdropper
    seed: int | None = None
    rng: np.random.Generator = field(init=False)

    def __post_init__(self):
        self.rng = np.random.default_rng(self.seed)


def _channel(qc: QuantumCircuit, qubit: int, p: float) -> None:
    """Depolarising channel acting on the verifier half while it travels to the verifier."""
    if p > 0:
        qc.append(depolarizing_error(min(p, 1.0), 1).to_instruction(), [qubit])


def _measure_resend(qc, qubit, creg, basis):
    if basis == "X": qc.h(qubit)
    qc.measure(qubit, creg); qc.reset(qubit)
    with qc.if_test((creg, 1)): qc.x(qubit)
    if basis == "X": qc.h(qubit)


def _signature_circuit(bit, basis, signer_basis, impersonate, eve, rogue, p) -> QuantumCircuit:
    q = QuantumRegister(3, "q")
    m1, m2 = ClassicalRegister(1, "m1"), ClassicalRegister(1, "m2")
    e, out = ClassicalRegister(1, "e"), ClassicalRegister(1, "out")
    qc = QuantumCircuit(q, m1, m2, e, out)
    qc.h(1); qc.cx(1, 2)
    _channel(qc, 2, p)                           # verifier half crosses the quantum channel
    if eve is not None:                          # eavesdropper measures and resends qubit B
        _measure_resend(qc, 2, e, eve)
    if bit: qc.x(0)
    if signer_basis: qc.h(0)
    if impersonate:                              # attacker holds no Bell pair, sends random bits
        qc.reset(0); qc.h(0); qc.measure(0, m1); qc.reset(0); qc.h(0); qc.measure(0, m2)
    else:
        qc.cx(0, 1); qc.h(0); qc.measure(0, m1); qc.measure(1, m2)
    if rogue is not None:                        # third party measures before the verifier
        _measure_resend(qc, 2, e, rogue)
    with qc.if_test((m2, 1)): qc.x(2)
    with qc.if_test((m1, 1)): qc.z(2)
    if basis: qc.h(2)
    qc.measure(2, out)
    return qc


def _noise(cfg: QDSConfig, scenario: str) -> float:
    return cfg.channel_noise + (cfg.attack_noise if scenario == "noise_injection" else 0.0)


def _sim(cfg: QDSConfig, scenario: str) -> AerSimulator:
    return AerSimulator()


def _run(sim: AerSimulator, qc: QuantumCircuit, shots: int, cfg: QDSConfig) -> dict:
    """Each circuit gets its own seed so shots are independent yet reproducible."""
    return sim.run(qc, shots=shots, seed_simulator=int(cfg.rng.integers(1 << 30))).result().get_counts()


def sign_and_verify(scenario: str, cfg: QDSConfig) -> dict:
    """Simulate one signature under a scenario and return per basis mismatch counts."""
    if scenario not in SCENARIOS:
        raise ValueError(f"unknown scenario {scenario}")
    sim, rng, n = _sim(cfg, scenario), cfg.rng, cfg.n_bits
    bits = rng.integers(0, 2, n)
    basis = rng.integers(0, 2, n)
    signer_basis = rng.integers(0, 2, n) if scenario == "forgery" else basis
    eve = (np.where(rng.random(n) < cfg.intercept_fraction, rng.integers(0, 2, n), -1)
           if scenario == "interception" else np.full(n, -1))
    rogue = rng.integers(0, 2, n) if scenario == "rogue_verifier" else np.full(n, -1)

    groups: dict[tuple, int] = {}
    for i in range(n):
        key = (int(bits[i]), int(basis[i]), int(signer_basis[i]), int(eve[i]), int(rogue[i]))
        groups[key] = groups.get(key, 0) + 1

    mismatch, total = {"Z": 0, "X": 0}, {"Z": 0, "X": 0}
    for (b, bs, sb, ev, rg), count in groups.items():
        qc = _signature_circuit(b, bs, sb, scenario == "impersonation",
                                None if ev < 0 else "ZX"[ev], None if rg < 0 else "ZX"[rg], _noise(cfg, scenario))
        res = _run(sim, qc, count, cfg)
        wrong = sum(v for k, v in res.items() if int(k.split()[0]) != b)
        name = "X" if bs else "Z"
        mismatch[name] += wrong; total[name] += count
    return {"mismatch": mismatch, "total": total, "n_bits": n}


def chsh_test(scenario: str, cfg: QDSConfig) -> float:
    """Estimate the CHSH value on reserved Bell pairs under the same channel conditions."""
    sim = _sim(cfg, scenario)
    a_angles, b_angles = (0.0, np.pi / 2), (np.pi / 4, -np.pi / 4)
    per = cfg.chsh_pairs // 4
    n_eve = int(round(per * cfg.intercept_fraction)) if scenario == "interception" else 0
    E = {}
    for i, ta in enumerate(a_angles):
        for j, tb in enumerate(b_angles):
            corr = 0
            for intercepted, shots in ((True, n_eve), (False, per - n_eve)):
                if shots == 0:
                    continue
                q = QuantumRegister(3, "q"); c = ClassicalRegister(3, "c")
                qc = QuantumCircuit(q, c)
                qc.h(1); qc.cx(1, 2); _channel(qc, 2, _noise(cfg, scenario))
                if intercepted:
                    qc.measure(2, 0); qc.reset(2)
                    with qc.if_test((c[0], 1)): qc.x(2)
                qc.ry(-ta, 1); qc.ry(-tb, 2); qc.measure(1, 1); qc.measure(2, 2)
                counts = _run(sim, qc, shots, cfg)
                corr += sum(v * (1 if k[0] == k[1] else -1) for k, v in counts.items())
            E[(i, j)] = corr / per
    return E[(0, 0)] + E[(0, 1)] + E[(1, 0)] - E[(1, 1)]
