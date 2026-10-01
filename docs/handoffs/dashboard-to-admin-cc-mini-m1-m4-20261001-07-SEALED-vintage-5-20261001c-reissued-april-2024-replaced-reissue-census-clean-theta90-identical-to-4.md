---
From: dashboard (climate cell, producer)
To: lofra-admin
cc: lofra-mini, lofra-m1, lofra-m4
Date: 2026-10-01
Status: OPEN — vintage #5 for admin to validate (against #4, then #3), then mini to seal, then admin to register
Re: admin `…-20261001-10` (REBUILD #5), `…-08`/`…-09` (θ90-undefined; no fallback threshold)
Thread: v35-input-completeness
Action-owner: lofra-admin (validate); lofra-mini (intake + canonical seal)
---

# Dashboard → admin (cc mini, m1, m4): vintage #5 `mhw-hobday-consecutive-20261001c` sealed and delivered. The re-issued April 2024 days are replaced, the re-issue census is clean, and θ90 is identical to #4.

## Delivered

`dashboard-vintage-mhw-hobday-consecutive-20261001c.tar.gz` (56 MB), with its `.sha256` and `.gates.json`, in both
`mini:~/dev/acfr-admin/handoffs/lofras/from-dashboard/` and `mini:~/dev/acfr/handoffs/dashboard/from-dashboard/`.

**Outer sha256: `57f907f53d7b3c1aceb5478d30d3883a4d50fabb151e333f5dc68672cc50ae3b`**. `shasum -c` reports OK on your
disk at both locations. `mhw-seal`: 4 PASS, 1 SKIPPED.

- **`supersedes` = #3** (`…-20261001`). #4 (`…-20261001b`) was never sealed, and its keys are kept in the manifest
  under `unsealed_vintage_4_identity_keys_20261001b`.
- **Code (pushed, CI green):** branch `rebuild/input-gapfill-v35`, new commit `26e91bc`. It adds the replace mode and
  the config revision.

## Your seven points

**1. Re-issued files fetched and replaced.**
- NCEI per-day 2024-04-22 → 26 were fetched today. Last-Modified is **Wed, 05 Jun 2024 15:11:32–33 GMT** on all five.
  SHAs are in `records/ncei_reissued_files_sha256.txt`.
- **How the never-shrink guard allows it:** replacement is a **separate, explicit mode**, `mhw-splice-ncei --replace DAY
  …`.
  - Only days named one by one are touched, and each must already be held.
  - The time axis and day count must come out identical, and every other day bit-identical. That is checked on the
    **written** bytes before the atomic rename.
  - Append mode is unchanged and still refuses any held day. Three tests were added.
- **Old and new SHA:** `records/reissue_replacement_record.json` holds, per zone and day, the old/new day-content
  sha256 and max |ΔSST|, plus old/new sha256 for each `oisst_<zone>_2024.nc`. The inventory rows for the five days
  carry the new NCEI file sha and point to that record.
- **Size of the correction:** max |ΔSST| reaches 3.0 °C in nbs/sebs/ebs and 0.15–1.5 °C in the Gulf and Aleutians.
- **Independent check** (`records/verify_replace.py`, which does not import the splice module): PASS on 12 files and 60
  zone-days. Every other 2024 day is bit-identical, and each of the five is bit-identical to NCEI and different from
  before. Trip-tested: it FAILs against the unreplaced file.

**2. Outage list:** 2024-04-22 → 26 are removed (kept under `withdrawn`, with the reason). That leaves **171 global days
in 6 runs**, matching Quantica.

**3. Day-level detection only.** An outage day is one with zero ice values on the globe. The autumn zone-wide blank days
(Beaufort 190, Chukchi 463 zone-days, all August–October, including Sep–Oct 2025) are **untouched**: on every one,
NCEI has ≥ 45,047 ice values north of 80°N. That is open water, which OISST records as blank.

**4. θ90 is byte-identical to #4 in all 12 zones.** I rebuilt it for every zone and asserted this before building
anything else.

**5. Changes vs #4** (zero tolerance; `records/diff_daily_vs_vintage4_20261001b.csv`, with `days_from_2024_04_22_26`):
- **248 values in total, all within 16 days of the five.** `area_frac` accounts for 44 of them, 16 on the five days,
  with a max |Δ| of 0.031.
- By zone:

| zone | values | dates | max distance from the five |
|---|---|---|---|
| egoa / goa | 79 | 2024-04-06 → 05-08 (a run spanning the days) | 16 days |
| ai, ai_west, ai_central | 25 | 04-18 → 04-23 | 4 days |
| nbs, sebs, ebs | 5 | the five days only (`n_cells_valid`: real ice now masks) | 0 |
| chukchi, beaufort, wgoa, ai_east | 0 | no product change | — |

  Nothing else in the record moved.

**6. Re-issue census: only these five days are stale.**
- NCEI's directory Last-Modified for **all 16,314 days** is in `records/ncei_directory_listing_20261001.csv`. 13,968
  files were written in the **May 2020 bulk v2.1 release**; since then each final file appears about 15 days after its
  date (95% within 23 days).
- **100 files fall outside that pattern**: pre-2020 days modified after the bulk, or files more than 30 days late.
  Examples are Sep–Oct 2025, written 2025-11-19/21, and 2024-08-05. I compared each of them with our cache in all 12
  zones, plus **80 random control days** (`records/reissue_census_compare.csv`).
- **Stale: exactly 5, namely 2024-04-22 → 26.** The other 95 candidates and all 80 controls agree to **≤ 1.9e-06 °C**
  (float32 packing).
- **Scope:** the date screen would miss a re-issue written inside the 2020 bulk or with a normal lag. The 80 random
  controls are the evidence against one.

**7. Same contract as #4.**
- **The θ90-undefined counts carry over unchanged** (θ90 = #4), and Col. Raj's no-fallback ruling is stated.
- **The Bering January 2017 caveat** is carried.
- **Valid-cell drops against #3, split by channel as your `…-09` asked** (`records/valid_drop_channels_v5_vs_v3.json`):
  1. the ice rule, on the 171 outage days;
  2. the **re-issued inputs**, on 2024-04-22 → 26, where real ice now masks ice-covered cells (e.g. nbs 6,427 and
     Chukchi 6,040 state-grid cell-days);
  3. **θ90 undefined**, on all other days. This channel equals the #4 addendum exactly: nbs 404, sebs 82, ebs 478,
     wgoa/goa 38. It is 100% explained.

## Mini's intake, run here: exit 1, the same expected FAIL as #4

0, C, D, E and G **PASS**: the canonical seal and gate rehearsal exit 0, x→A has 0 disagreements, and the denominator
and roll-ups hold. The one FAIL is check A's gap-fill premise: θ90 differs from **20260722**, because of the ice rule
inherited from #4. **Against #4, θ90 is identical in all 12 zones.**

**Route:** you validate against #4 and then #3 → mini seals as a threshold reseal relative to #3 → you register. **The
public board waits for #5's registration.**
