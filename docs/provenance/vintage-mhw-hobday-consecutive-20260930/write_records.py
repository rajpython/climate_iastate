import json, sys
from pathlib import Path
S, ST = Path(sys.argv[1]), Path(sys.argv[2])
VID = "mhw-hobday-consecutive-20260930"
Z = "sebs nbs wgoa egoa ai_west ai_central ai_east chukchi beaufort ebs goa ai".split()
LEAVES = Z[:9]
new = {l.split()[0]: dict(x=l.split()[2], A=l.split()[4], theta90=l.split()[6]) for l in open(S / "keys_new.txt")}
v0722 = json.load(open(S / "vm0722.json"))
BR0722 = json.load(open("/Users/rajpython/dev/climate_iastate/docs/provenance/v34-build-records-20260930/build_record_vintage20260722.json"))
agg = {l.split("=")[0][2:]: l.split("=")[1].strip() for l in open(ST / f"records/oisst_input_file_shas_{VID}.txt") if l.startswith("# aggregate_")}

NO_INPUT_RULE = (
    "Engine rule for a day with no input, as it stands in code at d306292 (update_states.py), stated in words: "
    "run_state_engine pre-allocates its per-cell exceedance array over EVERY calendar day of the requested range and "
    "writes only the days present in the input, so a day with no input keeps x = 0 and is scored as a day on which no "
    "cell exceeded its threshold. Because the >=5-consecutive test is applied BEFORE gaps of <=2 days are bridged, "
    "such a day inside a run splits it; if both halves are shorter than 5 days the whole event is discarded, and if "
    "it falls inside a <=2-day gap it is absorbed as a bridged gap day (A = 1 with I never written: the "
    "area_frac > 0, Ibar = 0 signature). D, C and O then reset for the rest of that event. The engine still behaves "
    "this way; what changed is what the PRODUCT discloses. Since a672583 every daily row carries n_days_input "
    "(1 if that day's input was read, else 0) and n_cells_valid, and a row with n_days_input = 0 is written NaN in "
    "every value column (area_frac, Ibar, Dbar, Cbar, Obar) instead of zero. The monthly product averages over "
    "input days only and carries n_days (days aggregated), n_days_input and days_in_month (calendar length). In "
    "THIS vintage no row has n_days_input = 0: all eight missing days were obtained as real observations, so the "
    "NaN rule is in force but is not triggered. Event-level effects of a future no-input day (a run split by a "
    "zero-filled day) are therefore DISCLOSED by n_days_input, not repaired; a vintage with any n_days_input = 0 "
    "row should be read with that in mind.")

