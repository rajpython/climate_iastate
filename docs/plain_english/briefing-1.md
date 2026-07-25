# Session Briefing #1 — Fixing and freezing the marine-heatwave "threshold"

**Date:** 2026-07-16 · **Topic:** the θ90 (theta-90) smoothing correction, from bug to live board

## The one-sentence version

We found and fixed a real error in how the dashboard defines a marine heatwave, rebuilt every
downstream number from 1982 to today, proved our corrected data is byte-for-byte identical to what our
research partner (LOFRA) is publishing against, locked it as the official version, and pushed it live to
the public board at marine.iastate.ai.

## What was wrong

A "marine heatwave" is defined relative to a **threshold**: for each day of the year, we compute how warm
the ocean usually is, and flag temperatures above the 90th percentile ("θ90") as unusually hot. The
standard scientific recipe (Hobday et al., 2016) builds that threshold in **two steps**: first pool a
window of nearby days to estimate each day's value, then **smooth the result across the calendar year** to
remove the jitter that comes from having limited data.

Our pipeline did step one but silently skipped step two. LOFRA — a separate research group re-checking our
work for a paper — caught it. We confirmed it was an honest oversight, not a deliberate choice, and
decided to do it the correct, standard way.

**Why it mattered:** that threshold is the line that *defines* the entire product. Every marine-heatwave
day, every "percent of the shelf in a heatwave" number, and every risk score is measured against it. So a
small change to the threshold ripples through everything.

## What we did about it

1. **Fixed the threshold** — added the missing smoothing step and rebuilt the threshold for all twelve
   Alaska regions. The effect was modest but real (the threshold shifted by about a tenth of a degree on
   average, more at the tricky spring-to-summer transition), and it slightly *reduced* the number of false
   heatwave days caused by the old jitter.

2. **Handled a data-vintage snag** — for the two Arctic regions (Chukchi and Beaufort), some recent
   baseline years were re-downloaded during the rebuild, which briefly made our "before" and "after" files
   inconsistent. We diagnosed it, regenerated a clean matching set, and re-shipped.

3. **Rebuilt the whole product** — with the corrected threshold, we re-ran the entire history
   (1982–present) to regenerate the heatwave states, the regional summaries, and the risk scores. We caught
   a second bug in the process (one regional roll-up came out blank for 2026 because of an empty data file)
   and fixed that too.

4. **Let LOFRA verify independently** — we shipped them the corrected threshold and the underlying
   day-by-day data so they could reproduce our numbers from scratch with their own code. They did, and
   everything matched to the last decimal.

5. **Froze it and proved identity** — before locking it, we verified file-by-file that the data LOFRA
   holds and the data we hold are **byte-for-byte identical** (thousands of files, all matching), so both
   sides are provably working from one and the same product. We then recorded it as the official, frozen
   version in our code history (a git commit and a tag).

6. **Deployed to the live board** — pushed the corrected data to the production server and confirmed the
   public site is serving the corrected numbers, extends up to today, and is healthy. A file-permission
   snag on the server (a technical ownership issue) briefly blocked the upload; it was resolved cleanly
   with no data loss or corruption.

## Where things stand now

- The public dashboard (marine.iastate.ai) shows the **corrected** marine-heatwave product.
- LOFRA is unblocked and can run their paper's analysis against a product that is identical to, and frozen
  in lockstep with, ours.
- The corrected product is the single official version; any future change will be an explicit, versioned
  update — never a silent one.

## Bottom line

A subtle but genuine methodological error in the core definition of the product was found, corrected,
independently verified, frozen, and deployed — with proof at every step that our numbers and our research
partner's numbers are one and the same.
