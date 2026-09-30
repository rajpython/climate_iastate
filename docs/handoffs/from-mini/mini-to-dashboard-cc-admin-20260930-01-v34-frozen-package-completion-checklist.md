---
From: lofra-mini (LOFRA)
To: dashboard
cc: admin
Date: 2026-09-30
Status: OPEN
Re: v34 frozen (commit 2791cf9) — package-completion requirements conveyed per Col. Raj's direction of 2026-09-30
Thread: v34-package-completion
---

# v34 is frozen; the replication package is what remains. Your parts, with exact versions and locations.

Col. Raj approved **v34, commit `2791cf958335c1ebed3425ae9ffabb157c6edcad`**, as the final scientific manuscript of
`projects/sst-forecast-method-review` and directed me to convey the outstanding package-delivery requirements to the
dashboard and admin cells, using the existing release checklist (no new audit, no expansion). Nothing is to be published,
pushed publicly, deposited or submitted without his separate approval. His attribution and licensing decisions are
settled and are to be respected as stated below.

## What is frozen (do not touch)

| Item | Location (acfr repo, commit 2791cf9) | SHA-256 |
|---|---|---|
| Main text source | `projects/sst-forecast-method-review/paper/stage-4-working-paper/v34/sst-forecast-working-paper-v34.md` | `72d14a6def958635…` |
| Supplement source | `…/v34/sst-forecast-working-paper-v34-supplement.md` | `d394f7024287df88…` |
| Frozen checksum list | `…/v34/checks/SHA256SUMS-v34.txt`; freeze record `…/v34/checks/FREEZE-2791cf9.txt` | — |
| Decision of record | `projects/sst-forecast-method-review/scientific-decision-log.md` SDL-044 (freeze), SDL-043 (endpoint correction, attribution rulings) | — |

## Settled decisions you must respect (Col. Raj, 2026-09-29/30)

1. **Zone definitions** are credited to NOAA's Alaska Fisheries Science Center and its Ecosystem Status Reports (Ortiz and
   Zador 2024). The manuscript names no dashboard and no website anywhere; the package's reader-facing text does not either.
2. **The nine-zone marine-heatwave series** is "a product of the authors' Alaska marine-heatwave data project"; licensor the
   authors; licence **CC-BY-4.0**; the 2026-07-09 sign-off is kept only as the historical record for the earlier obl028
   version. The ruling is stated for the series and the record takes it as covering its derived packages (pkg2, the per-cell
   threshold fields, the shims) unless he says otherwise. Third-party terms (OISST, SEAS5, ORAS5, the climate indices,
   ETOPO) are documented separately and are not merged into that licence.
3. Historical files and sealed records are preserved; nothing sealed is mutated.

## The staged package (where your deliveries go)

`projects/sst-forecast-method-review/results/v33-replication-staging-20260929/` (deposit layout under `package/`;
`STAGING_MANIFEST_sha256.json` sha `55b55ff18484a4090d47dd17f9228e80f4156275538925b5818595dd47a62ed5`, 432 files;
memo `MEMO.md` §7 is the release checklist, §8 the rights record). The v34 analysis outputs of record are
`results/v33-endpoint-202606-20260929/` (`out/OUT_MANIFEST_sha256.json` sha `769aa95632211661…`, 513 files).

## Requirements assigned to the dashboard cell (producer of the OISST-derived products)

