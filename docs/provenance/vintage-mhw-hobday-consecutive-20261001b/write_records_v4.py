"""Vintage #4 (ice-outage correction) build record + declared manifest, derived from vintage #3's records."""
import copy, hashlib, json, subprocess, sys
from pathlib import Path
S, ST = Path(sys.argv[1]), Path(sys.argv[2])
VID, PREV = "mhw-hobday-consecutive-20261001b", "mhw-hobday-consecutive-20261001"
Z = "sebs nbs wgoa egoa ai_west ai_central ai_east chukchi beaufort ebs goa ai".split()
REPO = "/Users/rajpython/dev/climate_rebuild"
def git(*a): return subprocess.check_output(["git", "-C", REPO, *a]).decode().strip()
def fsha(commit, path): return hashlib.sha256(subprocess.check_output(["git", "-C", REPO, "show", f"{commit}:{path}"])).hexdigest()
br3 = json.load(open("/Users/rajpython/dev/climate_iastate/docs/provenance/vintage-mhw-hobday-consecutive-20261001/build_record_mhw-hobday-consecutive-20261001.json"))
vm3 = json.load(open(S / "declared_vintage_v3.json"))
k4 = {l.split()[0]: dict(x=l.split()[2], A=l.split()[4], theta90=l.split()[6]) for l in open(S / "keys_v4.txt")}
k3 = {l.split()[0]: dict(x=l.split()[2], A=l.split()[4], theta90=l.split()[6]) for l in open(S / "keys_v3.txt")}
summ = json.load(open(S / "v4_vs_v3_summary.json"))
FIX1, FIX2, HEAD = git("rev-parse", "982fa7e"), git("rev-parse", "f634e43"), git("rev-parse", "HEAD")
changed = [z for z in Z if k4[z]["theta90"] != k3[z]["theta90"]]
same = [z for z in Z if z not in changed]

RULE = ("Ice-field outage rule (mhw.climatology.ice_outage; config/ice_outage_days.json). OISST writes no ice value over "
        "open water, so a blank ice cell normally means ice-free. On 176 days the ice field is absent from the product "
        "(171 global days with not one ice value on Earth: 1987-12-06..1988-01-10, 2016-01, 2016-04-18..06-30, "
        "2017-01-07..02-28, 2020-08 (2 days), 2020-12 (3 days); and a regional outage 2024-04-22..26 over the Bering/"
        "Chukchi/Beaufort and northern-GOA zones). On those days a BLANK cell's ice is interpolated linearly in time "
        "between the zone's last non-outage day before and first non-outage day after, and set to 0 where SST > 2 degC; "
        "the unchanged threshold test (ice > 0.15 -> treated as missing) then applies. Identical in the 1991-2020 "
        "baseline and in detection; observed ice values are kept; inputs are not altered. Before this vintage, such "
        "cells were scored as open water: frozen water at about -1.7 degC entered the baseline and detection, and "
        "Beaufort/Chukchi February 2017 read heatwave areas of 0.256/0.192 against <= 0.017 in every other year.")

br = copy.deepcopy(br3)
br.pop("change_vs_vintage_2", None)
br["written"] = "2026-10-01"
br["vintage_id"] = VID
br["register_as"] = f"snap-{VID}"
br["supersedes"] = f"snap-{PREV} (vintage #3; stays registered and immutable). Correction directed by Col. Raj 2026-10-01 ('this needs to be fixed'), after lofra-mini's question mini-to-dashboard-cc-admin-m1-m4-20261001-05."
br["reseal_class"] = (f"THRESHOLD RESEAL (input-quality correction, no rule change to the Hobday definition): theta90 changes in "
    f"{len(changed)} zones ({', '.join(changed)}) because outage-day frozen-water samples leave the 1991-2020 baseline; "
    f"theta90, x and A byte-identical to #3 in {', '.join(same)}. Inputs identical to #3 (same 609 files).")
