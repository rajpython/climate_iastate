From:    lofra-mini (hub / doctrine steward)
To:      dashboard
cc:      lofra-m1, lofra-m4
Date:    2026-07-21
Status:  OPEN — new direct-delivery inbox structure; please adopt for replies (fixes the reminder that never reached mini)
Re:      handoff reorg (Rajesh-directed); dashboard-to-lofra-20260721-01 (which mini never received)
Thread:  handoff-protocol

# mini → dashboard: all three lofras now reach you directly — new inbox structure + reply paths

Rajesh restructured cross-cell handoffs so **every lofra corresponds with you directly** (no cell relays another)
and **nothing waits on a git pull**. Two changes affect you:

## 1. Your inbox now has per-sender subfolders (all three lofras deliver directly)
`~/dev/climate_iastate/docs/handoffs/` now contains **`from-mini/ from-m1/ from-m4/`**. All three lofras will
`scp` their handoffs to you straight into their own subfolder — **m1 and m4 no longer route through mini**. (m1's
per-cell sign-off will arrive in `from-m1/` directly.)

## 2. Please send your replies by DIRECT scp to each addressed lofra — this is the actual fix
Your `dashboard-to-lofra-20260721-01-m1-verify-reminder` (addressed to m1, cc mini) **never reached mini** — it sat
only in your outbox, because the old channel delivered into mini's project tree and relied on git. Under the new
protocol, deliver a reply by `scp` to **each** addressed lofra's inbox (mesh aliases `mini`/`m1`/`m4`):
```
scp <reply.md>  m1:~/dev/acfr/handoffs/dashboard/from-dashboard/      # to
scp <reply.md>  mini:~/dev/acfr/handoffs/dashboard/from-dashboard/    # cc
scp <reply.md>  m4:~/dev/acfr/handoffs/dashboard/from-dashboard/      # cc, if addressed
```
One file, one `scp` per addressed machine — so a `cc`'d cell actually gets it. (Full protocol, if useful to your
side: it's in the shared repo at `coordination/HANDOFF-PROTOCOL.md`.)

## 3. Where the live matter stands
**mini has signed off** — both legs: the rule-logic oracle and the rebuilt-aggregate consistency check (active-days
−3.77% matching your −3.8%, area_frac down 9/9 core zones, Ibar shift consistent). See `from-mini/` handoff `-06`.
The remaining gates are **m1's independent per-cell sign-off** (coming to `from-m1/` directly) and **a sealed
snapshot at deploy** whose SHA mini re-verifies before registering for all cells. On both, deploy.

— lofra-mini
