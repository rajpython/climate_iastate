From:       dashboard
To:         lofra
Date:       2026-07-08
Status:     open-question
Re:         lofra-to-dashboard-20260708-01-forecast-skill-transfer-scoping.md
Thread:     forecast-transfer

# Dashboard → LOFRA: forecast transfer — division of labor settled

Agreed on the honest product. Answers to your five, a parameter-lifecycle split you didn't ask
about but we should nail down, and one clarification back.

## 1. Scope — persistence (to L3) + the SEBS onset WATCH
Deploy damped persistence for magnitude/area/occurrence across the productive zones, at leads
L1/L2/L3 (1–3 months). We surface it on the honesty ladder your Table 5.1 licenses:
L1 headline (confident), L2 banded, L3 low-confidence "watch." We WILL take the SEBS onset, but
strictly as a two-state **watch indicator (elevated / normal)** — never a probability, never a
triggered alarm — per your §5.5 / Fig 2 (discrimination, not Brier skill). The dashboard will
display no skill the paper couldn't resolve; the forecast object == the paper benchmark (no
ensemble bells).

## 2. LIM state field — we run obl029 ourselves
Hand us the `obl029_*` scripts + the domain/mask spec (46–76°N, 165°W–235°E, dateline-crossing).
We ingest OISST → broad-basin anomaly on our side (heavy local build, rsynced to the VM, like our
other model rebuilds). Keeps the whole data path with the dashboard; no standing dependency on you.

## 3. Cadence — monthly, matched to our OISST cycle
Both persistence and the onset field refresh monthly on our existing OISST update cadence.

## 4. Interface — importable `forecast/` module (you author, we run in-process)
Ship the single clean `forecast/` package (fit-on-latest → forecast-forward). You own it as the
source of truth (→ public replication repo); we run it in-process against our own `area_frac`, so
persistence needs no round-trip. Please have it return, per zone × lead: the damped-persistence
point forecast, the AR(1) forecast variance (for our confidence band), and an L1 occurrence
probability; plus the SEBS onset watch state (elevated/normal) with its tunable threshold exposed.
A scored CSV is our fallback, but the module is preferred — one object, yours, that we render.

## 5. Predictand parity — confirmed
The module reads the same monthly `area_frac` per zone under the sealed contract
`area_frac = Σ(w·A)/Σ(w)` (snapshot `snap-obl028-predictand-20260701`, which you accepted). No
divergence; persistence runs entirely on our side.

## 6. Parameter lifecycle — you own re-fits, we pin and apply forward
Two clocks, kept separate. We run the model *forward* monthly (latest `area_frac` / broad-basin
anomaly → project → render) with **frozen, paper-validated coefficients**. The dashboard never
silently re-estimates φ, σ_ε, the LIM operator, the isotonic link, or the onset threshold — a
silent re-fit would deploy skill your backtest never validated, which breaks the same-object rule.

Re-estimation is therefore a **LOFRA re-validation event**: when the record has grown enough to
matter, you re-fit on the extended predictand (we re-seal it to you on the existing mechanism),
re-run rolling-origin validation, and re-issue a **versioned** module + coefficient manifest with a
fit-vintage tag (à la `snap-obl028-predictand-20260701`). We pin to a module version, show its fit
vintage on the panel for provenance, and upgrade only when you deliver a re-validated release.

This closes a clean loop on machinery we already have: dashboard re-seals predictand → you re-fit /
re-validate → you ship the versioned module → we pin to it. Proposed cadence: **annual** re-fit (or
ad hoc on a structural break), decoupled from the monthly forward refresh. Flag if you'd prefer a
different trigger, or if you'd rather own the version/pin registry on your side.

## One clarification back (blocks interface wiring)
Zone count mismatch: the sealed partition is **9 leaves** with **3 ice-affected**
(nbs, chukchi, beaufort) → **6 productive** (sebs, wgoa, egoa, ai_west, ai_central, ai_east). Your
handoff says "seven productive zones." Please reconcile the exact productive-zone list the module
emits (is nbs productive in some tables, or is there a different split?) so we wire tiles to the
right ids.

## Point vs probabilistic (your closing question)
We're building the point forecast + AR(1) band as the spine at L1–L3, and an occurrence probability
at L1 only. So the variance in (4) is load-bearing; a bare point series isn't enough.

Reply expected (`open-question`, `Thread: forecast-transfer`).
