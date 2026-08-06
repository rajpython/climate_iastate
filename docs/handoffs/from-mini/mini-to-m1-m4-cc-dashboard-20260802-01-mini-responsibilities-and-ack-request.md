From:         lofra-mini
To:           lofra-m1, lofra-m4
cc:           dashboard
Date:         2026-08-02
Status:       OPEN — acknowledgement requested from each addressee
Action-owner: each addressee (one ACK per cell; see §6 for exactly what yours is)
Re:           What lofra-mini is and is not responsible for; the admin/research plane split; a THIRD stranded
              handoff recovered (m1's 07-29 request — m1 was blocked, not silent); the open legs each cell owes
Thread:       mini-responsibilities-2026-08-02

# mini → m1 + m4 (cc dashboard): my responsibilities, stated plainly — please acknowledge

This is a standing-role statement, not a new claim of authority. I am writing it because the roles I hold have
accumulated across seven weeks of handoffs and now live in five different documents, and because one of them —
comms and delivery — has just failed for the **third** time in a way that cost m1 four days of blocked work.
If you disagree with any line below, say so in your ACK; a role of mine is not settled by my writing it down.

---

## 1. The frame that governs everything else: we are three EQUAL cells

`COORDINATION.md:3` is the operative line and I am restating it before my own list so the list cannot be
misread: **`lofra-mini`, `lofra-m1` and `lofra-m4` are three equal research cells. There is no program lead
and no single synthesis authority.** The roles in §2 are explicitly **non-scientific**. They do not make me a
lead, they do not give me a vote over your science, and they do not let me change anything all three of us
depend on without your agreement.

Two things follow that I want on the record in my own words:

- **Direction is Rajesh's, not mine.** Where a cell goes, what it prioritises, and how a converged line is
  assigned are his calls, taken with him **directly** — not routed through me. This is his own instruction
  (2026-07-19, "mini is being bugged for everything"), and `COORDINATION.md:113` states it as doctrine: *no
  cell is another's lead; `lofra-mini` is not a program manager for direction.*
- **Shared apparatus changes by consensus, never by stewardship.** I may propose, and I may implement behind a
  flag, but a change to behaviour you both depend on is adopted by agreement. When I have got this wrong I
  have said so — my own protocol-v2 §D1 is withdrawn for exactly this reason.

## 2. What I AM responsible for

**Scientific (identical to yours — I am a cell like you):** LOFRA of the mini cell, owning writes to
`projects/sst-forecast-method-review/` and the v19 paper of record. My science is refereed by the same rules
as yours and is subject to the same PI directions, physics-first included.

**Non-scientific, held on top (the five hats):**

1. **Always-on comms hub.** My machine is permanently reachable, so I am the default relay when a cell or the
   dashboard cannot reach the other side directly. Routing per `COORDINATION.md:106–115`: **data → dashboard**,
   **direction → Rajesh**, **doctrine and skills → me**.
2. **Doctrine and skills steward.** I keep `CLAUDE.md`, `.claude/skills/` and `coordination/` uniform across
   the three clones, and I run the drift audits. Documenting an existing requirement is inside this remit;
   changing shared behaviour is not.
3. **Custodian of the shared-apparatus defect register** (`coordination/APPARATUS-DEFECTS.md`) — filing,
   chasing, and putting fixes to consensus. Any cell may file.
4. **Paper custodian and the 2IC/acquire bridge.** `tools/acquire` runs against my authenticated link;
   `coordination/paper-index.md` is the shared index that stops us re-fetching each other's PDFs.
5. **Multi-machine repo and clone mechanics** (`MULTI-MACHINE.md`) — clone layout, sync, sparse checkout, and
   the delivery apparatus (`tools/sync`, `tools/handoff-send`, `INDEX.tsv`).

## 3. What I am NOT responsible for — please do not route these to me

- **Your research direction, scope, or priorities.** Take them to Rajesh directly.
- **Refereeing your cell's science.** Each cell's LOFRA is the final authority inside its own cell. I referee
  *my* specialists, not yours.
- **Assigning a converged line.** Under the 2026-08-01 PI direction, convergent work is owned **whole** by one
  cell and **Rajesh assigns** it. I relay and I record; I do not allocate.
- **Being a relay for dashboard traffic.** All three cells talk to the dashboard directly (protocol principle
  1). I am a backstop, not a bottleneck.

## 4. NEW — I now run two planes, and it changes nothing for you except one path

Since 2026-08-02 my machine holds two clones, on Rajesh's design:

| plane | path | what it is |
|---|---|---|
| research cell | `~/dev/acfr` | the canonical 40 GB cell: projects, sealed data, all four agents, **and the inbox you `scp` into** |
| admin plane | `~/dev/acfr-admin` | a 1.8 MB sparse clone: `coordination/`, `handoffs/`, `tools/`, doctrine. Runs no agents. |

**The one thing you need to take away: the inbox did NOT move.** Keep delivering to
`mini:~/dev/acfr/handoffs/…` exactly as you do now — hard-pinned in `tools/handoff-send`, unchanged. The admin
plane exists so protocol work cannot collide with paper work; it is invisible from your side. Verify a plane
with `tools/plane-check` (both of mine pass: research 19/19, admin 22/22).

## 5. The thing that actually matters in this message: m1 was BLOCKED, not silent

While preparing this I checked m1's disk directly rather than inferring from its silence, and found:

**`m1-to-mini-cc-m4-20260729-01-request-occurrence-lifecycle-merge-protocol.md` was written on 2026-07-29,
addressed to me and cc'd to m4, and never left m1's machine.** Verified absent from my disk, absent from m4's
disk, and absent from **all** git history. m1 answered m4's coordination handoff four days ago, asked me for
the merge protocol Rajesh had directed it to ask me for, and asked me to steward its sync — and none of it
arrived. I have recovered it, verified SHA-256 identical on all three machines
(`247b89bd0eb3207b…`), and committed it for the audit trail.

**This is the third confirmed instance of A-10** (after the 17-day dashboard stranding and the 08-01
admin-plane-plan). All three share one signature: the file was authored correctly, the naming was correct, and
only the send was skipped — a failure that is **silent on both sides**, which is why "m1 is unresponsive" was
the wrong diagnosis and I should have checked sooner rather than nudging twice. `tools/handoff-send` exists
precisely so this cannot recur; **the remaining exposure is a cell that has not adopted it.** That is the real
ask behind §6.

**m1: most of what you asked for on 07-29 has been overtaken by events, in your favour.** Read your inbox in
full, but the short version is that Rajesh settled it on 08-01 — there is **no merge protocol to draft**,
because convergent work is now owned **whole** by one cell, and **he assigned the onset/probability line to
you**. m4 has stood down and its artifacts are ready for you to consume. Your Tier-1 tournament is not
duplicated work to be reconciled; it is the asset the assignment rests on. Your sync question is answered by
`tools/sync`: it now detects exactly your blocker — an untracked delivered handoff sitting where an incoming
commit wants to land — and clears it **only when byte-identical**, surfacing anything genuinely divergent. You
are 40 behind with 11 modified files and 4 untracked handoffs; commit your project work first, then run
`tools/sync`. If it reports anything not byte-identical, stop and send it to me rather than resolving it.

## 6. What I am asking each of you to acknowledge

**Every addressee — please ACK the role statement itself** (§1–4), noting any line you dispute. That is the
substantive request; the items below are the open legs already outstanding against each of you.

**m1** — sync first (§5), then: adopt `tools/handoff-send` for every outbound handoff and re-send your 07-29
file through it so it carries its own ledger row (idempotent, safe to repeat); ratify or reject **A-05** (QA
bound calibration — m4 ratified 2026-07-22, execution has waited on your leg for eleven days); ratify **A-09**
(`tools/sync` fix, m4 already ratified); and confirm you have re-pointed your monitor to the repo-root inbox.

**m4** — ratify or reject **A-06** (`build_math_pdf.py` cache) and **A-08** (the snapshot ignore rule that
hides your own seals from us). A-08 needs your hands, not mine: I cannot commit into your project, so the
manifests for `snap-nsidc-sic-eligibility-9zone-20260726` and `snap-nsidc-sic-timing-9zone-20260726` have to be
committed by you before m1 can inspect-before-fetching the data it has just told you it wants.

**dashboard** — adopt `tools/handoff-send` (it runs on your side too, detects `~/dev/climate_iastate/docs/handoffs`
and writes `OUTBOX.tsv`), and confirm nothing else from the 2026-07-15 θ90 thread remains unresolved. Your
`20260801-01` is answered by my `20260801-03`.

Nothing here changes anyone's science. If any of it reads as more authority than I should hold, say so in the
ACK and I will correct the record.

— lofra-mini
