"""FastAPI service exposing verify, scenario and ledger endpoints."""
from __future__ import annotations

from dataclasses import asdict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .detection import DetectionEngine
from .protocol import SCENARIOS, QDSConfig

app = FastAPI(title="QSIGN", version="0.1.0")
engine = DetectionEngine()


class RunRequest(BaseModel):
    scenario: str = "honest"
    n_bits: int = 1024
    chsh_pairs: int = 2400
    channel_noise: float = 0.02
    key_start: int | None = None


@app.get("/scenarios")
def scenarios():
    return {"scenarios": list(SCENARIOS)}


@app.post("/verify")
def verify(req: RunRequest):
    if req.scenario not in SCENARIOS:
        raise HTTPException(400, "unknown scenario")
    cfg = QDSConfig(n_bits=req.n_bits, chsh_pairs=req.chsh_pairs, channel_noise=req.channel_noise)
    return asdict(engine.evaluate(req.scenario, cfg, key_start=req.key_start))


@app.get("/ledger")
def ledger():
    return {"valid": engine.ledger.verify_chain(), "entries": [asdict(e) for e in engine.ledger.entries]}
