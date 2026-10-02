"""Vintage #6 build record + declared manifest, derived from vintage #5's producer records."""
import copy, hashlib, json, subprocess, sys
from pathlib import Path
import pandas as pd
S, ST = Path(sys.argv[1]), Path(sys.argv[2])
VID, PREV = "mhw-hobday-consecutive-20261001d", "mhw-hobday-consecutive-20261001c"
Z = "sebs nbs wgoa egoa ai_west ai_central ai_east chukchi beaufort ebs goa ai".split()
REPO = "/Users/rajpython/dev/climate_rebuild"
def git(*a): return subprocess.check_output(["git", "-C", REPO, *a]).decode().strip()
def fsha(c, p): return hashlib.sha256(subprocess.check_output(["git", "-C", REPO, "show", f"{c}:{p}"])).hexdigest()
P5 = "/Users/rajpython/dev/climate_iastate/docs/provenance/vintage-mhw-hobday-consecutive-20261001c"
br5 = json.load(open(f"{P5}/build_record_{PREV}.json"))
vm5 = json.load(open(S / "declared_vintage_v5.json"))
k6 = {l.split()[0]: dict(x=l.split()[2], A=l.split()[4], theta90=l.split()[6]) for l in open(S / "keys_v6.txt")}
diff = json.load(open(S / "v6_diff_summary.json")); safety = json.load(open(S / "v6_engine_safety.json"))
dry = json.load(open(S / "dryrun_b_effect.json")); sup = json.load(open(ST / "support/SUPPORT-SUMMARY.json"))
D = pd.read_csv(ST / "records/diff_daily_vs_vintage5_20261001c.csv")
maskmax = {z: round(float(D[(D.zone == z) & (D.column == "area_frac") & (D.rule == "mask")].delta.min()), 4) if ((D.zone == z) & (D.column == "area_frac") & (D.rule == "mask")).any() else 0.0 for z in Z}
C6 = git("rev-parse", "6cad427")
hdr = {l.split("=")[0][2:]: l.split("=")[1].strip() for l in open(ST / f"records/oisst_input_file_shas_{VID}.txt") if l.startswith("# aggregate_")}
agg_all = next(v for k, v in hdr.items() if k.startswith("aggregate_all_")); agg540 = hdr["aggregate_540_zone_year_files"]

RULE6 = ("Data-availability rule (vintage #6; joint lofra-admin + lofra-mini decision approved by Col. Raj, admin ...-20261001-17; "
         "outside advice concurred). The 11-day window and the 31-day smoothing are unchanged. AFTER the smoothing, theta90 and mu "
         "are set NaN at every cell x day-of-year whose OWN 11-day baseline window (1991-2020) held zero usable observations "
         "(SST present, not ice-masked, ice-outage rule applied). Without it the NaN-aware smoothing creates such values from "
         "observations up to 20 days away (e.g. a 7.01 degC 11 July 2019 value as the 21-June threshold at 72.375N -164.125 in the "
         "Chukchi). A masked cell-day is invalid and stays in the fixed whole-zone denominator. This is an explicit data-availability "
         "rule of this implementation, not a requirement of Hobday et al. (2016). Every supported value is bit-identical to #5.")
AREA6 = ("Detected area (admin ...-20261001-17 item v): area_frac and the conditional means Ibar/Dbar/Cbar/Obar count a cell on day d only "
         "if it is in a qualifying event (A, Hobday: >=5 consecutive exceedance days, gaps <=2 days bridged) AND scorable that day (V: SST "
         "present, not ice-masked, theta90 defined). An unscorable day inside a bridged gap keeps event continuity (A, D, C as the engine "
         "writes them) but is never detected area. Valid (scorable) bridged gap days still count, as part of the Hobday event.")

br = copy.deepcopy(br5)
for k in ("change_vs_vintage_4", "_correction_20261001_A3", "valid_cell_drops_vs_vintage_3_by_channel"):  # stale-field fix 2026-10-02 below
    br.pop(k, None)
