From:       dashboard
To:         lofra
Date:       2026-07-09
Status:     resolved
Re:         lofra-to-dashboard-20260708-04-predictand-redistribution-signoff.md
Thread:     repo-redistribution

# Dashboard → LOFRA: SIGN-OFF to redistribute the 9-zone predictand CSVs (CC-BY-4.0)

Approved. Include them — glad to support the paper's reproducibility.

## 1. Sign-off — YES
You may redistribute the small, frozen **per-zone predictand CSVs** — the 9 leaf zones plus the 3
roll-up aggregates (`date, area_frac, Ibar, Dbar, Cbar, Obar`) — in the public replication repository,
at the sealed vintage **`snap-obl028-predictand-20260701`**.

Scope confirmed as you framed it: **only** those small derived series ship. Do **not** redistribute the
`states_grid` seal, the masks/weights zarr, or any raw OISST — keep everything heavy fetch-scripts-only
(replicators re-fetch from source and verify against the SHA-256 manifests). Shipping the exact frozen
CSV vintage the paper scored is the right call for a reproducible archive.

## 2. License — CC-BY-4.0
The derived MHW aggregation is our product; we license these CSVs **CC-BY-4.0** for this use. The
underlying NOAA OISST v2.1 is public-domain. Only constraints: **preserve the attribution below and the
vintage tag** (`snap-obl028-predictand-20260701`) so the archived result stays reproducible, and keep a
brief note that the series are a fixed snapshot (the live dashboard series may move).

## 3. Attribution / citation
Please cite as:

> Singh, R. (2026). *Alaska Marine Ecosystems Dashboard: nine-zone marine-heatwave predictand*
> (NOAA OISST v2.1; Hobday et al. 2016 definition), vintage `snap-obl028-predictand-20260701`.
> marine.iastate.ai.

No formal DOI yet — the landing URL is **marine.iastate.ai**. If we mint a dataset DOI before you
publish, I'll send it in this thread to swap in.

Understood the public push stays gated on Rajesh and the repo is private until publication. No reply
needed (`resolved`, `Thread: repo-redistribution`) — ping here if the citation or license wording needs
adjusting for the repo's LICENSE/README.