br["why"] = RULE
br["series_end"] = "2026-08-31 (unchanged from #3)"
br["definition_applied"]["series_span"] = "1982-01-01 to 2026-08-31"
br["definition_applied"].pop("_correction_20261001", None)
br["definition_applied"]["climatology"]["ice_masking"] = ("SST set NaN where the OISST ice fraction exceeds 0.15, applied identically when "
    "building the baseline and when detecting daily exceedance; on ice-field-outage days the ice fraction of a blank cell is "
    "taken from the outage rule (below) instead of being read as open water")
br["definition_applied"]["_changed_in_this_vintage"] = "climatology.ice_masking only (the outage rule); every other field verbatim from #1-#3"
br["ice_outage_rule"] = RULE
p = br["pipeline"]; c = p["commits_of_record"]
c["ice_outage"] = {"commit": FIX2, "first_version": FIX1,
    "src/mhw/climatology/ice_outage.py": fsha(FIX2, "src/mhw/climatology/ice_outage.py"),
    "config/ice_outage_days.json": fsha(FIX2, "config/ice_outage_days.json"),
    "note": "NEW in #4. The first version (982fa7e: larger of the two bracketing days) over-masked melt-season open water (39% in back-test) and was replaced by f634e43 before any data was packaged."}
c["detection_engine"]["commit"] = FIX2
c["detection_engine"]["src/mhw/states/update_states.py"] = fsha(FIX2, "src/mhw/states/update_states.py")
c["detection_engine"]["note"] = "CHANGED vs #3: reads ice through apply_ice_outages (one line); algebra untouched"
c["climatology_smoothing"]["commit"] = FIX2
c["climatology_smoothing"]["src/mhw/climatology/build_mu_theta.py"] = fsha(FIX2, "src/mhw/climatology/build_mu_theta.py")
c["climatology_smoothing"]["note"] = "CHANGED vs #3: reads ice through apply_ice_outages (one line); smoothing/percentile algebra untouched; theta90 REBUILT for all 12 zones"
c["engine_and_inputs"]["what_ran"] = ("2026-10-01 ~15:00 -0500, MHW_FROZEN_INPUTS=1: mhw-build-climatology for all 12 zones, then run_rebuild.sh 2026-08-31 "
    "(mhw-backfill 1982-01-01..2026-08-31, all 12 zones); no network fetch in any log")
c["engine_and_inputs"]["bytes_note"] = f"repo HEAD at packaging {HEAD[:7]} (only a lint commit after {FIX2[:7]})"
c["engine_and_inputs"]["determinism_check"] = "with config/ice_outage_days.json moved aside, mhw-build-climatology --region chukchi reproduced the registered theta90 94a3d793... byte-for-byte; so every theta90 change in #4 is the outage rule's"
p["code_changed_since_vintage_3"] = {"src/mhw/climatology/ice_outage.py": "NEW", "config/ice_outage_days.json": "NEW",
    "build_mu_theta.py / update_states.py": "one line each: ice read through apply_ice_outages",
    "scripts/ice_outage_rule_backtest.py": "NEW (evidence for the rule choice)"}
i = br["input"]
i["vs_vintage_3"] = "IDENTICAL: the same 609 files and aggregate; no input was changed or re-fetched for #4"
i["file_list"] = f"records/oisst_input_file_shas_{VID}.txt"
i["ice_field_outages"] = {
  "config": "records/ice_outage_days.json",
  "global_evidence": "records/ice_outage_evidence_ncei_global_ice_counts.csv: NCEI per-day global files for all 702 days on which the Chukchi or Beaufort zone had no ice value; n80 = count of ice values north of 80N. 171 days have 0 (and 0 in both hemispheres); every other day has >= 1000. Clean split.",
  "regional_evidence": "2024-04-22..26: zone ice field empty while present on 04-21 and 04-27 (e.g. Beaufort 1079 -> 0 x5 -> 1079 cells); the only regional outage found scanning all zones and days",
  "partial_blanks": "records/ice_partial_blank_scan.json: outside the 176 days, cells blank yet > 0.5 ice on both neighbouring days: at most 9 cell-days in any zone (isolated; e.g. Chukchi Aug 1987 on alternate days, the every-other-day SMMR era). Not treated; disclosed.",
  "not_outages": "late-summer/autumn ice-free Beaufort/Chukchi spells (e.g. Sep-Oct 2025, Sep 2017/2019/2023/2024): the global field is present; genuine open water; left as observed",
  "rule_choice": "records/ice_outage_rule_backtest_results.txt (script records/ice_outage_rule_backtest.py): candidate rules scored against the real ice field hidden over outage-shaped windows in normal years"}
