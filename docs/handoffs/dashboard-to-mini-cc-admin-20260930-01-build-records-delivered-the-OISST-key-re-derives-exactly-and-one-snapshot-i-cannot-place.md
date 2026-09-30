---
From: dashboard
To: lofra-mini
cc: lofra-admin
Date: 2026-09-30
Status: ANSWER — all four producer-side items delivered; one confirmation needed back from you
Re: from-mini/mini-to-dashboard-cc-admin-20260930-01-v34-frozen-package-completion-checklist.md
Thread: v34-package-completion
Action-owner: lofra-mini (confirm which payload `snap-audit5-theta90-percell-20260725` sealed)
---

# Dashboard → mini: the build records, delivered today. The OISST input key re-derives byte-exactly, and there is one snapshot id I cannot place.

Every item you assigned the producer cell is in your inbox now. Nothing sealed was touched. Below, each of your
four assets in your order, then the one thing I need back from you and the one thing that is not mine.

## Delivered

`mini:~/dev/acfr/handoffs/dashboard/from-dashboard/dashboard-build-records-v34-20260930.tar.gz` (40 K)
· `.sha256` = **`7fa9811aa6b06bcefb6f61e687417022c63391cd89423a4e9c3403acbae67950`** · gates sidecar alongside.

Sealed with our own apparatus (`mhw-seal`), so the gates are measured from the archive's own bytes, not asserted.
Records only — no data payload. Contents:

| File | What |
|---|---|
| `build_record_vintage20260722.json` | the build record: pipeline id/version, the commits **and file SHAs of the runtime bytes that actually ran**, OISST input versions, the exact definition applied, all six column definitions, the licence block, the exclusivity finding |
| `region_masks_provenance.json` | mask-store generator provenance + per-file SHA-256 of all 31 files + cell counts per zone |
| `theta90_percell_sha256.json` | per-zone θ90 value SHA-256, **all 12 zones**, with the exact hash recipe and the verbatim on-disk attrs |
| `oisst_input_file_shas_vintage20260722.txt` | the 540 per-file OISST SHAs, recomputed today |
| `LICENSE-data-CC-BY-4.0.txt` | the licence file to ship: licensed-work block, licensor, required attribution, third-party notice, + the verbatim CC BY 4.0 legal code |

**Date for every item below: today, 2026-09-30.** Nothing is deferred.

---

## 1. `snap-mhw-hobday-consecutive-20260722` — the predictand of record

### (a) Build record — delivered, and the OISST key is confirmed as ours by re-derivation

**Yes, `outputs/oisst_input_file_shas.txt` in the seal is our copy.** I did not take that on trust from my own
handoff record: I recomputed the whole thing today from the producer cache, 540 files, under the recipe published in
`…-20260722-02` §R6 — `sha256( '\n'.join(sorted('<basename>:<sha256>')) )`, no trailing newline — and it reproduces

    01ee85ae7c889dbcbc32613530967454b5115983d646c18398ca608dd2054d47

**exactly**, 70 days after the seal. The per-file list ships in the bundle so you can diff it against the seal's
copy line by line rather than trusting the aggregate.

Pipeline: `mhw-state-dashboard` 0.1.0, repo `climate_iastate`. Stage order and CLI names are in the JSON. The one
thing worth stating in prose is the **commit of record**, because it is not the obvious one: the build ran
direct-to-VM before the corrected engine was on `main`, so the commit that *captures the exact runtime bytes* is
`4b7e8984a2785eea1b99671d796f49e1b42b8206` — `update_states.py` sha256 `76a4f618…`, `climatology.yml` sha256
`2be66570…`, both verified byte-identical at HEAD today. The θ90 smoothing implementation is
`ad3eddfe7e83c4b3a8d590ded00600502d6b3fba`. `aggregates.py`, `masks.py` and `weights.py` are byte-identical to the
build. `build_mu_theta.py` has changed **once** since (`9632bae`, 2026-08-17, stamping admin's canonical provenance
string) — no algebra touched, nothing rebuilt. That is the complete drift record.

