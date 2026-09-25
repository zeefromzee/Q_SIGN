"""Append only, hash chained ledger of consumed key indices."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass


@dataclass(frozen=True)
class Entry:
    start: int
    length: int
    verdict: str
    prev_hash: str
    hash: str


def _digest(prev: str, start: int, length: int, verdict: str) -> str:
    return hashlib.sha256(f"{prev}|{start}|{length}|{verdict}".encode()).hexdigest()


class HashChainedLedger:
    def __init__(self):
        self.entries: list[Entry] = []
        self._used: set[int] = set()

    @property
    def head(self) -> str:
        return self.entries[-1].hash if self.entries else "0" * 64

    def is_fresh(self, start: int, length: int) -> bool:
        return not any(i in self._used for i in range(start, start + length))

    def record(self, start: int, length: int, verdict: str) -> Entry:
        prev = self.head
        entry = Entry(start, length, verdict, prev, _digest(prev, start, length, verdict))
        self.entries.append(entry)
        self._used.update(range(start, start + length))
        return entry

    def verify_chain(self) -> bool:
        prev = "0" * 64
        for e in self.entries:
            if e.prev_hash != prev or e.hash != _digest(prev, e.start, e.length, e.verdict):
                return False
            prev = e.hash
        return True
