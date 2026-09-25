"""Threshold based detection engine. Every rule is a fixed statistical test; no learning."""
from __future__ import annotations

import math
from dataclasses import dataclass

from .ledger import HashChainedLedger
from .protocol import QDSConfig, chsh_test, sign_and_verify

OPTIMAL_CLONING_ERROR = 0.5 - math.sqrt(2) / 4   # about 0.146


@dataclass
class Verdict:
    decision: str        # ACCEPT, RETEST, REJECT or ALERT
    reason: str
    mismatch: float
    mismatch_z: float
    mismatch_x: float
    chsh: float
    ledger_fresh: bool
    forgery_bound: float


class DetectionEngine:
    def __init__(self, accept_threshold=0.07, reject_threshold=0.11, chsh_alert=2.6):
        self.t_accept, self.t_reject, self.chsh_alert = accept_threshold, reject_threshold, chsh_alert
        self.ledger = HashChainedLedger()
        self._next_index = 0

    def forgery_bound(self, n: int) -> float:
        """Hoeffding bound on the chance an optimal cloning forger stays under the accept threshold."""
        gap = max(0.0, OPTIMAL_CLONING_ERROR - self.t_accept)
        return math.exp(-2 * n * gap * gap)

    def evaluate(self, scenario: str, cfg: QDSConfig, key_start: int | None = None) -> Verdict:
        start = self._next_index if key_start is None else key_start
        fresh = self.ledger.is_fresh(start, cfg.n_bits)
        run_as = "honest" if scenario == "replay" else scenario
        stats = sign_and_verify(run_as, cfg)
        s = chsh_test(run_as, cfg)
        mz = stats["mismatch"]["Z"] / max(1, stats["total"]["Z"])
        mx = stats["mismatch"]["X"] / max(1, stats["total"]["X"])
        m = (stats["mismatch"]["Z"] + stats["mismatch"]["X"]) / stats["n_bits"]
        if not fresh:
            d, why = "ALERT", f"replay: key index {start} is already in the ledger"
        elif s < self.chsh_alert:
            d, why = "ALERT", f"channel tampering: CHSH {s:.3f} below {self.chsh_alert}"
        elif m <= self.t_accept:
            d, why = "ACCEPT", f"mismatch within {self.t_accept:.0%} threshold"
        elif m >= self.t_reject:
            d, why = "REJECT", f"mismatch above {self.t_reject:.0%} reject limit"
        else:
            d, why = "RETEST", "mismatch in retest band, collect more pairs"
        if fresh:
            self.ledger.record(start, cfg.n_bits, d)
            self._next_index = start + cfg.n_bits
        return Verdict(d, why, m, mz, mx, s, fresh, self.forgery_bound(cfg.n_bits))