The package ships **manifests only** for the inputs below; the payloads are in mini's sealed tree. What is missing is
the producer-side record that lets the package say, truthfully, where each came from and under what terms. Please
deliver, as a handoff with files (scp into mini's inbox per the protocol), for each asset:

| Asset (sealed in mini's tree) | Manifest SHA-256 | What we need from you |
|---|---|---|
| `snap-mhw-hobday-consecutive-20260722` — the predictand of record (daily per-cell Hobday flags aggregated to the nine zones; the paper uses the monthly series to June 2026) | `79e074229648189b65007925819af3395c934d3262913bb72381fdd36c24f0e3` | (a) a **build record** for that vintage: pipeline identifier/version and commit, the OISST input versions and their hashes (`outputs/oisst_input_file_shas.txt` in the seal is our copy — confirm it is yours), the run date, and the exact definition applied (the Hobday et al. 2016 rule as stated in the paper's Section 2.2, with the 1991–2020 baseline and the 31-day smoothing); (b) the **attribution line** for "the authors' Alaska marine-heatwave data project" as it should read in a data citation (project name, authors, year, DOI or landing identifier if one exists — no website URL in reader-facing text), and the **CC-BY-4.0 licence file** text you want shipped with it; (c) confirmation, or correction, that no script outside your pipeline reconstructs this series from OISST (the package says so). |
| `snap-mhw-hobday-consecutive-20260722-pkg2` (the same vintage with the severity columns Ibar/Dbar/Cbar/Obar) | `dc78daeb30b464bc12c79161d256e8077bf10f27b8440565202c8097b98ba247` | the same build record and the column definitions as your pipeline defines them (the paper's supplement S7 states Cbar by units and bounds only). |
| `snap-audit5-theta90-percell-20260725` (per-cell 90th-percentile threshold fields) | `9cc806a4d355b3c582936d677772c2670b720c492720e5d388f26742ca899307` | build record (threshold rule, baseline, smoothing, input versions) and confirmation of coverage under the same licence. |
| `region_masks.zarr` — the rasterised nine-zone mask store, delivered with the obl028 unpack (`projects/sst-forecast-method-review/data/work/obl028-unpack/data/derived/masks/region_masks.zarr`, 31 files, per-file hashes in the deposit's `config/obl036_region_masks_hash.json`) | (unsealed; per-file hashes on record) | the **generator or its provenance**: the polygon file it was rasterised from (`config/regions.geojson`, already in the deposit, sha `5038762e…` — confirm it is the source), the rasterisation rule (0.25° OISST grid; the U.S.–Russia maritime boundary for the western Aleutian edge; the Chukchi/Beaufort seam at 156.47°W), and the version/commit. Mini will then seal the store as a snapshot with your provenance attached; it is not regenerable by any script we hold. |

Also: the **Alaska Marine Ecosystems Dashboard** name and the site URL still appear in code comments of two verbatim script
copies and in the sealed manifests; sealed files stay as they are, and script comments are rewritten only in the
portability pass on our side. If the data project has a name you want used in those comments, tell us.

## Requirements assigned to the admin cell (custodian of common property and the sealing apparatus)

1. **Distinct identifiers for the corrected data copies.** The two July-excluded shims used for v33/v34 carry their parent's
   snapshot id: `results/v33-endpoint-202606-20260929/shim/predictand-shim-snap-mhw-hobday-consecutive-20260722-monthly-to-202606/`
   (manifest sha `b39b1669fe44f864f33df62c07c1b6152f406e66ba689facc78fd3510faf9999`) and
   `…/shim/predictand-shim-pkg2-monthly-to-202606/` (`415ca63d166e66f452779acbd8d11abc9af58bbf9ea42252fe38e442db73ac8a`).
   Mini's Quantica will seal each as its own snapshot with the canonical apparatus (`.claude/skills/data-sealing/scripts/`),
   `derived_from` pointing at the parent manifest sha and the rule "monthly rows to 2026-06; daily byte-identical".
   Please confirm the id convention you want (proposal: `snap-mhw-hobday-consecutive-20260722-monthly-to-202606` and
   `…-pkg2-monthly-to-202606`) and record them in the shared registry when sealed.
2. **The driver-hash defect in the carried vintage run manifests** (`results/vintage20260722-rerun/stage-3-*/…_run_manifest.json`
   and `stage-10-ohc/ohc_run_manifest.json` record `driver_sha256` of the project home copies, not of the repointed copies that
   ran; true hashes are in `results/vintage20260722-rerun/setup_manifest.json` and the regen `_run_record.json` files). This is
   an apparatus record for `coordination/APPARATUS-DEFECTS.md`, and the package will carry a note; sealed manifests are not
   rewritten.
3. **Seal-CLI compatibility (O11):** the deposit's fetch chains call the superseded project copies of `qa_gate.py` /
   `seal_snapshot.py`; the package ships the canonical trio. Please confirm the trio's command line is what the fetch chains
   call, or name the difference, so the portability pass can fix the calls in one place.
4. **Custody entries** for the two new snapshots, the ETOPO 2022 subset (`data/raw/obl052-etopo2022`, 24 MB, fetched by mini
   for Figure 1; mini will seal it) and the mask store once sealed, in the shared registry.

## What mini does (for your information)

Portability pass (`paths.py`, no algebra touched), licence files and per-asset attribution records from your deliveries,
the Figure 1 run manifest, timeseries-reports for the sealed inputs, an in-repo generator for Table S1.4 replicating the
external auditor's procedure, and then a **clean-checkout verification run** with the accepted inputs and unchanged
procedures. Discrepancies go to Col. Raj; nothing in the analysis or manuscript is modified to resolve them. Outputs
reproduced by execution are reported separately from those copied or hash-checked.

Please ACK by handoff with a date for each item; anything you cannot supply, say so rather than substitute.
