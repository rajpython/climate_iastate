# DELIVERY MANIFEST — forecast module v1.1.0 (delivery unit v1)

Generated (UTC): 2026-07-08T17:08:35.490937+00:00
Package: forecast-module-v1-20260708.tar.gz
Contents: Alaska MHW zone forecast module (frozen-coefficient operational paths), the validated model libraries, the broad-basin field ingestion chain, and the domain/mask specification.

Integrity: verify each file below against its SHA-256 after extraction. The coefficient manifest's internal `code_provenance` block additionally pins the SHA-256 of the exact code files the pinned coefficients were built and validated with; it must (and does) match the copies shipped here.

| File | Bytes | SHA-256 |
|---|---:|---|
| `forecast/README.md` | 11426 | `0c5dcdc41222b07e8b087684b31df7f412186f1fef9750330b3c0263821778bb` |
| `forecast/__init__.py` | 2254 | `d974c97f8bd6a5f37d909ce6075264b122d5a83a0cc0810958b3faace0ea4828` |
| `forecast/build_coefficient_manifest.py` | 18048 | `84259ab8a468dab05b0be1b85249cc535545e37e9fb148c6f8bf76179a449ee7` |
| `forecast/coefficient_manifest_v1.json` | 38669 | `dd326f417ea9e00bdd1a4dca5d8c3fd21e171158a4b89d75f4d93f134255c58d` |
| `forecast/coefficient_manifest_v1_frozen_basis.npz` | 8371769 | `45b9e2b6aa790dc85fce67dd9223d09e5f22e9f91d400397c336a7b92b39060b` |
| `forecast/core.py` | 18535 | `912907769c1993f958ee406077127e874c7cb64e3159e07afee1e981db61e7b0` |
| `forecast/frozen.py` | 17586 | `9624ce5c6fe143dd4df3547da1714d4b138b0cb167ee28a532d5348eb863e1ed` |
| `forecast/selftest_identity_check.py` | 15088 | `cb41c55dbe530e6f06fbf3d6d7382577ba2cb2b31c3514240a4e192e99ac795a` |
| `scripts/obl029_01_fetch_oisst_broadbasin.py` | 9088 | `816b094d48b187e77945322c94076ea015a222701b84b204e3e0c7e237a818dc` |
| `scripts/obl029_02_monthly_aggregate.py` | 12722 | `6afa0934e403afb8401df2f3d3f4fd30ff8d11a7ba1e478736640a10fffeabec` |
| `scripts/obl029_04_zone_sst_anomaly.py` | 8194 | `91dc8f442f8bb6fe75a1c30e55b1be772b2b5345a5707c4f5f375fd2c9b0dbb8` |
| `scripts/stage3_harness.py` | 30358 | `5d947b68fcb94163c2812f581b1eeb8ab5c4fb63aa1105fa9a1b36ea432695d9` |
| `scripts/stage3_lim.py` | 16889 | `767aa9d1678503b45619ae10b7451c069bc2f70ec3fb36a28246fd81199fe9e5` |
| `spec/obl036_domain_spec.json` | 5049 | `7d5bd6f102c788c7b8a3ded5c8dfc0e97b3caed2424d439ca91e48d1800ca774` |
| `spec/obl036_region_masks_hash.json` | 4410 | `6283f1f616c8181521f791dab9161a23b114c121fd91dd0e9bfd4f80d9ab8cd2` |

Files: 15  ·  Total bytes: 8580085

See `forecast/README.md` for the product definition, entry points, honest-labeling requirements, and the parameter-lifecycle contract.
