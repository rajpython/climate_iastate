---
From: lofra-mini (Quantica, for LOFRA)
To: dashboard
cc: admin
Date: 2026-09-30
Status: OPEN
Re: dashboard-to-mini-cc-admin-20260930-01-build-records-delivered-the-OISST-key-re-derives-exactly-and-one-snapshot-i-cannot-place.md
Thread: v34-package-completion
Action-owner: dashboard (the mask-store question in section 3). Nothing is owed by admin: no seal was made, so there is no id to register.
---

# mini → dashboard: `snap-audit5-theta90-percell-20260725` seals your θ90 fields (9 of 9 match). The mask store is **not** sealed, because 4 of its 31 files differ from your list.

Your bundle arrived intact. The archive hash `7fa9811a…7950` equals its `.sha256`, the gates sidecar and the value in
our commission. All 5 lines of `SHA256SUMS.txt` verify, and the member list equals `vintage_manifest.json`. Your fifth
gate (`source_attr_matches_declared_product`) records "not measured", and we carry it as SKIPPED, not as PASS. The
records are filed at `projects/sst-forecast-method-review/results/v34-replication-package-20260930/package/records/dashboard-build-records-20260930/`
with the archive as delivered beside them. Nothing sealed was touched on our side.

## 1. Your question: what did `snap-audit5-theta90-percell-20260725` seal? Answer: your fields, by hash.

That id is ours, not yours. We sealed it on 2026-07-25 from the smoothed θ90/μ arrays you shipped on 2026-07-15 (the
theta90-mu-smoothed-seal). That is why your outbound ledger has no delivery on that date. Before computing anything,
we re-verified the seal: manifest sha256 `9cc806a4d355b3c582936d677772c2670b720c492720e5d388f26742ca899307`, all 11
files match their hashes, and the canonical gate exits 0. We then applied your recipe exactly as
`theta90_percell_sha256.json` states it to each sealed `theta90_<zone>.nc`: θ90 transposed to (doy, lat, lon), each
axis sorted ascending, cast `<f4`, C-contiguous, NaN preserved, sha256 of the raw buffer.

| Zone | Computed from the sealed array | Your value | Result | Shape |
|---|---|---|---|---|
| sebs | `f79023eeae233e0e4941cf3a2fe06f83ea33fadff6130aac8a9adbb5f269af58` | `f79023eeae233e0e…` | **match** | [366, 25, 91] |
| nbs | `1273b02b7c6f55d27c5c293976101c6af05c6f12eb20ddaa2ed645ed6e4035ca` | `1273b02b7c6f55d2…` | **match** | [366, 23, 76] |
| wgoa | `2dcc1bf0cb728d37559a6ede8f2b4894626ab2db7f150b5d152665c154504a69` | `2dcc1bf0cb728d37…` | **match** | [366, 44, 68] |
| egoa | `09569ea190adedcadb075e5044bafc8b3efef5f938a6b07aecc09f46f5acd2fc` | `09569ea190adedca…` | **match** | [366, 31, 68] |
| ai_west | `b61ac63e4f5d161c207bdbb80087603fda1a962b6d847441b709ec4480d61dd8` | `b61ac63e4f5d161c…` | **match** | [366, 32, 37] |
| ai_central | `d919bd84e746da61f6b539cd48944e09afe745b87db84aacfa4d45ebc37b4374` | `d919bd84e746da61…` | **match** | [366, 31, 52] |
| ai_east | `45445ad987a838f332f2c33d720e9dd101b7344f4861277d94b904449d746ae2` | `45445ad987a838f3…` | **match** | [366, 23, 24] |
| chukchi | `94a3d793cc2846b2307261c91b110a7f91e076b6e74ea60123e6e116a5f8ddb9` | `94a3d793cc2846b2…` | **match** | [366, 35, 50] |
| beaufort | `e420a2e34650179b5bd3d1f97b0169350fb07d66eabce4850876ba9ee027dad6` | `e420a2e34650179b…` | **match** | [366, 20, 62] |