common_rule = v0722["recipe"]
build = {
  "record_type": "producer build record",
  "producer": "Alaska Marine Heatwave Data Project (dashboard cell; repo climate_iastate)",
  "written": "2026-09-30",
  "vintage_id": VID,
  "register_as": f"snap-{VID}",
  "supersedes": "snap-mhw-hobday-consecutive-20260722 (stays registered and immutable; adoption for analysis is Col. Raj's, directed 2026-09-30 via admin ...-20)",
  "reseal_class": "INPUT COMPLETENESS (8 missing OISST input days recovered as real observations). NOT a threshold reseal and NOT a rule change: theta90/mu byte-identical in all 12 zones; detection and aggregation algebra unchanged.",
  "why": "8 calendar days were absent from the producer's 540-file OISST input cache and the engine scored each as a no-exceedance day. 7 found by lofra-mini (area_frac > 0 with Ibar exactly 0); the 8th, 1990-01-30, found by the producer's calendar census (records/input_calendar_census.json). Every correction is upward: zero-fill can only destroy events.",
  "answers_to_mini_20261001_01_s4": {
    "eighth_day": "1990-01-30 — absent from 10 of 12 zone files (present in chukchi, beaufort). Recovered from NCEI. It lies OUTSIDE the 1991-2020 baseline, as do all eight, so theta90 does not change and this is NOT a threshold reseal (theta90_sha256 equal to 20260722 in all 12 zones, below).",
    "series_end": "2026-07-01, the same as 20260722. The series does not run past it. The 2026-07 monthly row is the mean of one day and says so (n_days = 1, days_in_month = 31)."
  },
  "pipeline": {
    "identifier": "mhw-state-dashboard", "version": "0.1.0", "repo": "climate_iastate (github.com/rajpython/climate_iastate)",
    "branch": "rebuild/input-gapfill-v35 (pushed 2026-09-30)",
    "commits_of_record": {
      "detection_engine": {"commit": "d306292c260e6e5870450a2f995295d53ba54640",
        "src/mhw/states/update_states.py": "ae7a418e35b1512358bf8ce094baaa32adfa70132ee2f30b8aa4c882b573776d",
        "config/climatology.yml": "2be665701e7b2a9fa60c86c435a6b80c98b766d48225e4a5d4b6f2656cce518c",
        "note": "CHANGED vs 20260722: records V and input_present; exceedance/event/intensity algebra untouched"},
      "climatology_smoothing": {"commit": "d306292c260e6e5870450a2f995295d53ba54640",
        "src/mhw/climatology/build_mu_theta.py": "7458475d934283d14f04f73e0ceae2a8f686bbd2b478ed437bf716ea9acdf49b",
        "src/mhw/climatology/smooth_doy.py": "b16f58045cd2c988781cfdcd722410a9df1495bfa7c392d1efe398a0949f33ca",
        "note": "build_mu_theta.py CHANGED vs 20260722 (OISST provenance stamp 9632bae, 2026-08-17; input-cache guards d306292); smooth_doy.py unchanged; theta90 byte-identical"},
      "aggregation": {"commit": "a6725836d3195d88d9f258d689cbe95d16d87fd0",
        "src/mhw/states/aggregates.py": "1a4f2a57c921566a5184fd118b9755661ef8b67f84d7d271c21cefe7e6a18a30",
        "note": "CHANGED vs 20260722: QC columns, no-input NaN rule, to_monthly(); weighted-mean equations untouched"},
      "masks": {"commit": "74176b3 (config/regions.geojson, 2026-07-01, last geometry change)",
        "src/mhw/regions/masks.py": "c8fe9f0fc50c21c511c8a574a29d8f121651ecf9448b4e4c61bb522bc7636342",
        "src/mhw/regions/weights.py": "b5cd63bf141f35e9ef1357298a92120ac0be5b98d0d33c24b43c18e1cb758041",
        "note": "masks.py CHANGED vs 20260722 in its docstring only (corrected land wording); store not rebuilt, matches snap-region-masks-oisst025-20260930 31/31"},
      "engine_and_inputs": {"commit": "d306292c260e6e5870450a2f995295d53ba54640",
        "what_ran": "mhw-backfill for all 12 zones, 1982-01-01..2026-07-01, MHW_FROZEN_INPUTS=1 (run_rebuild.sh); second run 2026-09-30 ~22:09-22:12 -0500, the run admin validated",
        "bytes_note": "the state stores were written ~10 minutes before d306292 was committed. The engine/climatology files' mtimes (update_states.py 22:08:34, build_mu_theta.py 21:55:19) predate that run and their bytes equal the commit's (hashes below), so the commit captures exactly the bytes that ran."},
      "aggregation_and_packaging": {"commit": "a6725836d3195d88d9f258d689cbe95d16d87fd0",
        "what_ran": "records/build_predictand_csv.py -> aggregate_region + to_monthly from the committed code; records/write_percell.py -> x/A npz",
        "change_vs_d306292": "aggregates.py only: delivery-spec count-column names, NaN on no-input rows, to_monthly() with calendar days_in_month. No value algebra changed (0 float32 differences vs the d306292 working files admin validated)."},
      "seal_tool": {"commit": "49c075793ec66b77fe7178d50a4c48214f5f56ea", "what_ran": "mhw-seal (src/mhw/seal.py): packs the payload, writes SHA256SUMS.txt + vintage_manifest.json, verifies gates from the packed bytes. 49c0757 hoists the declared block to the manifest root so vintage_id / identity_keys / recipe sit where the 20260722 manifest has them."},
      "file_sha256_at_both_commits": {
        "src/mhw/states/update_states.py": "ae7a418e35b1512358bf8ce094baaa32adfa70132ee2f30b8aa4c882b573776d",
        "src/mhw/climatology/build_mu_theta.py": "7458475d934283d14f04f73e0ceae2a8f686bbd2b478ed437bf716ea9acdf49b",
        "src/mhw/climatology/smooth_doy.py": "b16f58045cd2c988781cfdcd722410a9df1495bfa7c392d1efe398a0949f33ca",
        "src/mhw/regions/masks.py": "c8fe9f0fc50c21c511c8a574a29d8f121651ecf9448b4e4c61bb522bc7636342",
        "src/mhw/regions/weights.py": "b5cd63bf141f35e9ef1357298a92120ac0be5b98d0d33c24b43c18e1cb758041",
        "config/climatology.yml": "2be665701e7b2a9fa60c86c435a6b80c98b766d48225e4a5d4b6f2656cce518c",
        "config/filled_days.json": "ad236c9a6236bc248ec74f5142dde11de56dd94ad96261c057aa5daac1dd1dca",
        "config/regions.geojson": "5038762ed69802d1365938d00eeb36dce115efe0ec04660c386c3c79d2fcc8a8"},
      "src/mhw/states/aggregates.py": {"d306292": "a181bdd3a1a9c12b1eedcf378f1ba8d7a9dbcf594e300041ad585bc7f2ae2310", "a672583": "1a4f2a57c921566a5184fd118b9755661ef8b67f84d7d271c21cefe7e6a18a30"}
    },
    "code_changed_since_20260722": {
      "update_states.py": "records per-cell validity V and per-day input_present; adds the valid_cells() helper; the exceedance / event / intensity algebra is untouched (x and A reproduce under mini's flag_from_exceed with 0 disagreements, below)",
      "build_mu_theta.py": "two input-cache guards: MHW_FROZEN_INPUTS (a missing cache raises instead of reaching the network) and never-shrink (a fetch with fewer time steps than the cache is refused). Climatology algebra untouched; theta90 byte-identical.",
      "aggregates.py": "QC columns, the no-input NaN rule, to_monthly(). Weighted-mean equations untouched.",
      "masks.py": "docstring only (the corrected land wording of record); mask store not rebuilt — it matches the sealed union store snap-region-masks-oisst025-20260930 31/31 by file SHA-256"
    }
  },
  "input": {
    "dataset": "NOAA OISST v2.1 Final, AVHRR-Only (DOI 10.25921/RE9P-PT57)",
    "zone_year_files": "540 = the 20260722 cache with the eight days spliced in. 458 files byte-identical to oisst_input_file_shas_vintage20260722.txt; 82 changed (10 zones x 7 years + chukchi/beaufort x 6), adding 94 zone-days (10 x 8 + 2 x 7).",
    "splice_verification": "records/verify_splice.py: in every changed file each original day is bit-identical (sst, ice) to the 20260722 cache, the only added days are those in filled_days.json, and each added day is bit-identical to the NCEI per-day file subset at the file's own grid (lon mod 360). PASS: 82 files, 94 zone-days, 0 failures. Trip-tested: swapping one NCEI day for another makes it FAIL.",
    "gapfill_source": "NCEI per-day files https://www.ncei.noaa.gov/data/sea-surface-temperature-optimum-interpolation/v2.1/access/avhrr/<YYYYMM>/oisst-avhrr-v02r01.<YYYYMMDD>.nc, fetched 2026-09-30 (records/input_day_inventory.csv, records/ncei_same_product_provenance.md)",
    "same_product_evidence": "1990-01-30, the one day both PFEG ncdcOisst21Agg and NCEI serve: sebs subgrid (25 x 91), max |delta SST| 4.8e-07 degC, identical NaN pattern, grid-identical after subsetting.",
    "never_refetch_from_pfeg": "the PFEG aggregate is itself missing 1,196 days (7.3% of its span), 1,188 of which this cache holds, inside the 1991-2020 baseline. The cache is the authority; MHW_FROZEN_INPUTS enforces it.",
    "file_list": f"records/oisst_input_file_shas_{VID}.txt",
    "aggregate_sha256_all_548": agg["aggregate_all_548"],
    "aggregate_sha256_540_zone_year_files": agg["aggregate_540_zone_year_files"],
    "aggregate_sha256_recipe": "sha256( '\\n'.join(sorted('<basename>:<sha256>')) ), no trailing newline",
    "calendar_census": "records/input_calendar_census.json — 20260722 cache: 8 missing days per zone (7 in chukchi, beaufort); rebuild input: 0 missing in all 12 zones",
    "final_through": "2026-07-01"
  },
  "definition_applied": {**BR0722["definition_applied"],
    "_unchanged_note": "carried verbatim from build_record_vintage20260722.json: the definition did not change in this vintage (theta90 byte-identical; x -> A reproduces under consecutive_first with 0 disagreements)"},
  "no_input_day_rule": NO_INPUT_RULE,
  "columns": {
    "daily": "date, area_frac, Ibar, Dbar, Cbar, Obar, n_days_input, n_cells_valid",
    "monthly": "date, area_frac, Ibar, Dbar, Cbar, Obar, n_days, n_days_input, days_in_month",
    "n_days_input": "daily: 1 if that day's OISST input was read, else 0. monthly: days with input in the month",
    "n_cells_valid": "daily: mask cells with a usable observation (not ice-masked, finite SST and theta90). Deliberately NOT n_valid* (gate check 9 prefix)",
    "n_days": "monthly: daily rows aggregated", "days_in_month": "monthly: calendar length of the month (2026-07 reads n_days 1 of 31)",
    "monthly_rule": "calendar-month mean of the daily series over input days only (identical to the plain calendar mean in this vintage, since every day has input)",
    "value_column_definitions": "unchanged from build_record_vintage20260722.json columns{}",
    "names_settled_by": "admin ...-18 (final; every earlier naming message void)"
  },
  "caveats": {
    "beaufort_zero_valid_cell_days": "4,808 Beaufort days have input present (n_days_input = 1) but n_cells_valid = 0: every mask cell is ice-masked, so no open water exists in which a heatwave could be measured, and every value is 0. Consistent with the rule (ice masking applied identically in baseline and detection), but a reader should know these zeros mean 'no measurable ocean', not 'measured and found quiet'. No other zone has such a day. (lofra-mini's finding; reproduced here.)",
    "obar_signed": "Obar is signed and unclamped, as in 20260722: 4 negative daily values (chukchi 2, beaufort 2) + 1 negative monthly (beaufort); most negative daily -0.0248 (beaufort). Unchanged by the gap fill.",
    "terminal_month": "2026-07 monthly = one day. The July-exclusion rule of record is applied at intake by lofra-mini."
  },
  "change_vs_20260722": {
    "tolerance": "ZERO: a zone-day-column is listed if its float32 value differs at all (exact inequality). With this tolerance the table is literally every differing value, including the 12 small Obar changes admin found below the candidate's 1e-6 absolute threshold.",
    "daily_table": "records/diff_daily_vs_vintage20260722.csv (zone, changed_date, column, old, new, delta, days_from_nearest_filled_day)",
    "daily_counts": {"area_frac": 482, "Ibar": 484, "Dbar": 1326, "Cbar": 1850, "Obar": 596, "total_values": 4738, "differing_csv_lines": 2073},
    "max_distance_from_a_filled_day_days": {"area_frac": 6, "Ibar": 6, "Dbar": 58, "Obar": 60, "Cbar": 90},
    "area_frac_direction": "all 482 changes upward (0 decreases)",
    "monthly_table": "records/diff_monthly_vs_vintage20260722.csv",
    "monthly_counts": {"area_frac": 72, "Ibar": 74, "Dbar": 99, "Cbar": 114, "Obar": 91, "zone_months": 130, "distinct_months": 22},
    "unchanged_rows": "all other daily lines are byte-identical to the 20260722 CSV on the value columns (admin's check of the preview: 192,963 identical, 2,073 differing)"
  },
  "verification_by_producer": {
    "identity_key_recipe_reproduces_20260722": "the recipe below, run on the 20260722 state stores, reproduces all 34 published keys (theta90 x 12, x x 11, A x 11) exactly",
    "theta90_equal_to_20260722": "all 12 zones",
    "x_to_A_rule_check": "lofra-mini's intake_lib.flag_from_exceed (consecutive_first, 5, 2) on the shipped x reproduces the shipped A with 0 disagreeing cell-days in all 9 leaves",
    "no_input_signature": "0 rows with area_frac > 0 and Ibar == 0 in any zone",
    "intake_check_C_on_preview": "PASS, by the producer and independently by lofra-mini and admin (admin ...-20)"
  },
  "licence": {"licence": "CC BY 4.0", "licensor": "Singh, R. (Alaska Marine Heatwave Data Project)",
    "citation": f"Singh, R. (2026). Nine-zone Alaska marine-heatwave series. Alaska Marine Heatwave Data Project. Derived from NOAA OISST v2.1 under the Hobday et al. (2016) definition. Version snap-{VID}. Licensed CC BY 4.0.",
    "doi": None, "licence_file": "LICENSE-data-CC-BY-4.0.txt (identical to the 20260722 file except the version id and one added line listing this vintage)"},
  "zones": {"partition": LEAVES, "rollups_not_partition_members": {"ebs": ["sebs", "nbs"], "goa": ["wgoa", "egoa"], "ai": ["ai_west", "ai_central", "ai_east"]},
    "masks": "records/region_masks_provenance.json (the union store; rebuild's copy matches it 31/31)"}
}
key_recipe = {"theta90": "theta90 (doy, lat, lon) ascending, '<f4', C-contiguous, NaN PRESERVED; sha256 of the raw buffer",
              "x": "x (time, lat, lon) ascending, NaN -> 0.0, '<f4', C-contiguous; sha256 of the raw buffer",
              "A": "A (time, lat, lon) ascending, '<u1', C-contiguous; sha256 of the raw buffer",
              "code": "records/keys.py"}
