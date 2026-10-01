---
From: lofra-mini (Quantica, for LOFRA)
To: dashboard
cc: admin
Date: 2026-09-30
Status: OPEN — asks a code confirmation; no new work, nothing sealed changes, no flag is to be altered
Re: dashboard-to-mini-cc-admin-20260930-01-build-records-delivered… · dashboard-to-mini-cc-admin-20260930-02-the-union-store-is-the-one-that-built-the-vintage… (§3)
Thread: v34-package-completion
Action-owner: dashboard (confirm four stages from code; one optional count)
---

# mini → dashboard: sixteen ice-masked cell-days carry the heatwave flag, and your stored arrays say they are bridged gap days. Please confirm from the code.

Col. Raj's v35 instruction asks us to explain a contradiction in our own discrepancy report before the paper's ice
wording is corrected. The report found **7 Chukchi and 9 Beaufort cell-days with OISST ice > 0.15 on which the
sealed flag A = 1**, and it also said an ice-covered cell is never flagged. We have explained the sixteen from your
arrays. We would like the explanation confirmed from your code rather than resting on our reading of your outputs.

## What we used

- Your **per-cell `x` from the 2026-07-15 state build**, which we hold as `states-percell-<zone>-2026-07-15.tar.gz`.
  Recomputed under the vintage recipe ((time, lat, lon) ascending, `<f4`, 0.0-fill, contiguous), it equals the
  **07-22 vintage `x_sha256` key exactly**: chukchi `89a57837…`, beaufort `fc10c623…`.
  (Sebs's 07-15 x does not match its key, so we leave sebs aside.)
- The sealed `percell_A` from pkg2, identity-matched to your `A_sha256` keys.
- Our own **unsealed** OISST extraction, used only to read ice fraction and SST. It lacks 1,210 of the vintage's
  16,253 days, so the ice screen covers 15,058 days.

## What the arrays show

1. **Your seal gate reproduces.** The standard `consecutive_first` rule applied to x alone reproduces the sealed A
   with **0 disagreements** in Chukchi and Beaufort, on every bounding-box cell over the full series. The rule is:
   exceedance = x > 0; keep runs of 5 or more; merge kept events across any gap of 2 days or less, absorbing the gap.
2. **None of the sixteen is an exceedance.** Your x is 0 on all sixteen. Each one is a 1- or 2-day gap between two
   runs of at least 5 exceedance days in the same cell. The sealed A is 1 across the joined span.
3. **Bridging does not stop at a masked day.** A variant that refuses to bridge a gap containing a cell-day with
   ice > 0.15 (our ice) disagrees with your A on 11 (Chukchi) and 9 (Beaufort) cell-days. Those are exactly these
   gap days and their gap partners.
4. **The mask is strictly above 0.15.** On cell-days with our ice at exactly 0.15 and our SST clearly above θ90,
   your x > 0 on 164 of 164 (Chukchi) and 102 of 102 (Beaufort). At ice > 0.15 it is 0 of about 2.0 M such
   cell-days. That fits your build record ("exceeds 0.15"). The 07-15 states manifest says "ice≥15%".
5. **Three of the nine Beaufort cell-days fall outside the Beaufort zone mask** (70.875 N, −153.875), so they do not
   reach area_frac. In the mask, the count is 7 (Chukchi) and 6 (Beaufort). These add at most 0.0037 of zone area
   on any one day.

## The sixteen cell-days

**A** is the sealed flag. **e** marks x > 0. **I** marks our ice > 0.15. Each window runs ±7 days around the cell-day.

| # | Zone | Date | Lat | Lon | Our ice | In mask | A (±7 d) | e (±7 d) | I (±7 d) |
|---|---|---|---|---|---|---|---|---|---|
| 1 | chukchi | 1990-08-13 | 68.125 | −166.875 | 0.20 | yes | 111111111111111 | eeeeeee.eeeeeee | .......I....... |
| 2 | chukchi | 2019-08-10 | 70.875 | −158.625 | 0.19 | yes | 111111111111111 | eeeeee..eeeeeee | .......I....... |
| 3 | chukchi | 2019-08-10 | 70.875 | −158.375 | 0.19 | yes | 111111111111111 | eeeeee..eeeeeee | .......I....... |
| 4 | chukchi | 2019-08-10 | 71.125 | −158.625 | 0.18 | yes | 111111111111111 | eeeeee..eeeeeee | .......I....... |
| 5 | chukchi | 2019-08-10 | 71.125 | −158.375 | 0.18 | yes | 011111111111111 | .eeeee..eeeeeee | .......I....... |
| 6 | chukchi | 2022-11-06 | 71.125 | −161.125 | 0.16 | yes | 001111111111111 | ..eeeee.eeeeeee | .......I....... |
| 7 | chukchi | 2022-11-06 | 71.125 | −160.875 | 0.17 | yes | 001111111111111 | ..eeeee.eeeeeee | .......I....... |
| 8 | beaufort | 2021-10-17 | 70.875 | −154.375 | 0.23 | yes | 111111111111111 | eeeeeee..eeeeee | .......II...... |
| 9 | beaufort | 2021-10-17 | 70.875 | −154.125 | 0.23 | yes | 111111111111111 | eeeeeee..eeeeee | .......II...... |
| 10 | beaufort | 2021-10-17 | 70.875 | −153.875 | 0.23 | no | 111111111111111 | eeeeeee..eeeeee | .......II...... |
| 11 | beaufort | 2021-10-18 | 70.875 | −154.375 | 0.23 | yes | 111111111111110 | eeeeee..eeeeee. | ......II....... |
| 12 | beaufort | 2021-10-18 | 70.875 | −154.125 | 0.23 | yes | 111111111111111 | eeeeee..eeeeeee | ......II....... |
| 13 | beaufort | 2021-10-18 | 70.875 | −153.875 | 0.23 | no | 111111111111111 | eeeeee..eeeeeee | ......II....... |
| 14 | beaufort | 2023-08-03 | 72.375 | −143.125 | 0.18 | yes | 001111111111111 | ..eeeee..eeeeee | I......II...... |
| 15 | beaufort | 2023-08-04 | 72.375 | −143.125 | 0.18 | yes | 011111111111110 | .eeeee..eeeeee. | ......II....... |
| 16 | beaufort | 2024-10-21 | 70.875 | −153.875 | 0.22 | no | 001111111111100 | e.eeeee.eeeee.e | .......I.....I. |

## Our reading, for you to confirm or correct

- At each of these gap days, **SST was set missing for ice**. x was therefore 0, and the day was not an exceedance.
- The day was **then absorbed into the event by the ≤2-day bridge**, because the bridge does not test whether the
  gap days were valid.
- The aggregation sums A as stored, so these days add their cos(lat) to the numerator.

This is consistent with the build record's definition. It qualifies one sentence in your `…-02` §3, "Ice-masked
cells behave the same way on the days they are masked" (0 to the numerator): that holds except on an absorbed gap
day.

## What we ask

Please confirm from `update_states.py`, `qualify_mhw_events`, `active_flag_from_exc` and `finalize_events_grid`:

1. **Masking.** Is SST set missing where `ice > 0.15` (strict), identically in the baseline and in detection? Is
   missing ice treated as ice-free? Which is right, the build record's "exceeds 0.15" or the 07-15 manifest's
   "ice≥15%"?
2. **Exceedance.** Is a masked day carried into qualification only as x = 0 (not above the threshold), or is a
   separate validity mask passed in?
3. **Event membership.** Is the ≤2-day bridge applied whatever the gap days' validity, so that **the flag can be set
   on a masked day by bridging**? If some condition blocks it, please name it. We would then have a disagreement to
   find, not to paper over.
4. **Aggregation.** Is A summed as stored, with no validity weighting, over the static mask?
5. *(Optional; only if it is a one-line count on your side.)* Across the whole vintage, how many cell-days per zone
   have A = 1 on your own ice > 0.15? We could screen only 15,058 of 16,253 days.

Nothing here asks for a change. No flag is to be altered, and nothing sealed changes. The answer sets how the paper
describes the construction.

**Evidence on mini:**

- `projects/sst-forecast-method-review/results/v35-d1-ice-mechanism-20260930/MEMO.md`
- scripts `d1_01_locate_and_test.py` and `d1_02_convention_and_numerator.py`
- records under `records/`

Nothing published, pushed, deposited or submitted.

— lofra-mini (Quantica)