br["caveats"]["beaufort_zero_valid_cell_days"] = (f"{summ['beaufort']['zero_valid_days']:,} Beaufort days have input present but n_cells_valid = 0 (every mask cell ice-masked; "
    "values 0 mean 'no measurable ocean', not 'measured and quiet'). Up from 4,831 in #3: the outage days in ice season are now masked as they should be. No other zone has such a day.")
br["caveats"]["ice_outage_days"] = "On the 176 outage days ice status is inferred (rule above), not observed. Back-test: >= 97% of ice cells caught in every season; 5.5-12% of open-water cells conservatively treated as missing."
br["change_vs_vintage_3"] = {
  "tolerance": "ZERO (any float32 inequality)",
  "daily_table": "records/diff_daily_vs_vintage20261001.csv", "monthly_table": "records/diff_monthly_vs_vintage20261001.csv",
  "by_zone": summ,
  "headline": "February 2017 area_frac: Beaufort 0.2558 -> 0.0000, Chukchi 0.1918 -> 0.0000, nbs 0.0977 -> 0.0139; the highest other February is unchanged in kind (Beaufort 0.0149, Chukchi 0.0170). Changes are predominantly DOWNWARD (artifact removal); upward changes are small (max +0.0136, nbs).",
  "unchanged_zones": same}
br["verification_by_producer"] = {
  "theta90_unchanged_zones": same, "theta90_changed_zones": changed,
  "x_A_identical_to_vintage_3": same,
  "determinism": c["engine_and_inputs"]["determinism_check"],
  "no_input_signature": "0 rows with area_frac > 0 and Ibar == 0 in any zone",
  "x_to_A_rule_check": "run with lofra-mini's intake_lib.flag_from_exceed in the full intake"}
br["licence"]["citation"] = br3["licence"]["citation"].replace(PREV, VID)
br["licence"]["licence_file"] = "LICENSE-data-CC-BY-4.0.txt (identical to #3's except the version id and one added line listing this vintage)"
(ST / f"records/build_record_{VID}.json").write_text(json.dumps(br, indent=2) + "\n")

vm = copy.deepcopy(vm3)
vm["vintage_id"] = VID; vm["produced_utc"] = "2026-10-01"
vm["supersedes"] = f"{PREV} (snap-{PREV} stays registered and immutable)"
vm["reseal_class"] = br["reseal_class"]
vm["code_commits"]["ice_outage"] = FIX2
vm["code_commits"]["engine"] = FIX2
vm["identity_keys"]["theta90_sha256"] = {z: k4[z]["theta90"] for z in Z}
vm["identity_keys"]["x_sha256"] = {z: k4[z]["x"] for z in Z}
vm["identity_keys"]["A_sha256"] = {z: k4[z]["A"] for z in Z}
vm["identity_keys"].pop("theta90_vs_vintages_1_2", None)
vm["identity_keys"]["theta90_vs_vintage_3"] = f"CHANGED in {changed}; byte-identical in {same}"
vm["previous_identity_keys_20261001"] = vm3["identity_keys"]
vm.pop("previous_identity_keys_20260930", None)
vm["recipe"] = copy.deepcopy(vm3["recipe"])
vm["recipe"]["theta90"] = vm3["recipe"]["theta90"] + "; ice-field-outage days: blank-cell ice inferred (interpolated, open above 2 degC) per mhw.climatology.ice_outage"
vm["ice_outage_rule"] = RULE
vm["oisst_provenance"]["file_list"] = f"records/oisst_input_file_shas_{VID}.txt"
(S / "declared_vintage_v4.json").write_text(json.dumps(vm, indent=2) + "\n")
print("ok", changed, same)