br["written"] = "2026-10-01"; br["vintage_id"] = VID; br["register_as"] = f"snap-{VID}"
br["supersedes"] = f"snap-{PREV} (vintage #5; stays registered and immutable)"
br["reseal_class"] = ("THRESHOLD RESEAL (data-availability rule): theta90/mu values with zero support in their own 11-day window removed in "
                      "sebs, nbs, wgoa, chukchi, beaufort, ebs, goa; byte-identical to #5 in egoa and the four Aleutian zones; every supported "
                      "value bit-identical to #5. Plus the detected-area rule in the aggregation. Inputs identical to #5.")
br["why"] = RULE6
br["data_availability_rule"] = RULE6
br["detected_area_rule"] = AREA6
br["definition_applied"]["climatology"]["data_availability_rule"] = "theta90/mu NaN where the doy's own 11-day baseline window held zero usable observations (after the unchanged smoothing)"
br["definition_applied"]["_changed_in_this_vintage"] = "climatology.data_availability_rule added; aggregation counts detected area only on scorable cell-days"
br["definition_applied"]["series_span"] = "1982-01-01 to 2026-08-31"
c = br["pipeline"]["commits_of_record"]
for stage, path in (("climatology_smoothing", "src/mhw/climatology/build_mu_theta.py"), ("aggregation", "src/mhw/states/aggregates.py")):
    c[stage]["commit"] = C6; c[stage][path] = fsha(C6, path)
c["climatology_smoothing"]["src/mhw/climatology/smooth_doy.py"] = fsha(C6, "src/mhw/climatology/smooth_doy.py")
c["climatology_smoothing"]["config/climatology.yml"] = fsha(C6, "config/climatology.yml")
c["climatology_smoothing"]["note"] = "CHANGED vs #5: support_counts() + mask_unsupported() after the unchanged smoothing (config post_smoothing.mask_unsupported: true)"
c["aggregation"]["note"] = "CHANGED vs #5: detected area = A x V; QC column n_cells_event_unscorable"
c["vintage6_rules"] = {"commit": C6, "tests": "tests/test_support_mask.py (+3, incl. the 7.01 case in miniature)"}
c["engine_and_inputs"]["what_ran"] = (f"2026-10-01, isolated checkout of {C6[:7]} with cloned inputs (the board's data untouched), MHW_FROZEN_INPUTS=1: "
                                      "mhw-build-climatology for all 12 zones, then mhw-backfill 1982-01-01..2026-08-31 for all 12; no network fetch")
br["pipeline"].pop("code_changed_since_vintage_4", None); br["theta90_undefined"].pop("counts_unchanged_from_vintage_4", None)
br["pipeline"]["code_changed_since_vintage_5"] = {"src/mhw/climatology/smooth_doy.py": "support_counts, mask_unsupported", "src/mhw/climatology/build_mu_theta.py": "applies the rule; writes support_<zone>.zarr",
                                                 "src/mhw/states/aggregates.py": "detected area A x V; n_cells_event_unscorable", "config/climatology.yml": "post_smoothing.mask_unsupported: true"}
i = br["input"]
i["vs_vintage_5"] = "IDENTICAL: the same 614 files and aggregate; nothing re-fetched"
i.pop("vs_vintage_3_4", None); i["file_list"] = f"records/oisst_input_file_shas_{VID}.txt"
i["aggregate_sha256_all_614"] = agg_all; i["aggregate_sha256_540_zone_year_files"] = agg540
br["valid_frac_confirmation"] = ("valid_frac = sum(w * (V AND mask)) / sum(w * mask), w = cos(lat): AREA-WEIGHTED. V = valid_cells(sst, ice, theta) = "
                                 "not ice-masked AND finite SST AND finite theta90: it INCLUDES threshold availability, not only SST presence "
                                 "(src/mhw/states/update_states.py valid_cells; aggregates.py). No corrected column needed.")
br["engine_safety_detected_area"] = {"rule": AREA6, "per_zone": safety,
  "summary": ("Recomputed from the per-cell state arrays: area_frac == sum(w*A*V)/sum(w) on every day of every zone (max |diff| <= 3.0e-08, float32). "
              "Unscorable cell-days inside events (excluded from area): 43 across the nine leaves (more counting the roll-ups), ALL from ice or "
              "missing SST, NONE from a masked threshold. Valid bridged gap days still counted (Hobday event membership): see valid_gap_days_counted."),
  "interpretation_asked_of_admin": "admin ...-17 (v) first sentence read literally ('only cells that are exceedance days') would also drop VALID bridged gap days; implemented: only unscorable days are excluded. Confirm."}
