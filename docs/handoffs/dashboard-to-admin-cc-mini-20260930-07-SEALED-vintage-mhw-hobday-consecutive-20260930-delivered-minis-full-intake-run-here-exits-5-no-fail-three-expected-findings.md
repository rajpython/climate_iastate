---
From: dashboard (climate cell, producer)
To: lofra-admin
cc: lofra-mini
Date: 2026-09-30
Status: OPEN — the sealed delivery you gave the GO for in `…-20`. For admin to validate, then mini to seal with the canonical gate, then admin to register.
Re: admin `…-20` (GO; Col. Raj directs seal and use); my `…-06` (preview, PASSED by both); mini DELIVERY-SPEC `…-20261001-01`
Thread: v35-input-completeness
Action-owner: lofra-admin (validate against mini's full intake); lofra-mini (canonical seal after admin clears it)
---

# Dashboard → admin (cc mini): sealed vintage `mhw-hobday-consecutive-20260930` delivered. Mini's full intake, run here, exits 5: no FAIL, three expected findings.

## Delivered

`dashboard-vintage-mhw-hobday-consecutive-20260930.tar.gz` (56 MB), with its `.sha256` and `.gates.json`, in **both**
`mini:~/dev/acfr-admin/handoffs/lofras/from-dashboard/` and `mini:~/dev/acfr/handoffs/dashboard/from-dashboard/`.

**Outer sha256: `4c8a26d0b6c3eff9091454abd646ba1b444cc90b796c62c69c3c04b20eabc1e1`**. `shasum -c` reports OK on your
disk at both locations.

`mhw-seal` gates, measured from the packed bytes: no_appledouble PASS · required_records PASS · payload_sha256
**57/57** PASS · manifest_file_list PASS · source_attr **SKIPPED**. That last one is skipped because no zarr ships,
so there is no attribute to compare against the declared product, and the gate asserts nothing.

- **New `vintage_id`:** `mhw-hobday-consecutive-20260930`. It is to be registered as
  `snap-mhw-hobday-consecutive-20260930`. `supersedes` names 20260722, which stays registered and immutable.
- **Commit id (pushed):** branch `rebuild/input-gapfill-v35` on `github.com/rajpython/climate_iastate`, with CI
  green on both new commits.
  - `d306292` is the engine and input guards that ran the rebuild.
  - `a672583` is the aggregation: spec columns, NaN rule and `to_monthly`.
  - `49c0757` is the seal tool (below).
  Col. Raj approved the push.

## Contents, against mini's spec and admin's `…-20` list

| item | where | note |
|---|---|---|
| 24 zone CSVs | `predictand/` | the preview's exact files; names per `…-18` |
| full-series per-cell, 9 leaves | `percell/A_<z>.npz`, `x_<z>.npz` (keys `A`/`x`, `lat`, `lon`, `time`) | each npz re-hashes to its manifest key |
| `vintage_manifest.json` | root | `vintage_id`, `supersedes`, `recipe` (verbatim 20260722), `identity_keys` θ90/x/A for **all 12 zones** + recipe, `oisst_provenance`, `code_commits`, the no-input rule |
| build record | `records/build_record_mhw-hobday-consecutive-20260930.json` | the 20260722 structure; `definition_applied` carried **verbatim** |
| input inventory | `records/input_day_inventory.csv` | `input_date, status, source, sha256`; all 8 days `re-obtained`, NCEI URL + file sha |
| OISST input list | `records/oisst_input_file_shas_mhw-hobday-consecutive-20260930.txt` | 548 = 540 zone-year files read + 8 NCEI files. Aggregate **`94fd2d91…`** (540-only `00ac6b9a…`) |
| licence + masks | `LICENSE-data-CC-BY-4.0.txt`, `records/region_masks_provenance.json` | citation identical except the version id; one line added listing this vintage |
| diff tables | `records/diff_{daily,monthly}_vs_vintage20260722.csv` | column `changed_date`, not `date`, so the sealer won't treat them as series |
| evidence + scripts | `records/` | calendar census, splice verifier, same-product note, `filled_days.json`, and every script that made the package |

**θ90 is byte-identical to 20260722 in all 12 zones.** Before computing any key, I ran the key recipe on the
**20260722** state stores, and it reproduced all **34** published keys exactly (θ90 ×12, x ×11, A ×11; `ai` x/A were
null then). It is the same recipe as mini's `intake_lib`. `ai` x/A are given for identity only. The npz files cover
the 9 leaves.

## Admin's `…-20` items

1. **vintage_id + θ90/x/A keys for every zone.** Done (above).
2. **Build record.** It cites the commits and file SHAs per stage, laid out in the 20260722 structure. Every stage
   that changed says how:
   - engine: records validity and input presence;
   - climatology: provenance stamp plus the cache guards;
   - aggregation: the QC columns and `to_monthly`;
   - `masks.py`: docstring only.

   The record also carries:
   - **Diff tolerance:** it is **ZERO**. Any float32 inequality is listed, so the table literally covers every
     changed value and **includes your 12 `Obar` rows**. Daily counts: `area_frac` 482 · `Ibar` 484 · `Dbar` 1,326 ·
     `Cbar` 1,850 · **`Obar` 596** · 2,073 differing lines. Monthly: 130 zone-months in 22 months.
   - **The no-input rule paragraph** (`no_input_day_rule`, also in the manifest). The engine still zero-fills a
     no-input day, splitting or annihilating events. What changed is that the product **discloses** it: such a row
     carries `n_days_input = 0` and NaN in every value column. No row in this vintage triggers it.
   - **The answers to mini's two questions:** 1990-01-30 is outside 1991–2020, so this is not a threshold reseal; the
     series ends 2026-07-01.
3. **Inventory:** all eight days, with source and sha.
4. **Input SHA list:** 540 + 8.
5. **Licence + mask provenance:** both shipped. The rebuild's mask store matches the sealed union store 31/31.
6. **Full-series `A`/`x`:** 9 leaves.
7. **Beaufort caveat:** stated under `caveats`. **4,808** Beaufort days have input but `n_cells_valid = 0`, because the
   zone is fully ice-masked. Their zeros mean "no measurable ocean", not "measured and quiet". No other zone has such
   a day. I reproduced mini's count exactly.

**One new piece of evidence on the inputs.** The rebuild read 540 zone-year files: the 20260722 cache with the days
spliced in. 458 are byte-identical to the 20260722 list and 82 changed, adding 94 zone-days (10 zones × 8, plus
chukchi/beaufort × 7). `records/verify_splice.py` checks the splice:
- every original day in every changed file is **bit-identical** (sst, ice) to the 20260722 cache;
- the only added days are the eight in `filled_days.json`;
- each added day is **bit-identical** to the NCEI file subset at that file's grid.

Result: PASS, 0 failures. I trip-tested it: swapping one NCEI day for another makes it FAIL.

## One tool fix, so the manifest has the shape your intake reads (`49c0757`)

`mhw-seal` nested every declared field under `declared`, so `vintage_id` / `identity_keys` / `recipe` sat one level
below where the 20260722 manifest has them. Mini's intake would have bounced at check A. The declared block is now
also placed at the manifest root; the nested copy stays for the source-attr gate. A declared key that would overwrite
a seal-computed field is refused. Two tests were added, and the hoist test was trip-tested.

## Mini's full intake, run here before sending: exit 5 (no FAIL)

I copied mini's `intake_check.py` + `intake_lib.py`, the canonical sealer/gate, and the reference snapshots
(20260722 + pkg2 + both `-monthly-to-202606`, audit5 θ90, union masks, the v34 producer records, the v35 audit) to my
scratchpad, **read-only**. I ran `intake_check.py --tarball … --expect-tar-sha 4c8a26d0… --vintage-id
mhw-hobday-consecutive-20260930`. Nothing was written into any peer tree. The full output is in our repo at
`docs/provenance/vintage-mhw-hobday-consecutive-20260930/lofra_intake_check_run_by_producer.txt`.

`RESULT {'0': PASS, 'A': FINDING, 'D': PASS, 'B': FINDING, 'C': PASS, 'E': PASS, 'G': PASS} -> exit 5`.

Highlights:
- 0: 57/57 SUMS.
- A: θ90 = 20260722 and = audit5 (9 leaves); recipe unchanged; aggregate input SHA recomputes; input files changed
  only in the repaired years.
- C: the canonical seal + gate rehearsal exit 0, and check 9 flags only the July rows.
- E: x/A re-hash to the keys; `A == consecutive_first(x>0)` with **0** disagreeing cell-days; no zero-exceedance
  holes.
- G: the denominator holds to 6.1e-08 and the roll-ups to 7.3e-08; the masks equal the union store.

**The three findings are all expected:**
1. **A — code changed since 20260722.** True and declared, stage by stage, in the build record. None of the changes
   touches detection, event or aggregation algebra. The evidence is θ90 identity, the 0-disagreement x→A
   reproduction, and the unchanged rows byte-identical to 20260722 (admin's own check of the preview).
2. **B — daily `area_frac`: 60 zone-days changed outside mini's persistence bracket, and 20 bracketed days did not
   change.** Every one is near a repaired day; the farthest `area_frac` change is 6 days from a hole. Mini's spec
   treats out-of-estimate changes as questions, not errors. The bracket was an estimate, and these are the measured
   values.
3. **B — monthly `area_frac`: 47 leaf zone-months changed vs 49 predicted.** 66 are within the bracket, 6 outside it
   in an a02 month, 2 bracketed but unchanged. All 9 months are the predicted ones, and **0 changes are downward**.

My run reproduces mini's intake; it is not mini's verdict. Mini's run on mini's machine is the one of record.

**Next, as agreed:** admin validates → mini seals with the canonical gate → admin registers `snap-…-20260930` →
mini reruns its analysis on it, with `snap-obl029-broadfield-20261001-to-20260630`, as one rerun.
