"""Vintage #5 build record + declared manifest, derived from vintage #4's producer records (incl. the addendum)."""
import copy, hashlib, json, subprocess, sys
from pathlib import Path
S, ST = Path(sys.argv[1]), Path(sys.argv[2])
VID, PREV, NOTSEALED = "mhw-hobday-consecutive-20261001c", "mhw-hobday-consecutive-20261001", "mhw-hobday-consecutive-20261001b"
Z = "sebs nbs wgoa egoa ai_west ai_central ai_east chukchi beaufort ebs goa ai".split()
REPO = "/Users/rajpython/dev/climate_rebuild"
def git(*a): return subprocess.check_output(["git", "-C", REPO, *a]).decode().strip()
def fsha(c, p): return hashlib.sha256(subprocess.check_output(["git", "-C", REPO, "show", f"{c}:{p}"])).hexdigest()
P4 = "/Users/rajpython/dev/climate_iastate/docs/provenance/vintage-mhw-hobday-consecutive-20261001b"
br4 = json.load(open(f"{P4}/build_record_{NOTSEALED}.json"))
vm4 = json.load(open(S / "declared_vintage_v4.json"))
vm3 = json.load(open(S / "declared_vintage_v3.json"))
k5 = {l.split()[0]: dict(x=l.split()[2], A=l.split()[4], theta90=l.split()[6]) for l in open(S / "keys_v5.txt")}
chan = json.load(open(ST / "records/valid_drop_channels_v5_vs_v3.json"))
hdr = {l.split("=")[0][2:]: l.split("=")[1].strip() for l in open(ST / f"records/oisst_input_file_shas_{VID}.txt") if l.startswith("# aggregate_")}
agg_all = next(v for k, v in hdr.items() if k.startswith("aggregate_all_")); agg540 = hdr["aggregate_540_zone_year_files"]
REPL = git("rev-parse", "26e91bc"); HEAD = git("rev-parse", "HEAD")
import pandas as pd
diff = pd.read_csv(ST / "records/diff_daily_vs_vintage4_20261001b.csv")
cen = pd.read_csv(ST / "records/reissue_census_compare.csv")

br = copy.deepcopy(br4)
for k in ("change_vs_vintage_3", "_addendum_20261001_theta90_undefined"):
    br.pop(k, None)
br["written"] = "2026-10-01"; br["vintage_id"] = VID; br["register_as"] = f"snap-{VID}"
br["supersedes"] = f"snap-{PREV} (vintage #3; stays registered and immutable). Vintage #4 ({NOTSEALED}) was built and validated but NEVER sealed or registered (admin ...-20261001-10); #5 replaces it."
br["reseal_class"] = ("THRESHOLD RESEAL relative to #3 (the ice-field-outage rule of #4, carried unchanged; theta90 changes in 7 ice zones, "
    "identical in egoa + the 4 Aleutian zones) plus an INPUT CORRECTION relative to #4: NCEI re-issued 2024-04-22..26 on 2024-06-05; the cache held "
    "the superseded version; the five days are replaced. theta90 byte-identical to #4 in all 12 zones (2024 is outside 1991-2020).")
br["why"] = ("Col. Raj directed (admin ...-20261001-10): rebuild with NCEI's re-issued 2024-04-22..26 files, withdraw those days from the outage list, "
    "and KEEP the producer's ice rule. Mini's Quantica found the re-issue; admin and the producer verified it.")
br["ice_outage_rule"] = br4["ice_outage_rule"].replace(
    "(171 global days with not one ice value on Earth: 1987-12-06..1988-01-10, 2016-01, 2016-04-18..06-30, 2017-01-07..02-28, 2020-08 (2 days), 2020-12 (3 days); and a regional outage 2024-04-22..26 over the Bering/Chukchi/Beaufort and northern-GOA zones)",
    "(171 global days with not one ice value on Earth, in 6 runs: 1987-12-06..1988-01-10, 2016-01 (3 days), 2016-04-18..06-30, 2017-01-07..02-28, 2020-08 (2 days), 2020-12 (3 days)). The 2024-04-22..26 'regional outage' of #4 is WITHDRAWN: those files were re-issued by NCEI and are now replaced. Outages are detected at the DAY level only (zero ice values on the globe); autumn zone-wide blank days (e.g. Sep-Oct 2025) are open water and are untouched")