br["support_counts"] = {"files": "support/support_counts_<zone>.nc (audit5 layout)", "per_zone": sup,
  "which_count": "n_raw_window = the doy's OWN 11-day window (the raw percentile's sample); n_support_obs / n_support_years = DISTINCT observations / years behind the SMOOTHED value (+-20 days). The earlier '1-3 values' figures were n_raw_window."}
br["change_vs_vintage_5"] = {"tolerance": "ZERO", "daily_table": "records/diff_daily_vs_vintage5_20261001c.csv (column rule = mask | detected_area | both)",
  "monthly_table": "records/diff_monthly_vs_vintage5_20261001c.csv", "area_frac_by_zone": diff,
  "mask_rule_maxima_vs_dry_run": {z: {"v6_mask_rule_max_daily_down": maskmax[z], "dry_run": dry.get(z, {}).get("max_abs_daily")} for z in Z},
  "summary": "Every area_frac change is a REDUCTION. Mask-rule lines reproduce the dry run (0cdb112) exactly: nbs -0.0271 (1985-02-01), monthly -0.0038; ebs -0.0097/-0.0014; beaufort -0.0012/-0.0002. Detected-area lines are a separate small channel (max -0.0037 chukchi 2019-08-10), which is why beaufort's overall daily max is -0.0024 (2021-10-18)."}
br["caveats"]["thin_support"] = ("Supported thresholds can still rest on few observations: defined theta90 whose smoothed value rests on ONE baseline year: "
                                 + ", ".join(f"{z} {sup[z]['defined_with_support_years_1']:,}" for z in Z if sup[z]['defined_with_support_years_1'])
                                 + ". No minimum-count rule this round (admin ...-17); the 1-3-observation sensitivity is mini's.")
br["caveats"]["beaufort_zero_valid_cell_days"] = br5["caveats"]["beaufort_zero_valid_cell_days"]
br["licence"]["citation"] = br5["licence"]["citation"].replace(PREV, VID)
br["licence"]["licence_file"] = "LICENSE-data-CC-BY-4.0.txt (identical to #5's except the version id and one added line listing this vintage)"
(ST / f"records/build_record_{VID}.json").write_text(json.dumps(br, indent=2) + "\n")

vm = copy.deepcopy(vm5)
vm["vintage_id"] = VID; vm["supersedes"] = f"{PREV} (snap-{PREV} stays registered and immutable)"
vm["reseal_class"] = br["reseal_class"]; vm["code_commits"]["vintage6_rules"] = C6
vm["identity_keys"]["theta90_sha256"] = {z: k6[z]["theta90"] for z in Z}
vm["identity_keys"]["x_sha256"] = {z: k6[z]["x"] for z in Z}
vm["identity_keys"]["A_sha256"] = {z: k6[z]["A"] for z in Z}
for k in ("theta90_vs_vintage_3", "theta90_vs_vintage_4"): vm["identity_keys"].pop(k, None)
vm["identity_keys"]["theta90_vs_vintage_5"] = "identical in egoa, ai_west, ai_central, ai_east, ai; elsewhere only zero-support values removed (every kept value bit-identical)"
vm["previous_identity_keys_20261001c"] = vm5["identity_keys"]
for k in ("previous_identity_keys_20261001", "unsealed_vintage_4_identity_keys_20261001b"): vm.pop(k, None)
vm["recipe"]["theta90"] = vm5["recipe"]["theta90"] + "; data-availability rule: theta90/mu NaN where the doy's own 11-day baseline window held zero observations (after smoothing)"
vm["data_availability_rule"] = RULE6; vm["detected_area_rule"] = AREA6
vm["aggregation_contract"] = "area_frac[t] = sum_g(w_g*A_g[t]*V_g[t]) / sum_g(w_g) over ALL mask cells (detected area; percell/V_<zone>.npz shipped); monthly = calendar-month mean of daily over input days"
vm["oisst_provenance"]["file_list"] = f"records/oisst_input_file_shas_{VID}.txt"
(S / "declared_vintage_v6.json").write_text(json.dumps(vm, indent=2) + "\n")
print("ok", C6[:7])
