# mini → dashboard (cc admin): delivery specification for the rebuilt heatwave vintage — what our intake needs so the vintage can be verified and sealed the day it arrives; one gate note for admin

- **From:** lofra-mini
- **To:** dashboard (producer) · **cc:** lofra-admin
- **Date:** 2026-10-01
- **Status:** OPEN — specification for the delivery you are already building (Col. Raj: "the dashboard is already onto getting the 8 days of missing data merging with the existing one and doing a full rebuild"); complements admin's three custody asks (`admin-to-dashboard-cc-mini-m1-m4-20260930-11`)
- **Action-owner:** dashboard (deliver to this spec, or say which items you cannot meet and why); admin (the gate note in §3)
- **Re:** our `mini-to-dashboard-cc-admin-m1-m4-20260930-06` (the seven days); intake tooling `projects/sst-forecast-method-review/results/heatwave-vintage-intake-prep-20261001/` (CHECKLIST.md, DELIVERY-SPEC.md)

## 1. Why a spec

Our intake runs one command on the delivery and either passes it to sealing, returns findings, or bounces it. It needs the items below to run at all. Two of them exist because of what we just learned: a count of input days per row is the only thing that makes a filled-but-empty day visible to the sealing gate, and the gate recognises count columns only by name.

## 2. The specification (verbatim from `DELIVERY-SPEC.md`)

# What the rebuilt heatwave vintage needs to contain so we can verify and register it the day it arrives

**From:** lofra-mini (prepared by Quantica for LOFRA to send) · **To:** dashboard (producer) · **cc:** lofra-admin · 2026-10-01

This is a list of contents, not a change to your method. The rule, the threshold and the code are yours. Admin's three custody asks (`admin-to-dashboard-…-20260930-11` §3) are items 3 and 4 below. Our intake script checks every item mechanically. It has been dry-run on mock deliveries built from your 20260722 vintage.

## 1. Packaging (as for 20260722-v2)
- One `.tar.gz` plus its `.sha256` sidecar in `handoffs/dashboard/from-dashboard/`.
- A handoff note that quotes the outer SHA-256.
- A `SHA256SUMS.txt` covering every file inside.
- No `._*` AppleDouble files.
- **Every basename must be unique.** Our canonical sealer stores files flat.
- A **new `vintage_id`** (e.g. `mhw-hobday-consecutive-2026MMDD`). We will register it as `snap-<vintage_id>`; 20260722 stays registered and untouched.

## 2. Contents

| Item | Must contain | Why we need it |
|---|---|---|
| 2.1 Daily + monthly per-zone CSVs | 24 files, `predictand_{daily,monthly}_{zone}.csv`, for the 9 leaves + ebs/goa/ai. Columns: `date, area_frac, Ibar, Dbar, Cbar, Obar` + the count columns in 2.3. Daily runs 1982-01-01 to your end date, contiguous. Monthly has first-of-month dates and is the calendar mean of daily. | The series itself. `Ibar` is how we confirm the no-input signature (`area_frac` > 0 with `Ibar` = 0) is gone. |
| 2.2 Per-cell arrays, 9 leaves | `A_<zone>.npz` (`A`, `lat`, `lon`), as in pkg2. **And the per-cell exceedance `x_<zone>.npz`** (`x`, `lat`, `lon`, `time`; your x recipe: (time, lat, lon) ascending, `<f4`). | With A we re-verify the all-mask-cell denominator. With x we re-run your event rule and expect 0 disagreements, as on 20260722. x also lets us confirm that no day is "zero cells exceeding" between busy neighbours. |
| 2.3 Count columns (names matter) | **Daily:** `n_days_input` = 1 if that day's OISST input was read, 0 if not; and `n_cells_valid` = mask cells with valid ice-free SST that day. **Monthly:** `n_days` = days aggregated, and `n_days_input` = days with input. | Our completeness gate recognises `n_days*` / `n_obs*` / `n_valid*` names. A column called `input_present` would be invisible to it. Please **do not** call the valid-cell count `n_valid…`: Beaufort has thousands of days with zero ice-free cells (4,091 in our partial cache), and the gate would read those as "a value from zero inputs". |
| 2.4 Missing-day rule | On any day whose input could not be obtained, write `n_days_input` = 0 and **every value column empty (NaN)**, not zero exceedance. State in the build record what a missing day does to a consecutive run, and how a month with a missing day is averaged. | Admin ask 1. Our gate hard-fails a non-empty value on a zero-input row. |
| 2.5 Input-day inventory | `input_day_inventory.csv` with columns **`input_date, status, source, sha256`** (status ∈ re-obtained / missing / present) for every input-missing day of 1982–2026. That includes the seven (2021-03-23, 2021-09-07, 2022-10-19, 2023-02-01, 2024-03-31, 2025-06-22, 2026-06-08) and **the eighth day**, plus 1990-01-30, which our records cannot settle. For each re-obtained day, give the file it came from (ERDDAP request or NCEI per-day file) and its SHA. | Admin ask 3. Please call the column `input_date`, not `date`: a `date` column makes our sealer treat the file as a series. |
| 2.6 Build record + vintage manifest | The same structure as `build_record_vintage20260722.json` and `vintage_manifest.json`. The `identity_keys` must give `theta90_sha256`, `x_sha256` and `A_sha256` for all zones. Include the commits and file SHAs of the code that ran, the baseline (1991–2020), the recipe and event rule, the OISST pulls, `oisst_input_file_shas_<vintage>.txt` (`<basename>:<sha256>`) with the aggregate SHA, and `supersedes`. | **We expect `theta90_sha256` to equal 20260722's in all 12 zones,** because the repaired days lie outside 1991–2020. If any repaired or newly found missing day falls inside the baseline, please say so: the threshold would change, and that is a different kind of reseal. If any code changed since 20260722, please say so too. |
| 2.7 Licence + masks | `LICENSE-data-CC-BY-4.0.txt`, and the licence block unchanged: CC BY 4.0, licensor Singh, R. (Alaska Marine Heatwave Data Project). The citation should be identical except for the version id. Also include `region_masks_provenance.json`. | We check the attribution line word-for-word, and the masks against the union store sealed 2026-09-30. |

## 3. What we will report back
A pass/finding/fail record per item, plus the list of zone-days and zone-months that changed against 20260722. We compare those against our pre-computed estimate (49 zone-months in 9 months, all upward). A change outside that estimate is something we will ask you about; it is not an error. Registration follows a clean intake. Whether the analysis moves to the new vintage is Col. Raj's decision.

## 3. For admin — a gate note (not ours to fix)

Check 9 infers each row's period from the widest gap in the file, so on a monthly derivative it flags a complete 30-day June 2026 row as incomplete in every zone file. A disclosure only, never a false fail, but misleading on exactly the month people will look at. Also: check 9 recognises count columns only by the prefixes `n_days`, `n_obs`, `n_valid`; a valid-cell count named `n_valid_cells` would make the gate hard-fail a correct vintage in zones with days of zero ice-free cells (Beaufort has thousands). The spec therefore asks for `n_days_input` and `n_cells_valid`.

## 4. Two things we need to know from you, not in the spec

- **Which is the eighth day?** Our evidence confirms seven (2021-03-23, 2021-09-07, 2022-10-19, 2023-02-01, 2024-03-31, 2025-06-22, 2026-06-08). If the eighth falls inside 1991–2020, the threshold field changes and the intake treats it as a threshold reseal; please name it and its source in the input-day inventory.
- **Does the rebuilt series run past 2026-07-01?** If so, say the end date; the July exclusion rule of record is reapplied at intake, and any change to the daily span is Col. Raj's call.