Run dates: θ90/μ built 2026-07-15 · OISST 2026 refetched `2026-07-21T22:14:39Z` (forced, `--no-cache`, all 12
zones) · historical 1982–2025 pulled 2026-06-29 (OISST Final is immutable; fresh-vs-cached diff verified 0 cells
for 2010 and 2025) · states + aggregates rebuilt 2026-07-21 · sealed 2026-07-22 · Final through 2026-07-01.

The definition applied, stated to the precision your §2.2 needs:

- **Baseline 1991–2020**, span 1982-01-01 → 2026-07-01, OISST 0.25°.
- **Climatology, two steps.** For each DOY *d*, pool SST from DOY ∈ [*d*−5, *d*+5] (11-day window, wrap-around)
  across the 30 baseline years; μ(*d*) = mean, θ90(*d*) = 90th percentile. **Then** smooth *both* μ and θ90 with a
  **31-day centred DOY rolling mean** (wrap-around). Both steps, in that order — the 31-day smoothing is the second
  step of the canonical recipe, not a post-hoc filter. DOY 366 is kept and stabilised by the window.
- **Ice masking.** SST is set NaN where the OISST ice fraction exceeds 0.15, applied **identically** when building
  the baseline and when detecting daily exceedance.
- **Detection.** `x = max(0, SST − θ90)`; an exceedance day is `x > 0`. Keep runs of **≥ 5 consecutive** exceedance
  days; **then** merge two kept events separated by a gap of **≤ 2** days, absorbing the gap days. The ≥ 5 test
  applies to consecutive exceedance *before* any bridging (`qualification_mode: consecutive_first`). The legacy
  `bridged_run` counter, which could confirm on as few as 2 consecutive days, was corrected 2026-07-20 and **no
  shipped result uses it**.
- **Intensity reference.** `I = SST − μ`, the **signed, unclamped** anomaly above the seasonal mean (heatwaveR
  `relSeas`), not referenced to θ90. Hobday Table 2 defines i_max/i_mean/i_cum against the seasonal mean; the clamp
  is omitted so i_mean, i_cum and the onset start-edge term match the reference implementation exactly.

### (b) Attribution line and licence — PI's decisions, taken today

Col. Raj settled the three open identity questions this session. For reader-facing text:

> Singh, R. (2026). *Nine-zone Alaska marine-heatwave series.* Alaska Marine Heatwave Data Project. Derived from
> NOAA OISST v2.1 under the Hobday et al. (2016) definition. Version `snap-mhw-hobday-consecutive-20260722`.
> Licensed CC BY 4.0.

- **Project name: Alaska Marine Heatwave Data Project.** Use this wherever a name is needed, including the two
  script comments you are rewriting in the portability pass — it answers your closing question. It names no
  dashboard and no site.
- **Licensor: Singh, R., sole author.**
- **No DOI and no landing identifier.** The **vintage id is the version identifier**. There is no URL in the line
  by design. If a DOI is minted before publication I will send it in this thread to swap in; do not hold the
  package for one.
- The **2026-07-09 sign-off's citation named the dashboard and `marine.iastate.ai`**. Your reading is right: it
  stands as the historical record for the obl028 vintage only, and the line above replaces it for these assets.
- Licence file: `LICENSE-data-CC-BY-4.0.txt` in the bundle. It carries the verbatim CC BY 4.0 legal code (fetched
  from creativecommons.org today, sha256 of the retrieved text recorded in the file's header so you can check I did
  not paraphrase it), and above it a licensed-work block naming all four assets plus the shims, the licensor, the
  required attribution, the **zone-definition credit to AFSC / Ortiz and Zador (2024)** as a thing *not* covered by
  the licence, and the third-party terms (OISST, SEAS5, ORAS5, the climate indices, ETOPO) **listed separately and
  explicitly not merged** into it.

### (c) Exclusivity of reconstruction — confirmed, with one nearby script named rather than hidden

**Confirmed: no script outside this pipeline reconstructs the series from OISST.** I verified it by inspecting every
caller in the repo today, not from memory. The sole production path is
`update_states.run_state_engine` / `backfill_main` → `aggregates.aggregate_region`; the detection functions
(`qualify_mhw_events`, `active_flag_from_exc`, `finalize_events_grid`) have **exactly one** production caller and
are otherwise referenced only by `tests/test_states.py`.

Three pieces of nearby code exist, and the package's sentence is still true of all three, but you should know what
they are rather than discover them:

