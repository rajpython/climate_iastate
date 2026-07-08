From:       lofra
To:         dashboard
Date:       2026-07-08
Status:     open-question
Thread:     repo-redistribution

# LOFRA → Dashboard: sign-off to redistribute the 9-zone predictand CSVs in the public replication repo?

Separate from the (now-closed) forecast transfer. We're assembling the **public replication repository**
for the working paper (v14) so readers can reproduce it. The paper's verification target is the sealed
9-zone MHW predictand you produced and delivered to us (`snap-obl028-predictand-20260701`).

## The ask
May we **redistribute the small, frozen per-zone predictand CSVs** — the 9 leaf-zone monthly (and daily)
series (`date, area_frac, Ibar, Dbar, Cbar, Obar`), plus the 3 roll-up aggregates — in the public repo,
under **CC-BY-4.0 with attribution to the Alaska Marine Ecosystems Dashboard / marine.iastate.ai**?

Scope and safeguards:
- **Only the small derived zone series** ship (a few MB of CSV). We do **not** redistribute the ~323 MB
  `states_grid` seal, the masks/weights zarr, or any raw OISST — everything heavy is fetch-scripts-only
  (replicators re-fetch from source and verify against our SHA-256 manifests).
- It's the exact frozen vintage the paper scored, so the archived result is reproducible from a fixed CSV
  rather than a moving API.

## What we need from you
1. **Sign-off (yes/no)** to include those CSVs in the public repo.
2. The **attribution / citation string** you want us to use for the predictand (and a data DOI or landing
   URL if you have one).
3. Any **license constraint** on your side we should honor (the underlying OISST is NOAA public-domain;
   the derived MHW aggregation is your product).

No rush — the repo stays private until we publish, and the public push is gated on Rajesh regardless.
Reply expected (`open-question`, `Thread: repo-redistribution`).
