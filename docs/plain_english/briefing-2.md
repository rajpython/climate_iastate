# Session Briefing #2 — Mini's paper is frozen; we owed the paperwork for the data underneath it

**Date:** 2026-09-30 · **Topic:** the replication-package build records, and a mask disagreement that turned out to be a three-hour-old ghost

## The one-sentence version

Mini's paper is finished and frozen, so what remains is the replication package — the archive that lets a
stranger rebuild the results — and the part we owed was the paperwork proving where *our* data came from;
we delivered it, mini checked it against their sealed copies, and the one thing that didn't match turned
out to be a stale copy of a file they'd asked us to fix three hours before they took it.

## Background: who owes what

Mini writes the paper. **We are the data producer** — the nine-zone marine-heatwave series the paper
analyses is built by this repo, from NOAA satellite sea-surface temperature. A replication package can't
just say "the data came from the authors"; it has to state, checkably, *which* pipeline built it, from
*which* inputs, under *which* definition, and under *what* licence. That's what mini asked for, and none
of it existed as a written record.

## What we delivered

Four things, all verified rather than recalled:

1. **A build record.** Which commit's code actually ran (a subtle one: the vintage was deployed
   straight to the server before the fix reached the main branch, so the commit that *matters* is the one
   that captured the running bytes), which satellite files went in, the exact marine-heatwave definition
   applied, and the definition of every column in the data.
2. **A licence and a citation line.** You settled three open questions this session: the data project is
   the **Alaska Marine Heatwave Data Project** (no dashboard, no website URL — your ruling), the licensor
   is **you, sole author**, and there is **no DOI**, so the vintage id serves as the version. We shipped a
   proper CC BY 4.0 licence file, with the legal text fetched from Creative Commons today and its
   fingerprint recorded so mini could confirm we hadn't paraphrased it. They did, and it matched.
3. **The mask store** — the file that says which grid cells belong to which of the nine zones.
4. **A confirmation** that no other script anywhere in the repo rebuilds this series behind the pipeline's
   back, which the package asserts.

## The one number worth remembering

The satellite inputs are identified by a single fingerprint over 540 files. We recomputed it from our own
cache **70 days after the seal** and it came back **byte-for-byte identical**. So mini's copy of the input
list provably is ours. Three of the twelve threshold-field fingerprints reproduced exactly too, and mini
then reproduced all nine of the ones they hold.

## The disagreement, and why it was not a problem

Mini couldn't seal the mask store: **4 of its 31 files disagreed with our list.** They stopped and asked
rather than sealing over it — exactly right.

The four files are the three "combined" zones (Eastern Bering, Gulf of Alaska, Aleutians), each of which is
supposed to be the sum of its sub-zones. Back on **1 July**, mini flagged that our combined zones were a
few cells *bigger* than the sum of their parts — a polygon rounding artefact. We fixed it that morning and
rebuilt the file. The problem: mini had already packed their archive copy **a few hours earlier that same
morning**, before the fix. So they've been holding the pre-fix version ever since, and the version they're
holding is stale because of the change *they themselves asked for*.

Two independent ways we proved which version is the real one:

- **File timestamps.** All 31 of our files were written in a single pass at 11:26:45 that morning — two
  minutes before the commit that records the fix — and none has been touched since. The paper's data was
  built twenty days later, so it can only have read the fixed version.
- **The data itself.** In the published series, the three combined zones exactly equal the weighted sum of
  their sub-zones, across all 16,253 days, to seven decimal places. That's only true of the fixed version.

**And it changes nothing in the paper.** Every script in the package reads the nine sub-zones, and those
nine files are identical between us. We sent mini the corrected store, sealed, so they can finish.

## Two places where mini corrected *us*

Worth saying plainly, because this is the value of having an outside cell check the work:

- **We described how land is handled, and we described it wrong.** We'd written that land cells inside a
  zone "drop out" of the calculation. They don't. The denominator of the heatwave-area fraction is computed
  once from the fixed zone outline, so a cell that never has valid ocean temperature contributes nothing to
  the top of the fraction but its full weight to the bottom — permanently. Mini found this from the data
  (our own numbers only reproduce if you do it their way), and their sentence is now ours.
- **A miscount.** We said the onset-rate column has "five negative values". It's four daily and one
  monthly — a total across two different series, stated as if it were one.

Both are now in the record, and we asked admin to replace our earlier wording anywhere it reached shared
documents.

## What we did about the other cells

Since more than one cell holds a copy of the mask file, we didn't assume — we **checked all four**,
read-only. Result: **m1 and m4 both already hold the correct version, byte-for-byte in all 31 files.**
Mini's archive copy is the only stale one. So this is one stale file in one unpack directory, not a
programme-wide problem, and neither research cell needs to revisit anything. That determination went to
admin, who keeps the registry, so it binds across all four cells rather than living in one thread.

## One operational note

Mini's reply never reached us — this laptop was asleep when they pushed it. Our recovery tool found it and
pulled it down, hash-verified. This is now routine rather than exceptional, and worth knowing: the
session-start hook *lists* incoming mail but does not *collect* what never arrived.

## Where it stands

- **Us:** nothing open, except a DOI if you ever mint one.
- **Mini:** verify the store we sent, seal it, finish the package.
- **Admin:** register the canonical store and carry our two corrections.
- **m1, m4:** nothing.

Nothing has been published, deposited or submitted. Three commits sit locally on the feature branch,
unpushed.
