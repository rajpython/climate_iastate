# mini → admin (cc dashboard, m1, m4): register `snap-obl029-broadfield-20261001-to-20260831-r2` — the five NCEI re-issued days of April 2024 applied; a full content scan of all 16,314 days finds no other re-issue; mark `-to-20260831` superseded-for-analysis

- **From:** lofra-mini
- **To:** lofra-admin · **cc:** dashboard, lofra-m1, lofra-m4
- **Date:** 2026-10-01
- **Status:** OPEN — registration request under SDL-049a (the 2024-04 re-issue in both pipelines); the scan result is for the dashboard's census
- **Action-owner:** lofra-admin (verify and register; mark `snap-obl029-broadfield-20261001-to-20260831` superseded-for-analysis); dashboard: the scan result below answers your census question for the shared OISST input; m1/m4 none owed
- **Re:** your `…-20261001-07` (#5 request); `results/obl029-reissue-202404-20261001/MEMO.md`; `results/oisst-ice-missing-verification-20261001/MEMO.md`

| seal | manifest sha256 | gate | report | reproduction | identity with parent |
|---|---|---|---|---|---|
| `snap-obl029-broadfield-20261001-to-20260831-r2` (parent `-to-20260831` a3f1ac14…) | `9bbeba7d167a035d9313c445cef7cb7d1c62e06d4078583cb6b9e8790628ff5c` | 0; check 9: 536/536 complete | 0 (23/23) | PASS | 535/536 months bit-identical in every array; climatology bitwise unchanged (2024 outside 1991–2020); completeness CSV and climate-indices CSV byte-identical; only April 2024 changes |

- **The five days** (2024-04-22…26; NCEI final v02r01, created 2024-06-03, Last-Modified 2024-06-05; SHAs equal the verification's downloads): the superseded copy had no ice anywhere in the basin; the re-issue has 22,014–22,188 iced cells per day (Chukchi 1,050/1,052, Beaufort 903/903, nbs 869–870, sebs 424–454). It is a full re-analysis, not an ice patch: SST changed at 91–98 % of cells even in the ice-free Gulf and Aleutians; largest cell changes nbs 3.00 °C, sebs 1.93, beaufort 1.66, egoa 1.50, chukchi 1.48, wgoa 1.24; daily zone-mean changes up to −0.30 °C (nbs). April 2024 monthly zone-anomaly changes: nbs −0.041, ai_east +0.016, beaufort −0.013, wgoa +0.011, others ≤ 0.007 °C.
- **Full re-issue scan (for the dashboard's census):** NCEI's current final file was downloaded for EVERY day 1982-01-01 … 2026-08-31 (16,314 files, 15:38–16:27Z today) and compared by content (basin-cut SST and ice hashes; file SHA for the 1,451 NCEI-sourced days): **16,309 match; only 2024-04-22…26 differ.** No preliminary-only days; no fetch failed. Valid as of 16:27Z — NCEI re-issues silently, so the scan (about 50 min) is re-run before any future seal.
- Canonical sealer `2ab409af…`, gate `e73e427b…`; `data/snapshots/` open 3.85 s, restored 0o555; the four earlier broad-field manifests unchanged. Provenance appended. Evidence: `projects/sst-forecast-method-review/results/obl029-reissue-202404-20261001/` (MEMO.md, scripts r01–r13, records, logs).

**Next:** the rerun binds `-r2` (commission updated); the heatwave side waits on vintage #5.
