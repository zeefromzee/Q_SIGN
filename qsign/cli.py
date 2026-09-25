"""Run every attack scenario and print the detection results as a table."""
from __future__ import annotations

import argparse

from .detection import DetectionEngine
from .protocol import SCENARIOS, QDSConfig


def main(argv=None):
    ap = argparse.ArgumentParser(description="QSIGN attack laboratory")
    ap.add_argument("--bits", type=int, default=1024)
    ap.add_argument("--chsh", type=int, default=2400)
    ap.add_argument("--noise", type=float, default=0.02)
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args(argv)
    eng = DetectionEngine()
    print(f"{'scenario':<16}{'verdict':<9}{'mismatch':>9}{'Z basis':>9}{'X basis':>9}{'CHSH':>8}  reason")
    for i, sc in enumerate(SCENARIOS):
        cfg = QDSConfig(n_bits=a.bits, chsh_pairs=a.chsh, channel_noise=a.noise, seed=a.seed + i)
        v = eng.evaluate(sc, cfg, key_start=0 if sc == "replay" else None)
        print(f"{sc:<16}{v.decision:<9}{v.mismatch:>9.2%}{v.mismatch_z:>9.2%}{v.mismatch_x:>9.2%}{v.chsh:>8.3f}  {v.reason}")
    print(f"\nledger entries: {len(eng.ledger.entries)}, hash chain valid: {eng.ledger.verify_chain()}")
    print(f"forgery bound at {a.bits} pairs: {eng.forgery_bound(a.bits):.2e}")


if __name__ == "__main__":
    main()
