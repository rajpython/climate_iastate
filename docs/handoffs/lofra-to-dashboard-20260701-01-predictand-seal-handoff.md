From:       lofra
To:         dashboard
Date:       2026-07-01
Status:     resolved
Re:         dashboard-to-lofra-zone-and-data-answers-2026-06-30.md
Thread:     predictand-seal-handoff

# LOFRA → Dashboard: reciprocal ask answered — seal all 9 together after the Arctic all-clear

Thanks — your answers resolve OBL-031 and we've adopted the partition. We're also adopting the shared
**HANDOFF-CONVENTION v1** (with the `Status:` line), and this file follows it. Answers to your five items:

1. **Access mode:** bulk-snapshot **push** — confirmed.
2. **Landing path:** push to our staging dir
   `mini:/Users/rajpython/dev/acfr/projects/sst-forecast-method-review/data/incoming/`. We do **not** land it
   directly as a snapshot of record — Quantica verifies your SHA-256, runs our `qa_gate`, and re-seals it as
   our own immutable snapshot. (Provenance/QA stays on our side; no reflection on your seal.)
3. **Freeze date:** **one combined seal of all 9 zones at a single common vintage — _after_ your
   `chukchi`+`beaufort` rebuild all-clear.** Please don't cut a 7-zone snapshot now; we'd rather have all 9 at
   one date. Seal at the latest monthly-refresh boundary that is current when the Arctic rebuild is verified
   consistent on the new EEZ polygons.
4. **Scope of the seal:** everything in one snapshot — **9 leaves + 3 aggregates + AO/PDO + cold-pool
   covariates** (aggregates for our `/states` cross-check; covariates frozen at the same vintage for OBL-029).
5. **Format:** sealed tarball + SHA-256 manifest — confirmed.

**Sequencing.** We're holding OBL-028 for your follow-up handoff (`Status: resolved`, `Thread:
chukchi-beaufort-seam`) confirming `chukchi`+`beaufort` are internally consistent on the new US-EEZ Arctic-FMP
polygons. On that all-clear, cut the combined 9-zone seal and push to the staging dir above. We'll then
QA-gate, re-seal, aggregate per your contract + masks/weights, and cross-check our GOA/EBS/AI roll-ups against
`/v1/regions/{goa,ebs,ai}/states`.

**On our QA side** we'll confirm the Arctic masks are water-only/land-clipped and check coverage at the
documented ~0.17° NBS/Chukchi Bering-Strait gap and across the 9-leaf tiling — flagging back anything that
doesn't reconcile, per your standing invitation.

Every seam and polygon is now settled on our side (thanks for the Point-Barrow move and the EEZ upgrade). No
open questions from us — this is `resolved`; the next move is your combined seal + push after the Arctic
all-clear.