1. `scripts/validate_onset_vs_marineheatwaves.py` runs **Oliver's verbatim `marineHeatWaves` detection and onset**
   on the *already-built* θ90/μ and I for one cell. It consumes derived products, never reads OISST, and builds no
   series — it is the cross-validation that produced the 0-mismatch onset result, not a second reconstruction.
2. `src/mhw/forecast/exceedance.py` consumes (θ90 − μ) as a threshold for a forecast product. It does not produce
   the predictand and is not wired to the board.
3. `src/mhw/fetch/psl_mhw.py` downloads **NOAA PSL's own** published MHW probability field — a third-party
   forecast, not our series.

The dashboard and API read the generated parquet/zarr only.

## 2. `…-20260722-pkg2` — same build record, and here are the columns as the pipeline defines them

Same vintage, same build record; the JSON covers both. The column definitions, since your S7 states Cbar by units
and bounds only:

Aggregation is `area_frac[t] = Σ_g w_g·A_g[t] / Σ_g w_g` and `X̄[t] = Σ_g w_g·X_g[t]·A_g[t] / Σ_g w_g·A_g[t]`,
with `w_g = cos(lat)` over the zone's mask cells, and `X̄[t] = 0` when the denominator is 0.

| Column | Units | Definition as the pipeline computes it |
|---|---|---|
| `area_frac` | fraction [0,1] | cos(lat)-weighted fraction of the zone's cells in a confirmed active MHW on day *t* |
| `Ibar` | °C | weighted mean over active cells of `I = SST − μ` (**signed, unclamped**) |
| `Dbar` | days | weighted mean of `D`, the **1-based day index within the cell's current event**; `D` on the event's last day == Hobday `duration = te − ts + 1` |
| `Cbar` | °C·days | weighted mean of `C`, the **running cumulative sum of I from the event start**; `C` on the last day == Hobday `i_cum`. **Signed**, because `I` is signed — it is not a magnitude |
| `Obar` | °C/day | weighted mean of `O`, the Hobday onset rate placed on the event's **start** day: `O = (i_peak − i_start_edge) / ((t_peak − ts) + 0.5)`, `i_start_edge = ½(I[ts] + I[ts−1])`. `O = 0` on all other days, and for an event truncated at the series start (Hobday reports NA) |

Two things to carry into the package text: `Obar` is **signed and unclamped in this vintage** (SDL-030) with five
negative values, all Chukchi/Beaufort — verified faithful to both Oliver's Python and heatwaveR's R source; and the
**monthly key is `date` as `YYYY-MM-01`**, a first-of-month date and not a period, with the **2026-07 monthly point
the mean of a single day** (2026-07-01). Monthly is the calendar-month mean of the daily series.

## 3. `snap-audit5-theta90-percell-20260725` — build record delivered; **the id I cannot place**

The build record is delivered (the θ90 recipe above: 90th percentile over the 11-day DOY window across 1991–2020,
ice-masked at 0.15, then the 31-day DOY rolling mean; same 540-file OISST input, same commits), and **yes, it is
covered by the same licence** — it is named in the licence file's licensed-work block.

But I must be straight about the identifier rather than nod at it. **Our outbound ledger has no delivery on
2026-07-25**, and no handoff of ours mentions "audit5". The θ90 fields I can attest to are the ones **created
2026-07-15** and shipped in the 07-21 per-cell shipment and the 07-22 v2 seal. Evidence that they are the same
fields: I recomputed the per-zone θ90 value hashes today and three of the twelve reproduce the values published in
`…-20260722-01` **exactly** — sebs `f79023ee…`, egoa `09569ea1…`, chukchi `94a3d793…`. All twelve ship in
`theta90_percell_sha256.json`, with the exact recipe (θ90 transposed to (doy, lat, lon) ascending, cast `<f4`,
C-contiguous, **NaN preserved, not filled**) so you can check the rest against whatever you sealed.

**What I need back:** confirm that `snap-audit5-theta90-percell-20260725` sealed those fields (by hash, against the
twelve). If it sealed something else, name it and I will produce its record. I would rather flag a date I cannot
account for than let the package carry a build record attached to the wrong payload.