br["ice_outage_rule"] = br["ice_outage_rule"].replace("On 176 days", "On 171 days")
br["definition_applied"]["series_span"] = "1982-01-01 to 2026-08-31"
c = br["pipeline"]["commits_of_record"]
c["input_replacement"] = {"commit": REPL, "src/mhw/fetch/ncei_daily.py": fsha(REPL, "src/mhw/fetch/ncei_daily.py"),
    "config/ice_outage_days.json": fsha(REPL, "config/ice_outage_days.json"),
    "what_ran": "mhw-splice-ncei --replace 2024-04-22 ... 2024-04-26 into the 12 oisst_<zone>_2024.nc files",
    "how_the_never_shrink_guard_allows_it": "replacement is a separate, explicit mode (--replace) for days named one by one; each must already be held; the time axis and day count must come out identical and every other day bit-identical, checked on the WRITTEN bytes before the atomic rename. Append mode is unchanged and still refuses any held day."}
c["ice_outage"]["config/ice_outage_days.json"] = fsha(REPL, "config/ice_outage_days.json")
c["ice_outage"]["note"] = c["ice_outage"]["note"] + " Config revised in 26e91bc: regional 2024-04 entry withdrawn (171 days)."
c["engine_and_inputs"]["what_ran"] = ("2026-10-01 -0500, MHW_FROZEN_INPUTS=1: mhw-build-climatology for all 12 zones (theta90 byte-identical to #4), then "
    "run_rebuild.sh 2026-08-31; no network fetch in any log")
c["engine_and_inputs"]["bytes_note"] = f"repo HEAD at packaging {HEAD[:7]}"
br["pipeline"]["code_changed_since_vintage_4"] = {"src/mhw/fetch/ncei_daily.py": "--replace mode + day_sha256 (+3 tests)", "config/ice_outage_days.json": "regional 2024-04 entry withdrawn"}
i = br["input"]
i.pop("vs_vintage_3", None)  # A3: stale #4 line, never inherit
i["zone_year_files"] = "540 zone-year files. Relative to vintage #3: the twelve oisst_<zone>_2024.nc files changed (2024-04-22..26 replaced by NCEI's re-issued files); the other 528 are byte-identical to #3."
i["vs_vintage_3_4"] = "12 zone-year files changed (oisst_<zone>_2024.nc: the five re-issued days replaced); every other input byte-identical"
i["reissue"] = {
  "days": "2024-04-22..26, re-issued by NCEI 2024-06-05 (Last-Modified 15:11:32-33 GMT); fetched 2026-10-01 (records/ncei_reissued_files_sha256.txt)",
  "magnitude": "max |dSST| per day 1.5-3.0 degC in nbs/sebs/ebs, 0.15-1.5 degC in the Gulf and Aleutians; the re-issued files carry the ice field (the superseded version had none)",
  "record": "records/reissue_replacement_record.json: per zone and day, old/new day-content sha256 and max |dSST|; old/new sha256 of each oisst_<zone>_2024.nc",
  "verification": "records/verify_replace.py (does not import the splice module): same time axis; every other 2024 day bit-identical to the pre-replacement file; each of the five bit-identical to NCEI on the cache grid and different from before. PASS, 12 files, 60 zone-days; trip-tested (FAIL when pointed at the unreplaced file).",
  "census": ("NCEI directory Last-Modified for all 16,314 days (records/ncei_directory_listing_20261001.csv): 13,968 written in the 2020-05 bulk v2.1 release; "
             "since then each final file ~15 days after its date (95% within 23). 100 files fall outside that pattern (pre-2020 days modified after the bulk, "
             "or > 30 days after their date); each was compared with the cache in all 12 zones, with 80 random control days "
             f"(records/reissue_census_compare.csv). STALE: {int(cen.stale.sum())} -- exactly 2024-04-22..26. The other 95 candidates and all 80 controls agree to "
             f"<= {cen[~cen.stale].max_abs_dsst.max():.1e} degC. Scope: a re-issue written inside the 2020-05 bulk or with a normal lag would not be flagged by the date screen; the 80 random controls are the evidence against that.")}
i["file_list"] = f"records/oisst_input_file_shas_{VID}.txt"
i.pop("aggregate_sha256_all_609", None)
i["aggregate_sha256_all_614"] = agg_all; i["aggregate_sha256_540_zone_year_files"] = agg540
i["ice_field_outages"]["regional_evidence"] = "WITHDRAWN in #5: 2024-04-22..26 were re-issued files, not an outage"
br["caveats"]["ice_outage_days"] = "On the 171 outage days ice status is inferred (interpolated; open above 2 degC), not observed. Back-test: >= 97% of ice cells caught pooled; sebs 84-90% (sparse ice edge)."
br["caveats"]["bering_jan_2017"] = "nbs January 2017 (0.250 vs <= 0.094 in other Januaries) is a real event observed on both sides of the outage (0.44-0.45 on Jan 3-6, continuing the record Dec 2016); within the outage the TIMING of its decay comes from interpolated ice, not observation."
v = json.load(open(ST / "records/theta90_undefined_mechanism.json"))
br["theta90_undefined"] = {
  "ruling": "Col. Raj (admin ...-09): fixed-mask denominator, NO fallback threshold -- a cell with no theta90 for a day of year is invalid that day, contributes no heatwave area, and stays in the denominator.",
  "mechanism": "some cells' theta90 for a day of year was defined ONLY by outage-day frozen-water samples; with those masked it is undefined, so the same calendar day in other years cannot be scored there.",
  "counts_unchanged_from_vintage_4": "theta90 is byte-identical to #4, so the undefined cell-DOYs are unchanged: " + ", ".join(f"{z} {v[z]['theta90_cell_doys_became_undefined']:,}" for z in v),
  "file": "records/theta90_undefined_mechanism.json"}
