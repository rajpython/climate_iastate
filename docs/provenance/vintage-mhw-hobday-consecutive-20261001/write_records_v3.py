"""Vintage #3 build record + declared manifest, derived from vintage #2's records."""
import copy, json, sys
from pathlib import Path
S, ST = Path(sys.argv[1]), Path(sys.argv[2])
VID, PREV = "mhw-hobday-consecutive-20261001", "mhw-hobday-consecutive-20260930"
Z = "sebs nbs wgoa egoa ai_west ai_central ai_east chukchi beaufort ebs goa ai".split()
br2 = json.load(open(S / f"staging/records/build_record_{PREV}.json"))
vm2 = json.load(open(S / "declared_vintage.json"))
k3 = {l.split()[0]: dict(x=l.split()[2], A=l.split()[4], theta90=l.split()[6]) for l in open(S / "keys_v3.txt")}
hdr = {l.split("=")[0][2:]: l.split("=")[1].strip() for l in open(ST / f"records/oisst_input_file_shas_{VID}.txt") if l.startswith("# aggregate_")}
agg_all = next(v for k, v in hdr.items() if k.startswith("aggregate_all_"))
agg540 = hdr["aggregate_540_zone_year_files"]
SPLICE_COMMIT = "30b3cb5"  # replaced with the full sha below
import subprocess
SPLICE_FULL = subprocess.check_output(["git", "-C", "/Users/rajpython/dev/climate_rebuild", "rev-parse", SPLICE_COMMIT]).decode().strip()
SEAL_FULL = "49c075793ec66b77fe7178d50a4c48214f5f56ea"

br = copy.deepcopy(br2)
br["written"] = "2026-10-01"
br["vintage_id"] = VID
br["register_as"] = f"snap-{VID}"
br["supersedes"] = f"snap-{PREV} (vintage #2; stays registered and immutable). Extension directed by Col. Raj via admin ...-20261001-02: 'extend every input to 2026-08-31 ... if (and only if) all data can go up to August'."
br["reseal_class"] = "EXTENSION (2026-07-02..2026-08-31 appended from NCEI final per-day files). NOT a threshold reseal and NOT a rule change: theta90 byte-identical to #1/#2 in all 12 zones; the eight repaired days carried over unchanged; detection and aggregation algebra unchanged."
br["why"] = "Col. Raj directed every input of the single rerun to reach 2026-08-31. NCEI lists 31/31 July and 31/31 August 2026 OISST v2.1 per-day files as FINAL (no _preliminary), so the condition holds on the producer side."
br.pop("answers_to_mini_20261001_01_s4", None)
br["definition_applied"]["series_span"] = "1982-01-01 to 2026-08-31"  # A2: never inherit the span from an older vintage
br["series_end"] = "2026-08-31. No September days. July and August are complete months (monthly n_days = n_days_input = days_in_month = 31)."
p = br["pipeline"]
p["branch"] = "rebuild/input-gapfill-v35 (pushed)"
c = p["commits_of_record"]
c["input_splice"] = {"commit": SPLICE_FULL, "src/mhw/fetch/ncei_daily.py": None,
    "what_ran": "mhw-splice-ncei --start 2026-07-02 --end 2026-08-31 into the 12 oisst_<zone>_2026.nc files (append-only, never-shrink, final files only, subset on each file's own grid). The same module reproduces vintage #2's eight-day splice bit-for-bit (188/188 zone-day-vars).",
    "note": "NEW in #3: the splice is now committed code (in #2 it was an inline script, independently verified)"}
c["engine_and_inputs"]["what_ran"] = "run_rebuild.sh 2026-08-31 (committed in " + SPLICE_FULL[:7] + "): mhw-backfill for all 12 zones, 1982-01-01..2026-08-31, MHW_FROZEN_INPUTS=1; 2026-10-01 ~13:35-13:38 -0500; no network fetch in any log"
c["engine_and_inputs"]["bytes_note"] = "engine/climatology bytes unchanged since d306292 (hashes below); the run used committed code"
c["seal_tool"] = {"commit": SEAL_FULL, "what_ran": "mhw-seal; declared block hoisted to the manifest root"}
import hashlib
c["input_splice"]["src/mhw/fetch/ncei_daily.py"] = hashlib.sha256(subprocess.check_output(["git", "-C", "/Users/rajpython/dev/climate_rebuild", "show", f"{SPLICE_FULL}:src/mhw/fetch/ncei_daily.py"])).hexdigest()
p["code_changed_since_vintage_2"] = {"src/mhw/fetch/ncei_daily.py": "NEW (the splice, as code)", "run_rebuild.sh": "committed; end date is an argument", "everything else": "byte-identical to #2's commits (engine d306292, aggregation a672583, seal 49c0757)"}

i = br["input"]
i["zone_year_files"] = "540 = vintage #2's files with 2026-07-06..08-31 appended to the twelve 2026 files (57 days each, 684 zone-days). The other 528 are byte-identical to #2."
i["extension"] = {
  "days": "2026-07-02..2026-08-31 (61 days)",
  "from_ncei": "2026-07-06..2026-08-31 (57 days), NCEI final per-day files fetched 2026-10-01 (records/ncei_extension_files_sha256.txt)",
  "already_present": "2026-07-02..07-05 (4 days) were already in the 2026 files from the 2026-07-21 PFEG pull (vintage #2 ended at 07-01 by its end date, not its inputs). KEPT, not replaced (append-only): checked against the NCEI final files, max |dSST| <= 1.9e-06 degC (1-2 float32 ulps) and |dice| <= 6e-08 in all 12 zones, identical NaN pattern (records/cached_20260702_0705_vs_ncei_final.json).",
  "verification": "records/verify_extend.py (independent of the splice module): in all 12 files every #2 day is bit-identical, the added days are exactly 2026-07-06..08-31, each is bit-identical to its NCEI file on the cache grid, and 2026-01-01..08-31 has no gap. PASS, 684 zone-days, 0 failures. Trip-tested (a wrong end date FAILs)."}