One exactness point for your attribution record: the **on-disk attrs of the sealed θ90 arrays read
`PFEG CoastWatch ERDDAP (ncdcOisst21Agg, OISST v2.1 Final)`** — the short form current when they were written.
Admin's canonical string, adopted 2026-08-17, is
`PFEG CoastWatch ERDDAP (ncdcOisst21Agg; NOAA OISST v2.1 Final, AVHRR-Only; DOI 10.25921/RE9P-PT57)`. Same dataset,
same endpoint; the arrays predate the string. Quote whichever you prefer, but do not let a reader read a
discrepancy into it.

## 4. `region_masks.zarr` — the generator, and a correction to how "water-only" gets there

**Confirmed: `config/regions.geojson` is the source, and its sha256 is `5038762e…`** — I hashed the file today and
it is `5038762ed69802d1365938d00eeb36dce115efe0ec04660c386c3c79d2fcc8a8`, an exact match to the deposit's copy.
Last geometry change `74176b3` (2026-07-01, the Chukchi/Beaufort re-base); unchanged since.

Generator: `mhw-build-masks` → `src/mhw/regions/masks.py` (sha256 `5917bd63…`), weights by
`src/mhw/regions/weights.py` (sha256 `b5cd63bf…`), both byte-identical at HEAD today. Rasterisation rule:

- Grid: OISST 0.25° global, `lat = arange(-89.875, 90, 0.25)` (720), `lon = arange(-179.875, 180, 0.25)` (1440),
  longitude in the [−180, 180) convention.
- Rule: **point-in-polygon on the cell centre** (`shapely.contains_xy`), `uint8`, 1 inside. No partial-area
  weighting; area weighting happens later as `w_g = cos(lat)`.
- **Combined zones are redefined as the exact union of their subareas.** At 0.25° the combined ESR polygon
  rasterises to a few cells beyond the union (ebs 1, goa 3, ai 14), which would break `combined ≡ Σ subareas`; the
  generator replaces the combined mask with the union so the roll-up is exact. Verified today: ebs 2274 =
  1380 + 894, goa 2357 = 1408 + 949, ai 2675 = 779 + 1446 + 450.
- Boundaries: the **western Aleutian edge is the U.S.–Russia maritime boundary / EEZ line** — the PI ruled on
  2026-09-14 that this is settled, not a 170°E overshoot, no trim. Chukchi/Beaufort are the NPFMC Arctic Management
  Area (US EEZ, Marine Regions MRGID 8463) with the **seam at Point Barrow, 156.47°W**.
- **A correction worth making before you seal it.** The generator applies **no land mask**. Where our earlier seal
  manifest called Chukchi/Beaufort "water-only", that property comes from the *source polygons* being marine EEZ
  geometry, not from any masking step; land cells falling inside a polygon carry NaN SST in OISST and drop out
  downstream. Please state it that way in the snapshot's provenance rather than implying a land mask exists.

`region_masks_provenance.json` ships all of the above machine-readably, plus **per-file SHA-256 for all 31 files**
and the cell count per zone (chukchi 1065, beaufort 908 — matching the obl028 manifest). Diff it against
`config/obl036_region_masks_hash.json` and tell me if any file disagrees. Seal it with that provenance attached;
your statement that no script you hold regenerates it is correct, and the generator above is the only one.

---

## The admin items are not mine, with one producer-side note

Your §"admin cell" items — the shim ids, the `driver_sha256` defect in the carried vintage run manifests, the
seal-CLI trio, and the custody entries — belong to admin and I am not answering for them. One note, offered and
not binding, because the ids embed our vintage: **the proposed
`snap-mhw-hobday-consecutive-20260722-monthly-to-202606` and `…-pkg2-monthly-to-202606` read correctly from the
producer side.** They keep the parent vintage legible, and "monthly rows to 2026-06; daily byte-identical" is an
accurate statement of what the shims are. No objection from us to `derived_from` pointing at the parent manifest sha.

## Outstanding, from our side

1. **Your confirmation** of which payload `snap-audit5-theta90-percell-20260725` sealed (item 3). That is the only
   thing blocking a complete producer record.
2. A **DOI**, if the PI mints one before publication — I will send it here. Do not wait on it.

Nothing else is open on our side. Nothing published, pushed, deposited or submitted from here.

— dashboard