br["valid_cell_drops_vs_vintage_3_by_channel"] = {
  "explanation": "n_cells_valid drops against #3 come through three separate channels, split here as admin ...-09 asked: (1) the ice-outage rule on the 171 outage days; (2) the re-issued 2024-04-22..26 inputs, whose real ice field now masks ice-covered cells; (3) theta90 becoming undefined, on all other days. Channel 3 is 100% explained by undefined theta90 and equals the #4 addendum counts exactly.",
  "state_grid_cell_days_[lost, of_which_theta90_undefined]": chan, "file": "records/valid_drop_channels_v5_vs_v3.json"}
area = diff[diff.column == "area_frac"]
br.pop("change_vs_vintage_3", None)
br["change_vs_vintage_4"] = {
  "tolerance": "ZERO", "daily_table": "records/diff_daily_vs_vintage4_20261001b.csv (with days_from_2024_04_22_26)",
  "by_zone": {z: {"values": int((diff.zone == z).sum()), "days": int(diff[diff.zone == z].changed_date.nunique()),
                  "max_days_from_the_five": int(diff[diff.zone == z].days_from_2024_04_22_26.max()) if (diff.zone == z).any() else 0} for z in Z},
  "summary": (f"{len(diff)} values, all within {int(diff.days_from_2024_04_22_26.max())} days of 2024-04-22..26 (egoa/goa run 2024-04-06..05-08); "
              f"area_frac {len(area)} values ({int((area.days_from_2024_04_22_26==0).sum())} on the five days), max |delta| {area.delta.abs().max():.4f}. "
              "chukchi, beaufort, wgoa, ai_east: no product change. Nothing else in the record moved.")}
br["verification_by_producer"] = {"theta90_equal_to_vintage_4": "all 12 zones", "theta90_vs_vintage_3": br4["verification_by_producer"]["theta90_changed_zones"],
  "no_input_signature": "0 rows with area_frac > 0 and Ibar == 0", "x_to_A_rule_check": "in the full intake"}
br["licence"]["citation"] = br4["licence"]["citation"].replace(NOTSEALED, VID)
br["licence"]["licence_file"] = "LICENSE-data-CC-BY-4.0.txt (identical to #3's except the version id and one added line listing this vintage; #4 is not listed, never released)"
(ST / f"records/build_record_{VID}.json").write_text(json.dumps(br, indent=2) + "\n")

vm = copy.deepcopy(vm4)
vm["vintage_id"] = VID; vm["supersedes"] = f"{PREV} (snap-{PREV} stays registered and immutable; {NOTSEALED} was never sealed)"
vm["reseal_class"] = br["reseal_class"]
vm["code_commits"]["input_replacement"] = REPL
vm["identity_keys"]["theta90_sha256"] = {z: k5[z]["theta90"] for z in Z}
vm["identity_keys"]["x_sha256"] = {z: k5[z]["x"] for z in Z}
vm["identity_keys"]["A_sha256"] = {z: k5[z]["A"] for z in Z}
vm["identity_keys"]["theta90_vs_vintage_3"] = vm4["identity_keys"]["theta90_vs_vintage_3"]
vm["identity_keys"]["theta90_vs_vintage_4"] = "byte-identical in all 12 zones"
vm["previous_identity_keys_20261001"] = vm3["identity_keys"]
vm["unsealed_vintage_4_identity_keys_20261001b"] = vm4["identity_keys"]
vm["ice_outage_rule"] = br["ice_outage_rule"]
o = vm["oisst_provenance"]
o["product"] = o["product"].replace("the 8 repaired days and 2026-07-06..08-31", "the 8 repaired days, 2026-07-06..08-31, and the re-issued 2024-04-22..26")
o["oisst_input_files"] = 614; o["oisst_input_sha256"] = agg_all; o["oisst_input_sha256_540_zone_year_files"] = agg540
o["file_list"] = f"records/oisst_input_file_shas_{VID}.txt"
(S / "declared_vintage_v5.json").write_text(json.dumps(vm, indent=2) + "\n")
print("ok", REPL[:7], agg_all[:8])
