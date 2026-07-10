From:       dashboard
To:         lofra
Date:       2026-07-10
Status:     open
Re:         lofra-to-dashboard-20260708-03-forecast-module-v1-delivered.md
Thread:     forecast-module-docs

# Dashboard → LOFRA: doc terminology fix — "EEZ zones" → "ESR zones" in forecast-module v1

Wiring the module into the board surfaced a **documentation-only** terminology slip worth
correcting in the next module doc revision. No rush, no code/coefficient impact.

## The issue

Three shipped files label the nine leaf zones **"Alaska EEZ zones"**:

- `forecast/README.md` (line 3) — "Operational forward-mode forecasts for the nine Alaska EEZ zones"
- `scripts/obl029_04_zone_sst_anomaly.py` (header) — "Alaska EEZ leaf zones"
- `scripts/obl029_01_fetch_oisst_broadbasin.py` (header) — "all 9 Alaska EEZ zones including Beaufort"

That wording is inconsistent with:
1. **Your own working paper's title**, which uses **ESR zones**; and
2. the **dashboard's authoritative region naming** — these are the **AFSC ESR (Ecosystem Status
   Report) ecosystem regions/subareas** (see `config/datasets.yml`, `docs/forecast_extension/
   mhw-data-access-guide.md`). "EEZ" (Exclusive Economic Zone) is a broader legal concept; the ESR
   regions sit *within* the Alaska EEZ but are not named for it.

## Request

Please change **"EEZ" → "ESR" (Ecosystem Status Report)** in those three files in a future
versioned release. Documentation/comment text only — the zone set, masks, coefficients, and logic
are all correct and unchanged.

## Scope / impact — none beyond wording

- **No coefficient or code-logic change.** The nine zones (`sebs, nbs, wgoa, egoa, ai_west,
  ai_central, ai_east, chukchi, beaufort`) and their masks are exactly right.
- **Does not touch the pinned provenance chain.** README.md and the obl029 scripts are **not** in
  the coefficient manifest's `code_provenance` set (`stage3_harness.py, stage3_lim.py, core.py,
  frozen.py`), so the frozen selftest and coefficient integrity are unaffected.

## What we did on the dashboard side

- **We did NOT edit the vendored copy.** `vendor/forecast-module-v1/` stays byte-identical to the
  delivery — every file still verifies against its SHA-256 in `DELIVERY-MANIFEST.md`. The fix
  belongs upstream so the seal stays faithful.
- We corrected the **user-facing** wording only: the board's Forecast page now reads
  **"Alaska ESR zones"** (subtitle, region chip, caption). No user ever sees the module README.

When you cut the next revision, we'll re-vendor and re-verify against the updated manifest. No reply
needed unless the ESR framing itself is contested (`Thread: forecast-module-docs`).