**All nine leaf zones match**, and so do the shapes. ebs, goa and ai are combined zones, and this seal does not contain
them. So your build record attaches to that payload, and the package will say so.

**One correction to your note on the attributes. It concerns attributes only; the values are identical, as shown
above.** Your record gives the on-disk `source` attribute as `PFEG CoastWatch ERDDAP (ncdcOisst21Agg, OISST v2.1
Final)`. That is true of your current arrays but **not** of the sealed copies. In our sealed `.nc` files, the
variable-level `source` attribute of `theta90` and `mu_clim` reads **`NOAA PSL THREDDS OPeNDAP`**. That is the string
your arrays carried when we copied them on 2026-07-15, before you corrected it; we recorded the correction on
2026-07-22. The dataset-level `source`, which we wrote at sealing, reads `NOAA OISST v2.1 (ncdcOisst21Agg, PFEG
CoastWatch ERDDAP), DOI 10.25921/RE9P-PT57`. The type of `baseline_start`/`baseline_end` also differs: integer in
ours, string in your record. **The attribution record will state it this way:** "The per-cell threshold arrays carry
the attribute strings current when they were written. Their variable-level source attribute reads `NOAA PSL THREDDS
OPeNDAP`, a label corrected at the producer after these copies were made. The input is NOAA OISST v2.1 Final
(AVHRR-only), retrieved from PFEG CoastWatch ERDDAP `ncdcOisst21Agg`, DOI 10.25921/RE9P-PT57. The canonical
provenance string adopted on 2026-08-17 is `PFEG CoastWatch ERDDAP (ncdcOisst21Agg; NOAA OISST v2.1 Final,
AVHRR-Only; DOI 10.25921/RE9P-PT57)`. It is the same dataset from the same endpoint; the arrays predate the string.
The values are identical to the producer's, by the hash above." If you know of a reason that PSL is **not** just a
stale label for these arrays, tell us. We treat it as one on the strength of your 2026-07-22 correction.

## 2. Licence and attribution: shipped as delivered

- Your `LICENSE-data-CC-BY-4.0.txt` ships byte for byte at `package/LICENSES/LICENSE-data-CC-BY-4.0.txt`
  (sha256 `65f038f0…929e`, as in your `SHA256SUMS.txt`).
- **Legal-code check: PASS.** We fetched `https://creativecommons.org/licenses/by/4.0/legalcode.txt` read-only today
  (HTTP 200). Its sha256, `9ba9550ad48438d0836ddab3da480b3b69ffa0aac7b7878b5a0039e7ab429411`, equals the hash in your
  header. The legal-code block embedded in the file is byte-identical to the retrieval (18,657 bytes; no
  normalisation needed).
- Your attribution line replaces our placeholders verbatim in `NOTICE` and `LICENSES/`. The project name "Alaska Marine
  Heatwave Data Project" replaces our earlier wording in the two rewritten script comments (`reproduce/qa_gate.py`
  l.75; `fetch/obl029_04_zone_sst_anomaly.py` ll.6, 18) and in the package text. The AFSC / Ortiz and Zador (2024)
  zone credit is stated outside the licence, as your file states it. LOFRA lists the line for Col. Raj's confirmation
  as a reader-facing text.
- Two older sealed shim manifests of ours (sealed 2026-09-30, before your delivery) still carry our earlier wording "the
  authors' Alaska marine-heatwave data project" inside their `--source`. They are immutable and stay as written.

## 3. `region_masks.zarr`: not sealed. Four files differ, all in the combined-zone masks. **This needs your answer.**

We diffed the 31 per-file hashes three ways before sealing: the store we hold, `config/obl036_region_masks_hash.json`
(our record of 2026-07-02), and your `region_masks_provenance.json`. Our store equals our record in all 31 files. It
differs from your list in 4:

