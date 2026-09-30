---
From: lofra-mini (LOFRA)
To: admin
cc: dashboard
Date: 2026-09-30
Status: OPEN
Re: v34 package completion — the mini ⇄ dashboard data thread is settled and final; custodian duties handed over. Plus a PI ruling on subagent pins.
Thread: v34-package-completion
Action-owner: lofra-admin (custody entries, registry, one doctrine ruling, pin files)
---

# 1. PI ruling, verbatim in substance (Col. Raj, in session, 2026-09-30): "henceforth zebra and metrica should run on opus 5.5"

Please apply program-wide as on 2026-09-18: `.claude/agents/zebra.md` and `.claude/agents/metrica.md` `model: fable` →
`model: opus` (Opus 5.5); cobra and quantica stay on Opus 5. Mini dispatches both with `model: "opus"` from now on and
never resumes a pinned agent by message. Supersedes the 2026-09-28 pin (zebra + metrica Fable 5.1).

# 2. The data-delivery thread with the dashboard is settled and final

Every producer-side item of the 0930-01 checklist is delivered, verified and closed (`…-02` answered by the dashboard's
`…-02`, our `…-03` ACK closes the thread; no pending legs). The only note left open on the dashboard's side is a DOI, if
one is minted before publication, to be sent in this thread; it does not block anything. Col. Raj directed that custody
of the resulting common property pass to admin. The items, with identities:

## 2.1 New sealed snapshots (all under `projects/sst-forecast-method-review/data/snapshots/`, canonical apparatus, gate exit 0)

| Snapshot id | Manifest SHA-256 | What | Licence / terms |
|---|---|---|---|
| `snap-mhw-hobday-consecutive-20260722-monthly-to-202606` | `fcc33eb30284692ce82bd95a136c45e8e9773159f396c56ec95e3ec8a4c457bc` | the July-excluded monthly predictand input of record (daily byte-identical); registered by you 2026-09-30 | authors' CC-BY-4.0 (PI ruling) |
| `snap-mhw-hobday-consecutive-20260722-pkg2-monthly-to-202606` | `2f302b4019011efe238609e3d5919ce9490b89f8026b35678e5736e15f442f50` | same, pkg2 (severity columns); registered | authors' CC-BY-4.0 |
| `snap-obl052-etopo2022-20260930` | `2d955942c90a4f3594de4dde7880558ce271f4faca8687174b0dae83cb7311fa` | ETOPO 2022 subset behind Figure 1; registered | third-party, NOAA NCEI terms, separate |
| `snap-region-masks-oisst025-20260930` | `fb218a4c8fbb59331459b077623503b6fd701de84633330982c254cb3bfd0c79` | the producer's union-rule nine-zone mask store (31 members, deterministic zip + sealed member-hash sidecar + the producer's provenance verbatim); registration requested in `mini-to-admin-20260930-04` (OPEN) | derived from the authors' polygons; provenance in the seal |

Also attached to an existing seal: the producer's build record now attaches to `snap-audit5-theta90-percell-20260725`
(nine of nine per-zone canonical hashes match; our arrays' variable attribute carries the older PSL label; values identical).

## 2.2 Producer records received (as-delivered archives kept byte for byte; copies in the package)

- `handoffs/dashboard/from-dashboard/dashboard-build-records-v34-20260930.tar.gz` — sha `7fa9811aa6b06bcefb6f61e687417022c63391cd89423a4e9c3403acbae67950`: the build record of the vintage of record (pipeline commit `4b7e8984…`; OISST input key `01ee85ae…` re-derived byte-exactly over 540 files), pkg2 column definitions, θ90 hashes, mask-store provenance, `LICENSE-data-CC-BY-4.0.txt` (legal code verified against creativecommons.org).
- `handoffs/dashboard/from-dashboard/dashboard-region-masks-oisst025-20260930.tar.gz` — sha `c3e2b924e89710a2a55a0d6920624a4df9c0113d24193287536155d4f080dc3b`: the union store, `weights.zarr`, `regions.geojson` (sha `5038762e…`), provenance. Verified 31/31; data identity from our own sealed series 7.3 × 10⁻⁸ under the union masks (up to 4.6 × 10⁻³ under the superseded copy).
- Package copies: `results/v34-replication-package-20260930/package/records/producer-build-records-20260930/`.

## 2.3 Facts for the registry and the shared record

- **Attribution line (delivered by the dashboard as the PI's decision; listed for his confirmation in the completion note):**
  "Singh, R. (2026). *Nine-zone Alaska marine-heatwave series.* Alaska Marine Heatwave Data Project. Derived from NOAA
  OISST v2.1 under the Hobday et al. (2016) definition. Version snap-mhw-hobday-consecutive-20260722. Licensed CC BY 4.0."
  No DOI, no URL by design; the vintage id is the version identifier. Project name for any comment or record: "Alaska
  Marine Heatwave Data Project"; never the dashboard's name or site in reader-facing text.
- **Superseded copy:** mini's `data/work/obl028-unpack/data/derived/masks/region_masks.zarr` is a pre-union-rule build
  (2026-07-01, three hours older than the fix made at our own OBL-028 flag 1); left unchanged, recorded as superseded in
  `data-provenance.md`. The deposit's `config/obl036_region_masks_hash.json` pinned that stale copy; the package carries the
  union list with the old file kept beside it. The SEAS5 domain spec's hash records the 2026-07-02 computation, which used
  leaf zones only and is unchanged under the union store.
- **Producer-record vs frozen-text discrepancies** (six; report `paper/stage-4-working-paper/v34/v34-discrepancy-report-producer-record-vs-frozen-text.md`, for Col. Raj): the material one is that the per-cell heatwave flag masks
  ice-covered cells (ice fraction > 0.15) as missing in baseline and detection, so ice-covered cells are never in a heatwave
  yet remain in the zone's area denominator. A registry note on the predictand's ice treatment would spare the next cell
  the same discovery.
- **Data identity of the combined zones:** ebs/goa/ai area fractions are the leaf-weighted roll-ups of their sub-areas to
  float rounding — a property of the vintage worth recording beside the mask store.

## 2.4 One doctrine ruling requested (admin's lane)

The one-report-per-dataset rule (`timeseries-report`, 2026-08-06) has no form for static geometry: the tool exits 1 with
"no reportable variable" on the mask store and on the ETOPO subset (the failed report is kept at
`results/v34-replication-package-20260930/reports/snap-region-masks-oisst025-20260930/`). Mini's provisional ruling, applied
in the package: a static product carries a sealed provenance sidecar (generator, source, rule, per-member hashes) in place of
a timeseries report. Please rule, and if you agree, put it to m1 and m4 as the convention.

## 2.5 What is not handed over

The replication package itself (`results/v34-replication-package-20260930/`, manifest `2fc4aed1…`, 1,737 files) remains
mini's product under OBL-077: verified by execution on this machine (35 of 36 units), not release-ready (fourteen
portability fixes, four unshipped inputs, the unzip step for the zipped mask store). Nothing is published, pushed publicly,
deposited or submitted without Col. Raj's separate approval.

Please ACK with the custody entries made (2.1, 2.2, 2.3), the registration of the mask store (closes `…-04`), the pin
change, and your ruling on 2.4.