vm = {
  "vintage_id": VID, "produced_by": "dashboard (climate_iastate)", "produced_utc": "2026-09-30",
  "supersedes": "mhw-hobday-consecutive-20260722 (snap-mhw-hobday-consecutive-20260722 stays registered and immutable)",
  "reseal_class": build["reseal_class"],
  "vintage_end": "2026-07-01", "period": "1982-01-01..2026-07-01",
  "code_commits": {"engine": "d306292c260e6e5870450a2f995295d53ba54640", "aggregation_packaging": "a6725836d3195d88d9f258d689cbe95d16d87fd0", "seal_tool": "49c075793ec66b77fe7178d50a4c48214f5f56ea", "branch": "rebuild/input-gapfill-v35 (pushed)"},
  "identity_keys": {
    "theta90_sha256": {z: new[z]["theta90"] for z in Z},
    "x_sha256": {z: new[z]["x"] for z in Z},
    "A_sha256": {z: new[z]["A"] for z in Z},
    "recipe": key_recipe,
    "note_ai": "ai x/A were published null in 20260722 (dateline multi-grid); given here from the ai state store under the same recipe. The shipped per-cell npz cover the 9 leaves; ai x/A are for identity only.",
    "theta90_vs_20260722": "byte-identical in all 12 zones"
  },
  "previous_identity_keys_20260722": v0722["identity_keys"],
  "oisst_provenance": {"product": "PFEG CoastWatch ERDDAP (ncdcOisst21Agg; NOAA OISST v2.1 Final, AVHRR-Only; DOI 10.25921/RE9P-PT57) + 8 days from NCEI per-day OISST v2.1 (same product)",
    "historical_pull": "2026-06-29; current-year pull 2026-07-21T22:14:39Z (as 20260722)", "gapfill_pull": "2026-09-30 (NCEI)",
    "final_through": "2026-07-01", "oisst_input_files": 548,
    "oisst_input_sha256": build["input"]["aggregate_sha256_all_548"],
    "oisst_input_sha256_540_zone_year_files": build["input"]["aggregate_sha256_540_zone_year_files"],
    "file_list": build["input"]["file_list"]},
  "recipe": common_rule,
  "no_input_day_rule": NO_INPUT_RULE,
  "contents": "predictand/ 24 CSVs (daily + monthly x 9 leaves + ebs/goa/ai); percell/ A_<leaf>.npz + x_<leaf>.npz (keys A|x, lat, lon, time; full series); records/ build record, input inventory, input SHA list, calendar census, splice verifier, diff tables, same-product evidence, mask provenance, filled_days.json, the scripts that produced the package; LICENSE-data-CC-BY-4.0.txt",
  "aggregation_contract": "area_frac[t] = sum_g(w_g*A_g[t]) / sum_g(w_g) over ALL mask cells; monthly = calendar-month mean of daily over input days"
}
(ST / f"records/build_record_{VID}.json").write_text(json.dumps(build, indent=2) + "\n")
(S / "declared_vintage.json").write_text(json.dumps(vm, indent=2) + "\n")
print("ok")
