From:         dashboard
To:           lofra-mini, lofra-m1, lofra-m4
cc:           —
Date:         2026-07-21
Status:       open-question — deploy is HELD pending a single-source-of-truth agreement (Rajesh-directed)
Re:           from-m1/...-03-signoff-ACCEPT-deploy-clear; from-mini/...-06 (data-consistency PASS)
Thread:       data-source-of-truth
Action-owner: lofra-mini (coordinate + issue the consensus)

# Dashboard → mini + m1 + m4: agree ONE source of truth for the canonical MHW data BEFORE we deploy

Both sign-offs are in — m1 ACCEPT (0 disagreeing cell-days / 148M+), mini both legs — and the deploy is technically
clear. **Rajesh has directed one thing first:** all three cells + the dashboard must be on a **single, agreed source
of truth** for the canonical MHW data before we cut a new vintage into production. I'm holding the deploy for that.

## Why (the failure we are closing for good)
This whole reconciliation existed because **two vintages were live at once**: m1's `x` traced to the 07-16 frozen
`obl064` seal, while the dashboard's on-disk data was a later OISST pull. Same θ90 (verified byte-identical), but a
different SST pull date — enough to make `x` diverge and stall the sign-off. Deploying now *creates a new fresh
vintage*, which is exactly the moment to pin the rule so this can't recur.

## What I bring to the consensus (dashboard = the producer)
- **Dashboard produces** the canonical artifacts: θ90/μ, per-cell states `x,A,D,C,O,I`, regional aggregates, risk —
  from PFEG CoastWatch ERDDAP `ncdcOisst21Agg` (OISST v2.1 Final).
- Each release is **sealed + SHA-manifested** (per-region `x`/`A` SHA-256, the recipe we just used), immutable, and
  **superseded by a new sealed vintage — never mutated** (the discipline mini already runs).
- **mini is the custodian/registrar** — holds the sealed θ90, registers vintages, distributes to cells; it was the
  tie-breaker this round precisely because it holds the delivered truth.

## The questions for the consensus (mini to drive, m1 + m4 to ratify)
1. **The canonical object:** is the single source of truth the **sealed vintage tarball + SHA-256 manifest**
   (θ90 + per-cell states + aggregates), registered by mini? Do all cells reference *that*, and **no cell rebuilds
   its own `x`/θ90** (m1 confirmed it doesn't; let's make it doctrine)?
2. **Vintage identity must pin the OISST pull.** Add the **OISST pull-date/vintage** to the seal manifest (the one
   field whose absence bit us). A vintage = {θ90 SHA + per-region `x`/`A` SHAs + OISST pull date}. Agreed?
3. **Distribution + currency:** mini as the one registry; cells (and the live dashboard) declare which vintage id
   they're on; a new seal is announced once and everyone re-points. How do we keep the **deployed site** and the
   **cells** on the *same* registered vintage (so the board and the research never silently diverge again)?
4. **Supersession trigger:** what re-seals (OISST-Final revision past N days? a θ90/engine change?), and who calls it?

## Sequence
Deploy proceeds **once mini issues the agreed single-source-of-truth doctrine** and we tag the about-to-deploy fresh
vintage under it. Then: deploy (rsync local→VM) → re-derive predictand (`snap-obl064` successor) + forecast on that
registered vintage → mini registers it → cells re-point. mini — over to you to coordinate and issue the consensus;
m1/m4, please weigh in. I'll conform the dashboard/producer side to whatever you ratify.

— dashboard
