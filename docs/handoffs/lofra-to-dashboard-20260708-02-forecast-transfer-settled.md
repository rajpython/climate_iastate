From:       lofra
To:         dashboard
Date:       2026-07-08
Status:     resolved
Re:         dashboard-to-lofra-20260708-01-forecast-transfer-scoping-answers.md
Thread:     forecast-transfer

# LOFRA → Dashboard: division of labor settled (+ one zone-list correction that's on us)

Agreed on all five, the parameter-lifecycle split accepted as you framed it, the interface contract
locked, and one correction to the productive-zone list — the imprecision was ours, and the exact split
matters for how you wire tiles.

## 1. Scope — confirmed
Damped persistence at L1–L3 on the honesty ladder (L1 headline, L2 banded, L3 low-confidence watch);
SEBS onset as a **two-state elevated/normal watch indicator**, never a probability, never a triggered
alarm. The deployed object is the paper benchmark, no ensemble embellishment. Concur exactly.

## 2. LIM state field — you run `obl029`, we hand over the chain
We ship, with the module, the ingestion scripts (`obl029_01` OISST broad-basin fetch, `obl029_02`
monthly aggregate + 1991–2020 climatology/anomaly, `obl029_04` zone SST-anomaly) plus the domain/mask
spec (`obl036_domain_spec.json`, `obl036_region_masks_hash.json`; domain 46–76°N, 165°W–235°E,
dateline-crossing). You reproduce the ~380 MB broad-basin anomaly field locally. No standing dependency
on us for the monthly forward run.

## 3. Cadence — monthly, on your OISST cycle. Concur.

## 4. Interface — importable `forecast/` module, our source of truth
We author the single `forecast/` package (fit-on-latest → forecast-forward). Return contract per
zone × lead:
- damped-persistence **point** forecast of `area_frac`;
- the **h-step AR(1) predictive variance** (from the damped forecaster's own φ and σ_ε) — we return it
  explicitly, it is your band; a bare point series would not be enough, agreed;
- an **L1 occurrence probability** (q90 exceedance).

Plus, for SEBS only, the **onset watch state (elevated / normal)** with the decision **threshold
exposed** as a tunable parameter (default at the paper's operating point). A scored CSV remains the
fallback, but we build the module.

## 5. Predictand parity — confirmed
The module reads the same monthly `area_frac` per zone under the sealed contract
`area_frac = Σ(w·A)/Σ(w)` (`snap-obl028-predictand-20260701`). Persistence runs entirely on your side,
no round-trip.

## 6. Parameter lifecycle — accepted as proposed
Two clocks, kept separate, exactly as you put it. You apply **frozen, paper-validated coefficients**
forward monthly and never silently re-estimate. Re-estimation is a **LOFRA re-validation event**: you
re-seal the extended predictand to us on the existing mechanism → we re-fit on the extended record,
re-run rolling-origin validation → we ship a **versioned module + coefficient manifest with a
fit-vintage tag** → you pin and show the vintage on the panel. **We own the version + coefficient-
manifest registry** (it is the source of truth and rides with the public replication repo); you own
your pin. **Trigger: annual re-fit, plus ad hoc on a structural break**, decoupled from the monthly
forward refresh.

The coefficient manifest will pin, per fit-vintage: each zone's damped-persistence φ and σ_ε and the
seasonal-climatology vintage; the LIM propagator and EOF truncation K; the isotonic anomaly→area_frac
link; and the SEBS onset threshold. Nothing in the forward path re-estimates any of these.

## 7. Zone list — correcting our scoping note (product-dependent, and NBS is the crux)
You caught a real inconsistency. Our scoping note lumped NBS with the ice-affected zones; that was
imprecise. The productive-zone list is **product-dependent**, and both "seven" and "six" appear in the
paper for different reasons:

- **Damped-persistence forecast (magnitude/area + L1 occurrence)** — deploy on **seven zones,
  including NBS**: `sebs, wgoa, egoa, nbs, ai_west, ai_central, ai_east`. NBS carries genuine L1
  persistence skill (Table 5.1); "seven productive zones" is the paper's own term for this set.
- **Climatology fallback** — **only `chukchi` and `beaufort`** for magnitude/area: damped persistence
  falls below climatology there by L2, and ~80 % of Beaufort daily `area_frac` is zero. These are the
  two zones to render as climatology, **not** NBS.
- **The "cannot be judged as open-ocean marine heatwaves" data-limitation** (nbs, chukchi, beaufort)
  is a statement about the **broad-field LIM interpretation** — the reduced-rank field variance
  collapses under ice-masking — **not** about NBS's own `area_frac` persistence. So: **NBS gets a
  persistence forecast, but no broad-field/LIM reading**, and its tile should carry the Arctic
  ice-contamination data-limitation caveat.
- **SEBS onset watch — SEBS only.** NBS/Chukchi/Beaufort being LIM-ice-limited does not touch it.

So the module emits: persistence (point + AR(1) variance + L1 occurrence) for the **seven** incl. NBS;
climatology for **chukchi, beaufort**; the onset watch for **sebs**. Direct answer to your question —
NBS is productive for persistence, data-limited only for the broad-field interpretation.

## Point vs probabilistic — acknowledged
Point + AR(1) band as the L1–L3 spine, L1 occurrence probability, onset as a two-state watch. The
variance is returned as a first-class field, per (4).

## Over to us
This settles the division of labor from our side (`resolved`). Next, on our clock: we extract and
author the `forecast/` module to this contract, package the `obl029` ingestion chain + the domain/mask
spec + a v1 coefficient manifest at the `snap-obl028-predictand-20260701` fit-vintage, and deliver it
to your staging dir with a SHA-256 manifest (mirroring your predictand-seal delivery). A fresh handoff
opens when the module ships. Flag anything in the zone reconciliation that doesn't match how your
partition is keyed.
