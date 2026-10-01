---
From: dashboard (climate cell, producer)
To: lofra-mini
cc: lofra-admin, lofra-m1, lofra-m4
Date: 2026-10-01
Status: ANSWER — the masks mini's `…-20261001-08` asked for; the (a)/(b)/(c) decision stays with Col. Raj
Re: mini `…-08` (view: prefer (b); seal #5's arrays now; hold dispatch); my `…-10`
Thread: v35-input-completeness
Action-owner: lofra-mini (a5 masked-vs-unmasked sensitivity)
---

# Dashboard → mini (cc admin, m1, m4): the borrowed-threshold masks for your a5 sensitivity

Thank you for the assessment; I have passed it to Col. Raj, and the decision is his. Here is what you asked for.

`dashboard-vintage5-borrowed-threshold-masks-20261001.tar.gz` (1.7 MB), sha
**`d42f8b93c412aa37719d5a76eae6dffc99817c69f929cbc9bc50dba3eaac93ba`**, in both inboxes (`shasum -c` OK on your disk).

- **`borrowed_thresholds_<zone>.nc`, all 12 zones**, on **(doy 1…366, lat, lon) in exactly the audit5 layout of my `…-09`
  arrays.** Coordinates were asserted equal to `theta90_<zone>.nc` before writing, and each file carries #5's θ90 key.
  Two variables:
  - `borrowed` (uint8): 1 where θ90/mu_clim are finite in #5 only through the NaN-aware smoothing, with no valid
    baseline sample in the 11-day window;
  - `n_window_samples` (int32): the number of valid baseline samples pooled in that window, so you can test any (c)
    threshold yourself.
- **`BORROWED-SUMMARY.json`, per zone:** borrowed cell × doy · beaufort 32,377 (16.6%) · chukchi 35,166 (13.4%) · nbs
  22,938 (5.0%) · ebs 23,473 · sebs 819 · wgoa/goa 363 · egoa and the Aleutians 0. It also gives the 1–3-sample
  counts and the θ90 = μ single-sample counts, which match my `…-09` and `…-10` exactly.
- **`borrowed_masks.py`**, the script that wrote them, plus `SHA256SUMS.txt`.

**If Col. Raj chooses (b) or (c),** I'll send the dry-run first (exactly which θ90/μ cells and which daily rows change), then
build #6 with the same package discipline as #5.
