# Mathematical model

**Key.** For each index i the source prepares the Bell state |Phi+> = (|00> + |11>)/sqrt(2) on qubits A_i (signer) and B_i (verifier), and the private key holds a basis b_i in {Z, X}.

**Signing.** Message bit m_i is encoded as |m_i> when b_i = Z and as H|m_i> when b_i = X. A Bell basis measurement on the message qubit and A_i returns two bits (m1, m2).

**Verification.** The verifier applies X^m2 then Z^m1 to B_i, which recovers the encoded state exactly in the noise free case, and measures in basis b_i. Honest mismatch is therefore zero without noise, and equals half the depolarising parameter with a depolarising channel.

**Attack signatures.**
- Forger guessing the basis: wrong basis half the time, random outcome then, so expected mismatch 25 percent.
- Optimal cloning forger: expected mismatch 1/2 minus sqrt(2)/4, about 14.6 percent.
- Impersonator without Bell pairs: verifier half is maximally mixed, expected mismatch 50 percent.
- Intercept and resend on a fraction f of pairs: CHSH falls from 2 sqrt(2) towards 2 sqrt(2)(1 minus f) plus sqrt(2) f.

**Decision.** Mismatch e over N pairs is compared with thresholds T_accept = 0.07 and T_reject = 0.11. By Hoeffding's inequality, the probability that a forger with true mismatch 0.146 shows e at most T_accept is at most exp(minus 2 N (0.146 minus T_accept) squared).
