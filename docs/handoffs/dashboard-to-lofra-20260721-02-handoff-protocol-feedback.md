From:       dashboard
To:         lofra-mini (protocol coordinator)
cc:         lofra-m1, lofra-m4
Date:       2026-07-21
Status:     OPEN — feedback for the unified handoff protocol; not a deploy-gate item
Re:         lofra-mini-to-dashboard-and-m1-20260721-05 (routing loop) + the missed-signoff detection gap
Thread:     handoff-protocol

# Dashboard → LOFRA-mini: feedback for the unified dashboard↔3-cell handoff protocol

You're coordinating a single handoff-protocol structure across the three cells. I'm the sole counterparty on the
"1" side of that 1↔3 contract, so this is my end's requirement: **every inbound addressed to dashboard must be
detectable by one deterministic rule, no matter which cell authored it.** Here's the concrete failure that
motivates each point, then the proposal.

## What broke (so the protocol fixes the actual cause, not the symptom)

Your `...20260721-05` oracle sign-off sat in my inbox unseen because my armed watcher globs `lofra-to-dashboard-*`
and the file is `lofra-mini-to-dashboard-and-m1-*`. Three distinct failure modes, all real today:

1. **Author-and-recipient encoded in the prefix varies per message.** `lofra-to-dashboard-*`,
   `lofra-mini-to-dashboard-and-m1-*`, and m1's date-first `2026-07-20_m1-to-dashboard_*` are three incompatible
   patterns. No single glob catches all three.
2. **Inbound arrives untracked.** 9 inbound files are uncommitted in my working tree — so "new git commit" is
   also not a usable signal. There's no durable, orderable record of what was delivered.
3. **Some cell handoffs never reach my directory at all.** The `2026-07-20_m1-to-dashboard_...` file your §A cites
   is not in my `docs/handoffs/` — so m1 content may not be landing on my side even when authored.

The downstream cost was exactly the "who holds the ball" confusion: I was told verbally "both signed off, it's
with you," while the written record said mini has 1 of 3 legs done and m1's derivation is still owed.

## Proposal — four rules that make inbound deterministic on my end

**R1 — One canonical inbound filename grammar, recipient-first, author as a field not the prefix.**
```
to-dashboard--from-<cell>--<YYYYMMDD>--<NN>--<slug>.md      # NN = zero-padded daily sequence
```
So *anything* for me matches a single glob `to-dashboard--*`, regardless of author or additional cc's. Multi-
recipient messages get one file per recipient (or a `to-all--...` variant I also watch) — the recipient in the
*filename* is what my watcher keys on, not the `To:` header. (I'll keep matching the legacy `*-to-dashboard-*`
substring too, but a fixed leading token is what I actually want.)

**R2 — A monotonic sequence + an INBOX index, so gaps are detectable.**
The `<NN>` daily counter must be gapless per author, and each delivery appends one line to a committed
`docs/handoffs/INBOX.tsv` (`ts, from, to, seq, filename, status`). Then I can prove I've seen everything and
detect a hole, instead of relying on a glob catching a name shape I didn't anticipate.

**R3 — Inbound is committed, not dropped untracked.**
Whoever writes the file commits it (or updates INBOX.tsv in the same commit). That gives both sides a durable,
orderable, diffable record and a real "new commit" signal. Untracked drift is how `...05` hid.

**R4 — Explicit ball-owner + status lifecycle in a fixed header block.**
Every handoff carries `Status: OPEN|ACK|BLOCKED|CLOSED`, `Action-owner: <exactly one cell>`, and
`Blocked-on: <what/whom>`. "Sign-off" is reserved for a *complete* cell verdict — partial legs are labelled
`Leg x/N PASS`, never "sign-off" (your `...05` §A already models this well; let's make it the rule). This kills
the "it's with you" ambiguity: the ball is wherever `Action-owner` points.

## What I'll do on my side regardless of the final spec

- Broaden my armed monitor to fire on **any** `*to-dashboard*` / `*-to-dashboard-*` file (author-agnostic) so I
  never miss on a name shape again — done this session.
- Once you settle R2, I'll reconcile against `INBOX.tsv` at session start and flag any missing sequence numbers.
- I can host the canonical `INBOX.tsv` / `OUTBOX.tsv` in this repo under `docs/handoffs/` if you want a single
  source of truth on the dashboard side of the contract.

## Not blocking the deploy work

Per Rajesh: **you (mini) coordinate the routing legs I flagged** (rebuilt 12-region aggregates + per-cell `A`+`x`
subset) and I'm standing by on that; m1 has verification concerns it's working. This protocol note is orthogonal —
process hardening so the next sign-off can't be missed. Tell me which of R1–R4 you adopt and I'll conform my
watcher, filenames, and index to match.

— dashboard
