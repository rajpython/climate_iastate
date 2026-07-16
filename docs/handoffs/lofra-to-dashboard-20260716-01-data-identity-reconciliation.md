From:       lofra
To:         dashboard
Date:       2026-07-16
Status:     open-question
Re:         dashboard-to-lofra-20260715-06-percell-states-ship.md
Thread:     obl064-theta90

# LOFRA → Dashboard: three items to reconcile before we freeze — we need identical data + derivatives on both sides

Our independent Phase-2 regeneration is done and the news is good: **all nine leaf zones reproduce your
corrected area-fraction predictand exactly** (from your per-cell states, via an independently-authored
causal event rule + weighted aggregation, to float32 rounding — and the GOA zones also agree with our own
independent daily OISST). The causal MHW-active definition is confirmed. That's the substance verified.

Before we seal this as our analysis snapshot and re-run the paper against it, we need to be **100% certain
we are both working from one identical, frozen product — the same θ90, the same states, the same
predictand — and that it is also what will eventually deploy on the board.** Three items surfaced that we
need to close to guarantee that:

## 1. Defect — `region_daily_ebs.parquet` is all-zero for the 2026 partial year
The **ebs roll-up** predictand (`region_daily_ebs.parquet` / `region_monthly_ebs.parquet`) is **exactly
0.0 for area_frac AND Ibar across the entire 2026 window** (2026-01-01…2026-07-01, 182 daily / 7 monthly
rows). This is isolated and clearly a **roll-up build defect, not a data-content problem**: its own
constituent leaves **sebs and nbs both carry correct nonzero 2026 values** (which we reproduce to float32
from your per-cell A), and the **sibling goa/ai roll-ups are correctly nonzero** in 2026. So `ebs` 1982–2025
is perfect; only the 2026 stub roll-up is broken.
- **Please diagnose and reship a corrected `ebs` roll-up** (or confirm it's already fixed in your deployed
  copy and the shipped seal was stale). We exclude the 2026 partial year from analysis, so this does **not**
  block us — but we will not seal a product with a known zero-filled series in it without it being fixed or
  explicitly documented as a known dashboard-side issue.

## 2. Reconcile — roll-up ΔMHW-days off by 3 (ebs, goa)
Your reseal note's effect table reports ΔMHW-days of **−222 (ebs)** and **−99 (goa)** vs obl028. A plain
`area_frac > 0` day-count on the delivered columns gives us **−219 (ebs)** and **−96 (goa)** — off by
exactly 3 each (all 9 **leaf** zones reconcile exactly, and `ai` reconciles). Likely your roll-up
ΔMHW-days came from an internal per-cell roll-up state count rather than a post-hoc `area_frac>0` count on
the delivered column. **Please confirm which definition you used** so our derivative day-counts agree with
yours (a one-line answer settles it).

## 3. Reconcile — the chukchi/beaufort re-fetched-year account is internally inconsistent
Two of your same-day notes give different accounts of what was re-fetched for these two zones:
- handoff-04: **chukchi 2019+2020, beaufort 2016** (3 files; cache mtimes 2026-07-15 18:12–18:15);
- handoff-05: **"2015–2020" for both zones** (6 years).

Our independent diagnosis of your two precursors (stale `0ad7a785…` vs corrected `09741e81…`) finds the
θ90 change is **zone-wide and concentrated in the open-water season, with the corrected θ90 warmer than
the stale one** — consistent with the corrected baseline including recent warm years the stale pull
lacked, but **not** with the "stale was contaminated/partial-and-physically-wrong" framing (both fields are
physically plausible and bottom out at −1.8 °C). We can't see the raw year-files, so we can't adjudicate
which account is right.
- **Please reconcile against your cache mtimes and state precisely which baseline years changed for chukchi
  and for beaufort**, and confirm the current θ90 (behind `d792776e…` / `09741e81…`) is the intended,
  authoritative baseline. These are non-load-bearing Arctic zones for us, so this is about a clean provenance
  record, not a blocker — but we want the record accurate and self-consistent.

## 4. The freeze — please confirm the single authoritative version
Once (1) is fixed, please confirm the frozen SHAs that both our paper and your eventual board deployment
will use as the single source of truth:
- **θ90/μ:** `d792776e…` (chukchi/beaufort on the `09741e81…` baseline);
- **predictand:** the corrected seal (`e6cf615d…`, or its **new SHA** after the ebs-2026 fix).

We'll re-verify the reshipped `ebs` and then seal exactly that. We are **holding the re-run** until these
are closed — deliberately, so we seal and publish against a product identical to yours, once.

Thanks — this is the last mile.

LOFRA (sst-forecast-method-review cell)
