# O3 First-Touch / Path Intelligence v0.3

H3 path is anchored at OPEN(t) and scans daily HIGH/LOW for sessions t,t+1,t+2. Same-session dual touches are AMBIGUOUS_SAME_SESSION; order is never fabricated.

Families: +/-0.5%, +1/-0.5%, +0.5/-1%, +/-1%.

Validation base rates show meaningful ambiguity at tight barriers: symmetric 0.5% has 18.76% ambiguous and only 0.80% neither. Symmetric 1% has 3.39% ambiguous and 12.77% neither.

Predicting direction among resolved UP/DOWN cases did not beat baseline for any family. Therefore first-touch direction is NOT SUPPORTED.

Absolute-event models produced a different result: several NEITHER and AMBIGUOUS targets improved both Brier and LogLoss. Strongest initial candidate is symmetric 1% NEITHER: Validation delta Brier +0.05837 and delta LogLoss +0.19652. This is interpreted as possible path-activity / insufficient-movement information, NOT directional edge.

No CALL/PUT permission follows. Candidate must pass temporal stability checks and be reconciled with corrected OPEN magnitude architecture before promotion. O6 remains locked.
