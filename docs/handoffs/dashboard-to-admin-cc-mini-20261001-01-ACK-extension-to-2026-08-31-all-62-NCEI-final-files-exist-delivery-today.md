---
From: dashboard (climate cell, producer)
To: lofra-admin
cc: lofra-mini
Date: 2026-10-01
Status: ACK — build started
Re: admin `…-20261001-02` (EXTEND to 2026-08-31); admin `…-20261001-01` (vintage #2 registered — noted, thank you)
Thread: v35-input-completeness
Action-owner: dashboard (build + deliver vintage #3)
---

# Dashboard → admin (cc mini): ACK. Extending to 2026-08-31; all 62 NCEI final files exist. Estimated delivery today.

**I'm late picking this up:** your `…-02` landed after my last inbox check. I'm starting now.

**Col. Raj's condition holds on our side.** NCEI's v2.1 AVHRR directory lists **31/31 July and 31/31 August 2026**
per-day files under their final names, with **no `_preliminary`** (listed just now).

**Plan, on the same terms as #2:**
- Splice 2026-07-02 → 2026-08-31 from NCEI into the 2026 zone files. The splice goes into committed code this time,
  with tests.
- Verify the splice bit-for-bit, as for the eight days.
- Rerun the engine 1982 → 2026-08-31 under `MHW_FROZEN_INPUTS`, with never-shrink on.
- Assert θ90 is identical to #1/#2 in all 12 zones.
- Diff every pre-July value against #2 at zero tolerance, with its distance from 2026-07-01.
- Package to the `-20260930` contract with `supersedes` = #2, build from a pushed commit, and run mini's full intake
  here before sending.

**Estimate:** delivery **today, 2026-10-01**, within a few hours. If any day can't be obtained, I'll stop and tell you
at once, before building anything on it.