i["file_list"] = f"records/oisst_input_file_shas_{VID}.txt"
i["aggregate_sha256_all_609"] = agg_all
i.pop("aggregate_sha256_all_548", None)
i["aggregate_sha256_540_zone_year_files"] = agg540
i["calendar_census"] = "records/input_calendar_census.json — rebuild input 1982-01-01..2026-08-31: 0 missing days in all 12 zones"
i["final_through"] = "2026-08-31"
i["splice_verification"] = "vintage #2's eight days: records/verify_splice.py (unchanged, carried over)"

br["columns"]["monthly_rule"] = "calendar-month mean of the daily series over input days only (every day has input in this vintage, so identical to the plain calendar mean)"
br["columns"]["days_in_month"] = "monthly: calendar length of the month; every month is complete through 2026-08 (no partial terminal month)"
br["caveats"]["beaufort_zero_valid_cell_days"] = br2["caveats"]["beaufort_zero_valid_cell_days"].replace("4,808", "4,831") + " Count updated for #3: 4,831 (4,808 through 2026-07-01 + 23 in July/August)."
br["caveats"]["terminal_month"] = "None: the series ends on the last day of August, so the last monthly row is a complete month. The July-excluded derivative is retired (admin ...-20261001-02)."
br["caveats"]["obar_signed"] = "Obar is signed and unclamped: 4 negative daily values (chukchi 2, beaufort 2) + 1 negative monthly (beaufort); most negative daily -0.0248. Unchanged from #1/#2."

d = json.load(open(S / "v3_diff_summary.json"))
br.pop("change_vs_20260722", None)
br["change_vs_vintage_2"] = d
br["verification_by_producer"] = {
  "theta90_equal_to_vintage_1_and_2": "all 12 zones",
  "x_through_2026_07_01_identical_to_vintage_2": "all 12 zones (x depends only on SST and theta90)",
  "A_changes_through_2026_07_01": "only 0->1, only on cells continuously active to 2026-07-01: nbs 51 cell-days, ebs 51 (the same cells), sebs 1 (outside the sebs mask, so no sebs value moves); 0 elsewhere",
  "state_stores_1982_2025": "byte-identical to vintage #2 (checked file-by-file for 2024, 2025)",
  "x_to_A_rule_check": "run with lofra-mini's intake_lib.flag_from_exceed in the full intake (below)",
  "no_input_signature": "0 rows with area_frac > 0 and Ibar == 0 in any zone"}
br["licence"]["citation"] = br2["licence"]["citation"].replace(PREV, VID)
br["licence"]["licence_file"] = "LICENSE-data-CC-BY-4.0.txt (identical to #2's except the version id and one added line listing this vintage)"
br["no_input_day_rule"] = br2["no_input_day_rule"]
(ST / f"records/build_record_{VID}.json").write_text(json.dumps(br, indent=2) + "\n")

vm = copy.deepcopy(vm2)
vm["vintage_id"] = VID
vm["produced_utc"] = "2026-10-01"
vm["supersedes"] = f"{PREV} (snap-{PREV} stays registered and immutable)"
vm["reseal_class"] = br["reseal_class"]
vm["vintage_end"] = "2026-08-31"
vm["period"] = "1982-01-01..2026-08-31"
vm["code_commits"] = {"engine": "d306292c260e6e5870450a2f995295d53ba54640", "aggregation_packaging": "a6725836d3195d88d9f258d689cbe95d16d87fd0",
                      "input_splice": SPLICE_FULL, "seal_tool": SEAL_FULL, "branch": "rebuild/input-gapfill-v35 (pushed)"}
vm["identity_keys"]["theta90_sha256"] = {z: k3[z]["theta90"] for z in Z}
vm["identity_keys"]["x_sha256"] = {z: k3[z]["x"] for z in Z}
vm["identity_keys"]["A_sha256"] = {z: k3[z]["A"] for z in Z}
vm["identity_keys"]["theta90_vs_vintages_1_2"] = "byte-identical in all 12 zones"
vm["identity_keys"].pop("theta90_vs_20260722", None)
vm["previous_identity_keys_20260930"] = vm2["identity_keys"]
vm.pop("previous_identity_keys_20260722", None)
o = vm["oisst_provenance"]
o["product"] = "PFEG CoastWatch ERDDAP (ncdcOisst21Agg; NOAA OISST v2.1 Final, AVHRR-Only; DOI 10.25921/RE9P-PT57) + NCEI per-day OISST v2.1 final files (same product): the 8 repaired days and 2026-07-06..08-31"
o["gapfill_pull"] = "2026-09-30 (NCEI, 8 days); 2026-10-01 (NCEI, 61 days, of which 57 spliced)"
o["final_through"] = "2026-08-31"
o["oisst_input_files"] = 609
o["oisst_input_sha256"] = agg_all
o["oisst_input_sha256_540_zone_year_files"] = agg540
o["file_list"] = f"records/oisst_input_file_shas_{VID}.txt"
vm["contents"] = vm2["contents"].replace("diff tables", "diff tables vs vintage #2").replace("splice verifier", "splice verifiers (#2's eight days; #3's extension)")
vm["aggregation_contract"] = "area_frac[t] = sum_g(w_g*A_g[t]) / sum_g(w_g) over ALL mask cells; monthly = calendar-month mean of daily over input days"
(S / "declared_vintage_v3.json").write_text(json.dumps(vm, indent=2) + "\n")
print("ok", SPLICE_FULL[:7], agg_all[:8])