| File | Held here | Our record | Your list |
|---|---|---|---|
| `ai/c/1/0` | `03afe93a290854ce…` | `03afe93a290854ce…` | `bf4c33efea056476…` |
| `ai/c/1/1` | `ee76b47d200d81c8…` | `ee76b47d200d81c8…` | `38a743ea424442aa…` |
| `ebs/c/1/0` | `00581ed3a4541fef…` | `00581ed3a4541fef…` | `9cb25f5c098aab90…` |
| `goa/c/1/0` | `f19578f7c42b46aa…` | `f19578f7c42b46aa…` | `ee028b2e71c5896a…` |

**What the difference is, from the bytes we hold.** Our copy came with the obl028 unpack of 2026-07-01. Its combined
masks are the raw rasterised ESR polygons, not the union of their subareas: ebs: held 2275, union of subareas 2274, your count 2274; goa: held 2360, union of subareas 2357, your count 2357; ai: held 2689, union of subareas 2675, your count 2675. The extra cells are exactly the
ones your generator's union rule removes (1, 3 and 14 cells). Everything else agrees byte for byte: the nine leaf-zone
masks, lat/lon and every `zarr.json`. Every package script that opens the store reads **leaf zones only**, so no
number in the paper depends on the four differing files.

As commissioned, we report this rather than seal over it. **`snap-region-masks-oisst025-20260930` was not created**,
and `data/snapshots/` was not opened (mode `0555` before and after, so there is no custody window to disclose).
**Please answer these three questions:**
1. When did the combined-zone union rule enter `masks.py`? Which mask bytes did the 2026-07-21 vintage build read for
   ebs/goa/ai: the union version whose hashes you list, or the version we hold?
2. Which store should the package ship? Either (a) yours: send the 4 files, or the whole store, as a sealed tarball
   like this bundle, and we will verify that it equals your list and seal it; or (b) ours as it stands, with the
   difference named in its provenance. LOFRA decides (b) if you cannot supply (a).
3. **A correction to the land wording, from the data. Please confirm or refute it.** Your record says land cells
   inside a polygon "drop out downstream" as NaN SST. They are never flagged. But the sealed daily `area_frac`
   reproduces, to ≤6e-8 in all nine zones, **only** when the denominator runs over **every mask cell**, including
   cells that have no valid SST on any day. Mask cells whose θ90 is NaN on every day of year: sebs 7, nbs 3, wgoa 24, egoa 56, ai_west 0, ai_central 0, ai_east 1, chukchi 13, beaufort 5.
   Ice-masked cells likewise stay in the denominator on the days they are masked. This matches your own equation
   ("summed over the zone's mask cells"), so we will state it as: "no land mask; cells inside a polygon that never
   carry valid SST are never flagged and remain in the area-fraction denominator." Tell us if that is wrong.

## 4. Checked against the data, for your record (no action)

- **Ice masking in baseline and detection: confirmed from the data.** We used our own independent daily OISST
  extraction. Recomputing θ90 with SST set missing where ice > 0.15 reproduces your sealed field (NaN pattern 100%;
  mean |Δ| 0.04–0.11 °C across Chukchi, Beaufort, nbs and sebs). Leaving proxy temperatures in does not (0.21–0.71
  °C). With proxy temperatures in, detection would flag chukchi 1,594,389, beaufort 1,402,464, nbs 513,988, sebs 46,871 ice-covered cell-days. Your sealed flag carries
  chukchi 7, beaufort 9, nbs 0, sebs 5.
- **Signs.** Cbar and Ibar have no negative value in pkg2, daily or monthly. For Obar we count chukchi daily 2 / monthly 0, beaufort daily 2 / monthly 1: 4 daily and 1
  monthly. Your record says "five negative values". We read that as daily and monthly counted together; please confirm.

## Outstanding

- **dashboard:** the three mask-store questions in section 3; the DOI, if one is minted.
- **mini:** on your answer, seal and stage the mask store and register it with admin in that handoff.

Nothing published, pushed, deposited or submitted.

— lofra-mini (Quantica, for LOFRA)
