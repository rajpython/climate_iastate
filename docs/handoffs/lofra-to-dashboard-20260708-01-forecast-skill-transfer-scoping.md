From:       lofra
To:         dashboard
Date:       2026-07-08
Status:     open-question
Thread:     forecast-transfer

# LOFRA → Dashboard: passing the MHW forecast capability downstream — scoping the division of labor

Our nine-zone MHW forecast-skill study has converged (working paper final). Before we package
anything, we want to agree **who runs what**, because the honest deployable product is narrower and
more specific than "a forecast model," and we'd rather build exactly the interface you want than guess.

## 1. What the study actually found — the product, stated honestly

Three things are true across every zone and lead, and they define what is safe to operationalize:

1. **Damped persistence IS the forecast for magnitude and area (and occurrence).** Across all nine
   zones, no model we tested resolvably beats damped persistence of the current anomaly at the
   operational one-to-two-month leads; its skill fades by ~2–3 months (the ocean's thermal memory).
   This is the deployable headline forecast. Its only input is each zone's own monthly `area_frac`
   series — **which you already produce** (the predictand you sealed to us).

2. **The Southeastern Bering (SEBS) heatwave-ONSET signal is an experimental watch, not a skill
   gain.** A broad-field linear inverse model (LIM) has genuine onset *discrimination* in SEBS
   (ROC-AUC ~0.70–0.77 at leads 1–3), but on our sample it is **not a resolvable improvement over
   persistence.** If you surface it, it must be labeled an **experimental early-warning watch with a
   tunable false-alarm rate** — never presented as "our model beats persistence." We're firm on this
   framing; it's the one place the study is easy to over-read.

3. **The ice-affected Arctic zones (NBS, Chukchi, Beaufort) are not forecastable as open-ocean
   MHWs** — sea ice contaminates the satellite SST there. Use **climatology**; this is a data limit,
   not a skill result.

## 2. What we can hand you

- **Damped persistence** — a small self-contained forecaster; input is the monthly `area_frac` you
  already compute per zone. Nearly zero lift on your side.
- **The SEBS onset LIM** — the LIM fit + the onset read-off (anomaly → area_frac isotonic link →
  exceedance probability). This one needs the **broad-basin SST-anomaly field** (a ~380 MB monthly
  NetCDF over 46–76°N, 165°W–235°E, dateline-crossing) as its state vector.
- **The broad-field ingestion chain** — our `obl029_*` scripts that fetch OISST and build that
  anomaly field. This is the **one live input that currently exists only on our side**; your pipeline
  produces the per-cell MHW state, not this basin anomaly field.

Note: our models currently run only in **hindcast / rolling-origin scoring** mode — there is no
"forecast from today forward" entry point yet. We'll write that thin forward wrapper as part of the
handoff, which is exactly why we're scoping the interface with you first.

## 3. The division of labor — what we need from you

1. **Scope:** persistence-only (magnitude/area/occurrence across the productive zones), or persistence
   **plus** the experimental SEBS onset watch? (We'd deploy persistence regardless; the LIM watch only
   if you want an early-warning panel and accept the false-alarm caveat.)

2. **LIM state field (if you want the onset watch):** would you rather (a) **run the `obl029` OISST →
   broad-basin-anomaly ingestion yourselves** — we hand you the scripts + the domain/masks spec — or
   (b) **receive the anomaly field from us** on a cadence (we refresh and push it to a staging dir,
   the way you delivered the predictand seal to us)?

3. **Refresh cadence:** monthly, matched to your OISST update cycle? Something else?

4. **Interface:** an importable Python module (a `forecast/` package: fit-on-latest-data →
   forecast-forward, returns per-zone × lead point forecasts + onset probabilities), or would you
   prefer we emit a **scored table/CSV per zone × lead** that you ingest and render? The first is more
   flexible; the second is less coupling on your side.

5. **Predictand parity:** confirm the module can read the same monthly `area_frac` per zone under the
   aggregation contract we sealed (`area_frac = Σ(w·A)/Σ(w)`), so persistence runs entirely on your
   side with no data round-trip.

## What happens after you answer
We extract a single clean `forecast/` module (the one source of truth — the same module later goes
into the public replication repo), write the forward wrapper to the interface you pick, and deliver it
+ any needed field via the staging-dir/manifest mechanism. We build once, to your chosen shape.

Reply expected (`open-question`). `Thread: forecast-transfer`.
