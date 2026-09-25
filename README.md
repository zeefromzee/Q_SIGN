# QSIGN

**Statistical threat detection for teleportation based quantum digital signatures.**
Smart India Hackathon 2026, problem statement 26141, Egreen Quanta LLP. Team Diva.

Live demo: https://zeefromzee.github.io/qsign/

QSIGN simulates a complete teleportation based quantum digital signature (QDS) protocol with Qiskit Aer and guards it with a detection engine built only on Pauli measurement statistics and fixed threshold rules. It detects forgery, impersonation, replay, quantum channel manipulation and unauthorised verification, and it explains every decision. No machine learning is used anywhere, as the problem statement requires.

## How the protocol works

| Stage | What happens |
|---|---|
| Key distribution | Entangled Bell pairs are shared between signer and verifier; each pair gets a ledger index |
| Signing | The private key picks the Z or X basis; each message bit is prepared as a Pauli eigenstate |
| Teleportation | A Bell measurement on the message qubit and the signer half gives two classical bits |
| Verification | The verifier applies X then Z corrections and measures in the committed basis |
| Detection | Ledger, CHSH and mismatch tests produce ACCEPT, RETEST, REJECT or ALERT |

## Detection rules

1. **Ledger test**: every key index may be consumed once. A reused index raises ALERT (replay).
2. **CHSH test**: reserved pairs are measured at four angle settings. A value below 2.6 raises ALERT (channel tampering). Ideal value is 2.828, the classical limit is 2.
3. **Mismatch test**: mismatch at most 7 percent gives ACCEPT, at least 11 percent gives REJECT, anything between gives RETEST.
4. **Forgery bound**: Hoeffding's inequality bounds the chance that an optimal cloning forger, with 14.6 percent expected mismatch, passes the 7 percent threshold. At 1024 pairs the bound is 6.3E-6.

## Results from `python -m qsign.cli`

| Scenario | Verdict | Mismatch | CHSH |
|---|---|---|---|
| honest | ACCEPT | 0.59% | 2.817 |
| forgery | REJECT | 25.29% | 2.813 |
| impersonation | REJECT | 48.93% | 2.727 |
| replay | ALERT | 0.59% | 2.733 |
| interception | ALERT | 13.77% | 2.150 |
| noise_injection | ALERT | 13.57% | 2.120 |
| rogue_verifier | REJECT | 25.78% | 2.823 |

Values vary slightly between seeds because quantum measurement is random; the verdicts are stable across seeds.

## Run it

```bash
pip install -r requirements.txt
python -m qsign.cli            # attack laboratory, all seven scenarios
pytest -v                      # nine automated tests
uvicorn qsign.api:app --reload # REST API on port 8000
```

Open `frontend/index.html` in a browser for the interactive verifier console,
or use the hosted copy at https://zeefromzee.github.io/qsign/

## Repository layout

```
qsign/protocol.py    Qiskit circuits for signing, teleportation, attacks and the CHSH test
qsign/detection.py   threshold rules, verdicts and the Hoeffding forgery bound
qsign/ledger.py      append only, hash chained key ledger
qsign/api.py         FastAPI service: /scenarios, /verify, /ledger
qsign/cli.py         command line attack laboratory
tests/               pytest suite covering every attack class
frontend/            interactive verifier console
docs/protocol.md     mathematical model
```

## References

Gottesman and Chuang, Quantum Digital Signatures, arXiv:quant-ph/0105032.
Bennett et al., Teleporting an unknown quantum state, Phys. Rev. Lett. 70, 1895 (1993).
Clauser, Horne, Shimony and Holt, Phys. Rev. Lett. 23, 880 (1969).
Hoeffding, J. Amer. Stat. Assoc. 58, 13 (1963).

## License

MIT
