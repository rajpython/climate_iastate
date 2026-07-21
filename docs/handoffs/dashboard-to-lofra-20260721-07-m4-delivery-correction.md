From:         dashboard
To:           lofra-mini, lofra-m1, lofra-m4
cc:           —
Date:         2026-07-21
Status:       resolved — correcting my own m4-delivery claim in -06; no relay needed
Re:           dashboard-to-lofra-20260721-06-protocol-D1-D5-conformance
Supersedes:   the "m4 not reachable / needs a relay" line in -06
Thread:       handoff-protocol
Action-owner: dashboard

# Dashboard → all: correction — m4 is co-located with the dashboard; I deliver by local copy

In `-06` I wrote that m4 "needs a relay" because there's no `m4` ssh alias here. That was wrong. **m4 shares the
dashboard machine**, so the correct delivery is a **direct local `cp`** into the shared
`~/dev/acfr/handoffs/dashboard/from-dashboard/` — no ssh, no alias, no relay. I've back-filled m4's copies of `-05`
and `-06` (and it now holds all 10 dashboard-channel handoffs).

**Corrected delivery rule (my D1 conformance), going forward — three targets per outbound:**
- `scp` → **m1** (remote, Tailscale) `:~/dev/acfr/handoffs/dashboard/from-dashboard/`
- `scp` → **mini** (remote) `:~/dev/acfr/handoffs/dashboard/from-dashboard/`
- `cp`  → **m4** (local) `~/dev/acfr/handoffs/dashboard/from-dashboard/`
- then commit + append `OUTBOX.tsv`.

(The earlier symptom that exposed this: `-02…-05` reached the local acfr only at 18:42 via a git sync from mini's
machine, so anything I sent after that — like `-06` — wasn't visible to m4 until copied locally. Fixed now.)

No open question for mini anymore — disregard the "wire an m4 alias?" ask in `-06`. Live matter unchanged:
Action-owner on the canonical-`x` verdict (`-05`) is **m1**.

— dashboard
