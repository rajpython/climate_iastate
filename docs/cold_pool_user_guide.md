# The Bering Sea Cold Pool — A Plain-Language Guide to the Cold-Pool Dashboard

*A guide for anyone — no oceanography or statistics background needed. After reading
this, you should be able to explain every number and chart on the two cold-pool pages —
**"Cold Pool: Observed & Validation"** and **"Cold Pool: Model Comparison"** — and answer
questions about them.*

---

## 1. The one-paragraph version

Off the coast of Alaska, in the eastern Bering Sea, there is a patch of unusually cold
water that sits on the seafloor every summer. Scientists call it the **cold pool**. Its
size changes a lot from year to year, and that size matters enormously for fish and crab
— and therefore for the fishing industry and the communities that depend on it. This
dashboard tracks **how big the cold pool is each year**, measured three different ways:
from a **real research survey** that goes out and takes the ocean's temperature with a
ship, and from **two independent computer models** of the ocean. Comparing them lets us
check that the models are trustworthy — and they are: all three agree very closely, and
where the two models differ from each other we get an honest measure of the uncertainty.

---

## 2. Background: what are we even looking at?

### First, what is a "continental shelf"?
A **continental shelf** is the **shallow, gently sloping seafloor that extends out from
the coastline** before the seafloor suddenly plunges into the deep ocean. Picture the edge
of a swimming pool: you wade out across the shallow shelf where you can still stand, and
then there is a sharp drop-off into the deep end.

So a shelf is a **place** — a horizontal area of seafloor on the map, defined by the water
above it being shallow. It is **not** a vertical column or a blob of water. Here is a
side-on slice, going from the Alaska coast out toward the open ocean:

```
  COAST
   │
   │░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
   │░░░░░░░  SHELF (shallow, ~50–200 m)  ░░░╲                ← water surface
   │▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒╲
   └───────────── seafloor ──────────────────╲
                                               ╲  ← "shelf break" / drop-off
                                                ╲
                                                 ╲░░░░░░░
                                                  ╲   DEEP
                                                   ╲  BASIN
                                                    ╲ (1000s of m)
                                                     ╲░░░░░░░░░░
```

The **eastern Bering Sea** has an unusually wide, flat shelf — it reaches hundreds of
kilometers offshore with the water only ~50–200 m deep the whole way, before dropping into
the deep Bering basin. When this guide says "**keep only the shelf (≤ 200 m)**," the 200 m
is the **water depth at each location** — we keep map spots where the seafloor is shallower
than 200 m (the shelf) and ignore spots where it plunges deeper (the basin). The cold pool
lives **only** on this shallow shelf.

### Where is this?
The **eastern Bering Sea (EBS)** is the part of the Bering Sea that sits on that wide,
shallow continental shelf west of Alaska — between the Alaska mainland and the deeper
ocean. It is one of the most productive fishing grounds on Earth: most of America's
pollock (the fish in fish sticks and fast-food fish sandwiches), much of its snow crab
and king crab, and a lot of Pacific cod come from here.

### Surface vs. bottom
When people talk about "ocean temperature" they usually mean the **surface** — the top
of the water, which is what satellites see and what swimmers feel. But fish and crab on
the shelf live on or near the **seafloor (the bottom)**, often 50–200 meters down. The
temperature *down there* can be completely different from the surface, and it is the
**bottom temperature** that controls where bottom-dwelling animals can live. This page is
about the **bottom**, not the surface.

So how do you measure the temperature of a shelf? Not as one block — you measure it
**location by location**. At each spot on the shelf, "bottom temperature" means the
temperature of the thin layer of water *right at the seafloor* there. The survey does this
by lowering a sensor to the bottom at each station; the models do it by reading the
deepest water layer in each grid cell. The **cold pool** is then simply *the collection of
shelf locations whose bottom water is at or below 2 °C* — a cold patch on the map, which
is why its size is reported as an **area** (km²).

### What is the "cold pool"?
Each winter, sea ice forms over the northern shelf. Making ice squeezes out salt, which
makes the water beneath it dense and very cold; that cold, salty, dense water sinks and
pools on the seafloor. When the ice melts in spring, this cold bottom water is trapped down
there and **lingers through the whole summer**, even as the surface warms up. The result is
a large area of the shelf where the bottom water stays at or below **2 °C (about 36 °F)** —
that is the **cold pool**. *(This definition and formation mechanism follow Kinney et al.
2022, who describe the cold pool as "the region of the Bering Sea shelf where bottom water
is < 2 °C throughout the summer," formed when "seasonal sea ice formation in winter results
in the formation of this cold, salty and dense water mass" — see References.)*

### Why does it matter?
The cold pool acts like an **invisible fence on the seafloor**. It "delineates the boundary
between Arctic and subarctic fish species" (Kinney et al. 2022):

- **Pollock and Pacific cod** tend to stay out of the cold pool, so a big cold pool pushes
  them into a smaller area (and changes where boats must go to catch them). When the cold
  pool was greatly reduced in 2017–2019, large proportions of the pollock and cod stocks
  shifted north (Kinney et al. 2022).
- **Snow crab**, by contrast, are a cold-water species associated with the cold pool. A
  2018–2019 marine heatwave that erased the cold pool was linked to a collapse of eastern
  Bering Sea snow crab — billions of crab disappeared (Szuwalski et al. 2023) — and the
  fishery was **closed for the first time in 2022, and again in 2023** (Alaska Dept. of
  Fish & Game; it reopened in 2024).

So the size of the cold pool, year to year, is a leading indicator of where the fish are
and how the ecosystem is doing. That is why it is worth a dashboard.

---

## 3. The key number: "cold-pool area"

The headline measurement on this page is an **area**, in **square kilometers (km²)**:

> **Cold-pool area (≤ 2 °C)** = how much of the shelf seafloor has bottom water at or
> below 2 °C.

A **bigger** number means a **bigger, colder** cold pool (a cold year). A **smaller**
number means the cold pool shrank (a warm year). To give a sense of scale:

| Year | Cold-pool area (≤2 °C, observed) | Roughly the size of… |
|------|----------------------------------|----------------------|
| 2012 (a cold year) | ~369,000 km² | Germany / Montana |
| 2025 (recent) | ~113,500 km² | Ohio |
| 2018 (record collapse) | ~6,200 km² | Delaware |

For comparison, the *entire* area the survey covers is about **490,000 km²** — roughly
the size of Spain. So in 2012 the cold pool covered most of the shelf; in 2018 it had
almost vanished.

### Colder thresholds
The page lets you choose a temperature threshold: **≤ 2 °C, ≤ 1 °C, ≤ 0 °C, or ≤ −1 °C**.
Think of these as "cold," "colder," "very cold," and "extremely cold." Each one measures
the area of seafloor below that temperature. The ≤ 2 °C version is the standard,
headline definition of the cold pool; the colder thresholds show the *core* of the
coldest water. (Yes, ocean water can sit below 0 °C without freezing, because it is
salty.)

---

## 4. Three ways we measure the cold pool

The whole point of the page is that we measure the same thing **three independent ways**
— one set of real observations and two computer models — and compare them.

> **First, an important clarification: "cold pool" is always a *shelf* thing, in every
> method.** The cold pool, by definition, is cold *bottom* water sitting on the shallow
> **continental shelf**. The deep Bering Sea basin off the edge of the shelf is cold on
> the bottom all year round, but that is just "the deep ocean is cold" — it is **not** the
> cold pool and nobody counts it. So:
> - The **survey** is *naturally* shelf-only: the research vessels only trawl the shelf,
>   so the cold-pool index is automatically confined to the shelf — there is no deep water
>   in it to begin with.
> - The **models** simulate the *entire* ocean including the deep basin, so we have to
>   *deliberately* trim them to the shelf (keep only water shallower than 200 m) to match
>   what the survey naturally measures. That trimming step exists only to make the models
>   comparable to the survey — it is not an extra assumption about what the cold pool is.
>
> In all three, "**bottom temperature**" means the temperature of the water touching the
> seafloor (not the surface), and the cold-pool area is "how much shelf seafloor is at or
> below the threshold."

### Way 1 — OBSERVED: the research survey (the "ground truth")
Every summer, NOAA's Alaska Fisheries Science Center (AFSC) sends research vessels across
the eastern Bering Sea **shelf**. At a fixed grid of **hundreds of stations**, they lower
a net (a "bottom trawl") to the seafloor. Attached to the gear is a temperature sensor, so
each haul records the **actual bottom temperature at that spot** (scientists call this
"gear temperature" because it is measured on the trawl gear).

To turn those hundreds of point measurements into an *area*, they fill in the map between
stations (interpolation) to make a smooth temperature map of the surveyed shelf, then
**add up the area of every patch colder than the threshold**. That total is the observed
cold-pool index. Because the survey only ever visits shelf stations (its official
footprint is about **490,000 km²** of shelf), its cold-pool number is inherently a
shelf measurement — no deep water is involved.

- **It is the gold standard** — real measurements from the real ocean.
- **It is annual** — one number per year, from the summer survey.
- **It is lagged, not live** — you only get a year's value after that summer's survey is
  done and processed.
- **It has gaps** — notably **2020**, when the survey was cancelled (COVID), so there is
  simply no observed value that year.
- **Coverage: 1982–2025.**

### Ways 2 & 3 — MODELS: two computer simulations of the ocean
A "model" here is not a guess — it is a detailed **physics simulation of the ocean**,
driven by real historical weather (winds, air temperature, sea ice), that computes the
temperature, currents, salinity and ice everywhere on a fine grid, including the **bottom
temperature in every cell**. We use **two** independent models (introduced in §4a). To
get a cold-pool number from either model that is comparable to the survey, we do the same
four steps:

1. **Pick the survey-time snapshot.** For each year we take the model's bottom temperature
   for the period nearest **early July** — the middle of the survey season (the week
   nearest early July for Bering10K, the July month for MOM6).
2. **Put it on a clean map grid.** We re-map the model onto a regular latitude/longitude
   grid (¼-degree cells) so it lines up with the rest of the dashboard.
3. **Trim to the shelf.** We keep only cells shallower than **200 meters** and ignore the
   deep basin (see the clarification box above). **Both models use the *same* shelf
   outline**, so they are measured on identical ground — which makes them directly
   comparable to each other, not just to the survey.
4. **Add up the cold area.** We count every shelf cell at or below the threshold and add
   up their areas — the same idea as the survey, just on model cells.

- **They fill the gaps** — the models have a value for **2020** and every year.
- **They are also lagged** — each model is a "hindcast" (it reconstructs the past), not a
  live feed.

> **How is a cell's area computed?** Each ¼-degree grid cell is about 27.75 km
> north-to-south. East-to-west it is narrower the farther north you go (the meridians
> converge toward the pole), so we shrink the east-west width by the cosine of the
> latitude. Multiplying the two gives the cell's area in km². Adding up the cold cells
> gives the cold-pool area. (The survey does the same kind of area sum on its
> interpolated map.)

---

## 4a. The two models — what they are, and how they compare

We show **two** regional ocean models side by side, on purpose. They are built by
different groups using different modelling systems, so when they *agree* we can be more
confident, and when they *disagree* that gap is an honest measure of uncertainty.

| | **Bering10K ROMS** | **CEFI MOM6 NEP** |
|---|---|---|
| Built by | NOAA PMEL + University of Washington (ACLIM program) | NOAA GFDL + PSL (CEFI initiative) |
| Modelling system | ROMS | MOM6 |
| Area it covers | Bering Sea / eastern shelf **only** (a regional specialist) | Whole Northeast Pacific — Baja California to the Chukchi (includes Gulf of Alaska + California Current) |
| Resolution | ~10 km | ~10 km |
| How often | Weekly | Monthly |
| Years available | **1970–2024** (cold-pool series shown: 1982–2024) | **1993–2024** (hindcast extends to mid-2025) |
| Beyond temperature | salinity, currents, sea ice, oxygen, nutrients, plankton | salinity, currents, sea ice, oxygen, nutrients, plankton, carbon/pH |
| Has a *forecast* version? | No public forecast feed | **Yes** — a seasonal forecast arm (the path to prediction) |

**What they have in common:** both are fine-resolution (~10 km) regional ocean models
that reconstruct the past from real weather, both reproduce the cold pool, both carry far
more than temperature, and both are recent-historical (lagged), not live.

**How they differ, and why it matters:**
- **Bering10K is the Bering specialist.** It was built and tuned specifically for this
  shelf and is the long-standing validated standard for the region.
- **MOM6 is the broad, multi-region model with a forecast arm.** It covers the whole
  Northeast Pacific and, crucially, has a **seasonal forecast** version — so it is the
  natural foundation for one day *predicting* the cold pool, not just reconstructing it.

**How good are they?** Compared the fair way (survey replication, §7), **both are
essentially unbiased** against the survey — Bering10K −0.16 °C, MOM6 +0.00 °C — and MOM6 is
actually a touch better at the point level (lower error, higher correlation). Neither is the
clear "winner," which is exactly why we show both: where they agree we trust the result;
where they disagree, that is the uncertainty signal. MOM6 additionally opens the door to
forecasting and to the rest of Alaska.

---

## 5. The other number: "mean bottom temperature"

Alongside the area, the page shows the **average bottom temperature** over the shelf, in
°C. This is simpler: it is just the typical seafloor temperature that year. A **low**
mean bottom temperature goes with a **big** cold pool (cold year); a **high** one goes
with a **small** cold pool (warm year). It is a useful companion to the area because it
does not depend on exactly where you draw the boundary of the survey — it is just "how
cold was the bottom, on average."

---

## 6. Reading the dashboard — two pages, four panels

The cold pool lives on **two pages**, each with its own threshold control (so you can,
say, view the observed index at ≤ 1 °C while comparing models at ≤ 2 °C).

### Page 1 — "Cold Pool: Observed & Validation"

**Panel A — Observed cold-pool index.** Top metrics: the selected year's cold-pool area
(km², with year-on-year change), that year as a % of the 1982–present mean, and mean bottom
temperature. Below them, two charts: the **area** (blue bars, one per year — note the big
cold years 1999/2010/2012, the **2017–2019 collapse**, and the **2020 gap** when there was
no survey) and the **mean bottom temperature** (red line, with a 2 °C reference). The
**threshold dropdown drives this panel.**

**Panel C — Survey-replicated validation** (appears when you pick model(s) to validate).
Each model's bottom temperature is sampled **at the survey's own haul locations and dates**
and compared to observed — the fair, literature-standard comparison. The skill table gives
each model's true **bias / RMSE / correlation**; this is where you read that both models are
essentially unbiased (Bering10K −0.16 °C, MOM6 +0.00 °C). Bottom-temperature based, so the
threshold control does not apply here.

### Page 2 — "Cold Pool: Model Comparison"

**Panel B1 — Full-shelf model view.** Each model's cold pool over its full ≤ 200 m shelf
(its *own* view), shown against observed: a standardized **area** panel (pattern) and an
absolute **bottom-temperature** panel. Here the MOM6 line sits ~1 °C warm — but this is the
full-shelf view, where the bigger-than-survey footprint inflates the warmth (§7); it is
*not* the model's true bias (that's Panel C). A pattern-agreement table gives each model's
correlation with the survey.

**Panel B2 — Model vs model, identical footing** (when both models are selected). The two
models on *exactly* the same basis — same ≤ 200 m shelf **and** same July monthly cadence,
no observations — isolating the genuine model-to-model difference. Three numbers report
inter-model correlation (area and bottom temp) and the mean temperature gap.

On this page the **threshold dropdown drives the area in both B1 and B2** (independently of
Page 1). At very cold thresholds (≤ 0 / −1 °C) many years have near-zero area, so the
pattern and correlations get noisier — the page notes this.

---

## 7. Understanding the comparison

### Why is the area shown "standardized (z-score)" in the comparison?
There is one honest wrinkle. The survey measures area over its **exact official survey
footprint**. The models measure area over a slightly **larger shelf region** (everything
shallower than 200 m). Because the models add up a bigger region, their **raw area numbers
come out larger** than the survey's — especially in warmer years. That is a difference in
*bookkeeping boundaries*, not a real disagreement.

To compare them **fairly**, the area panel shows each series **standardized** — a
"z-score." In plain terms: instead of plotting the raw km², we plot **how far each year
is above or below that series' own average, in standard steps.** This rescales all the
lines to the same footing, so you can see whether they **rise and fall together** — which
is the real question — without the boundary difference getting in the way. (The mean
bottom-temperature panel does *not* need this trick, so it is shown in real °C.)

### What does "Pearson r" mean?
**Pearson r** is a single number, between −1 and +1, that measures **how tightly two
things move together**:
- **+1.0** = they move in perfect lockstep (when one goes up, the other always goes up by
  a proportional amount).
- **0** = no relationship at all.
- **−1.0** = they move in perfect opposition.

The values on this page are very high — **0.90** for Bering10K and **0.97** for MOM6 (for
both area and bottom temperature). That means **both models reproduce the year-to-year ups
and downs of the real survey almost exactly.** (The exact number shifts a little with the
year range you select, because it is computed only over the years shown.)

### Three different comparisons (and which one is "fair")
This is the most important methodological point on the page. There are **three** distinct
ways the survey and the models relate, and they answer different questions — so they should
not be mixed up:

1. **Each model's own view** — the model's cold pool over the whole shelf (everything
   ≤ 200 m). This is the model's *product*: it can report a cold pool for places and years
   the survey never visited (e.g., 2020). It is *not* meant to equal the survey number.
2. **Model vs. model** — the two models compared to *each other*, on identical footing
   (same ≤ 200 m shelf, same monthly averaging). Where they agree we trust the result;
   where they disagree, that gap is the uncertainty signal.
3. **Model vs. survey ("survey replication")** — the **only fair way to score a model
   against the survey**: sample the model **at the survey's own haul locations and dates**,
   then compare to the observed bottom temperature there. This is what the research
   literature does (Kearney 2021; Seelanki et al. 2025), and it is how you get a *true*
   bias.

The trap — which our first attempt fell into — is comparing #1 against the survey: a
whole-shelf model average vs a survey-footprint observation. That is apples-to-oranges and
makes the models look artificially warm. The fix is comparison #3.

### What "bias" means, and the honest numbers
**Bias** is the average gap between model and observed bottom temperature (model − observed).
It differs from correlation: **correlation (r)** asks "do they rise and fall together?"
(shape); **bias** asks "is the model too warm or cold on average?" (level).

When we compare the models the **fair way (survey replication)**, both are excellent —
and MOM6's supposed "warm bias" essentially vanishes:

| Model | Survey-replicated bias | RMSE | r (point-level) |
|---|---|---|---|
| Bering10K ROMS | **−0.16 °C** (slightly cold) | 1.11 °C | 0.83 |
| CEFI MOM6 NEP | **+0.00 °C** (essentially unbiased) | 0.85 °C | 0.90 |

Both are within a few tenths of a degree of the survey; MOM6 is actually a touch *better* at
the point level (lower RMSE, higher correlation). These are the numbers shown in the
**survey-replicated validation** panel, and they are directly comparable to the published
literature.

### Then why did MOM6 look "+1.2 °C warm" earlier?
Because that figure came from the *wrong* comparison (#1 vs the survey). The +1.2 °C breaks
down into three roughly equal artifacts, none of which is a real model failure:

| Contribution to the old +1.2 °C | Size | How we know |
|---|---|---|
| Our ≤ 200 m shelf is **bigger than the survey footprint** + fixed July week ≠ exact survey dates (affects *both* models) | ~+0.4 °C | Bering10K measured the same way shows the same offset |
| Using a **whole-July average** instead of a single week (the shelf warms through summer) | ~+0.4 °C | *measured*: re-sampling Bering10K as a July monthly mean raised its offset from +0.4 to +0.8 °C |
| MOM6's warm bias **in the shallow nearshore**, which our big footprint over-weights but the survey under-samples | ~+0.4 °C | matches Seelanki et al. (2025): a "modest warm bias in the shallow region and a cold bias near the continental slope," attributed to vertical mixing |

The last row reconciles with the literature: MOM6's warm bias is *concentrated in shallow
water* and is partly cancelled by a cold bias near the slope — so over the survey footprint
the **average** bias is near zero (what survey replication shows), even though a whole-shelf
average that over-weights the nearshore looks warm. *(Citations: Seelanki et al. 2025,
doi:10.5194/gmd-18-7681-2025, §3.6; companion model description Drenkard et al. 2025,
doi:10.5194/gmd-18-5245-2025, which notes the scheme can "overmix some shelf regions subject
to strong tidal motions." See References.)*

### So what does the comparison tell us?
Compared the *correct* way, **both models are excellent, essentially-unbiased stand-ins for
the survey** — MOM6 marginally better at the point level, Bering10K marginally colder. They
reproduce the famous events (cold 2012, the 2017–2019 collapse), they **fill years the
survey missed** (like 2020), and — being two independent models — **where they agree we can
be confident, and where they disagree we get an honest measure of uncertainty.** That is the
foundation for everything we want to build on top of them.

---

## 8. Where the data comes from (sources, and exactly how we got it)

Everything on this page is built from **public, free** data — no login, no special
access, no data-sharing agreement. But the *three sources are obtained in two different
ways*, which is worth being precise about (it also matters when we describe our methods to
NOAA collaborators).

### A note on "how we get it": files vs. data services
- The **observed survey index** is a small published **file** we simply download (one file
  per release). It is produced by NOAA but **distributed through a code/data repository
  (GitHub) and archived on Zenodo** — *not* served from a noaa.gov data API.
- The **two models** are large datasets we read directly from **NOAA's own data servers**
  over a standard ocean-data service called **OPeNDAP/THREDDS**. Rather than downloading
  whole files, OPeNDAP lets us pull just the region, variable, and dates we need, on
  demand — effectively a data API. Both model servers are **on noaa.gov**.

### Source 1 — Observed cold-pool index (the survey)
- Producer: **NOAA Alaska Fisheries Science Center (AFSC)**, Groundfish Assessment Program.
- How we get it: **direct file download from GitHub** (the AFSC product repo); the citable
  archive is on Zenodo. *(There is also an R-package install route; we use the raw file.)*
- Repository: `afsc-gap-products/coldpool` — <https://github.com/afsc-gap-products/coldpool>
- Citable archive: Zenodo DOI **10.5281/zenodo.16915337** —
  <https://doi.org/10.5281/zenodo.16915337>
- Exact files: the `cold_pool_index` object (the annual index), and
  `index_hauls_temperature_data.csv` (the **per-haul** station temperatures — location,
  date, observed bottom temperature — used for survey replication, §7).
  <https://raw.githubusercontent.com/afsc-gap-products/coldpool/main/data/cold_pool_index.rda>
- Coverage: eastern Bering Sea shelf, **1982–2025** (no 2020). Index: one row per survey
  year; hauls: ~15,000 station records.

### Source 2 — Bering10K ROMS model (ACLIM)
- Producer: **NOAA PMEL + University of Washington**, Alaska Climate Integrated Modeling
  (ACLIM) program.
- How we get it: **OPeNDAP/THREDDS from a noaa.gov server** (open, no login).
- Server: NOAA PMEL THREDDS — <https://data.pmel.noaa.gov/aclim/thredds/>
- Exact dataset: the operational hindcast bottom-5m temperature collection
  (`B10K-K20_CORECFS`) —
  `https://data.pmel.noaa.gov/aclim/thredds/dodsC/B10K-K20_Level2_CORECFS_bottom5m_collection.nc`
- Coverage: Bering Sea / EBS, **weekly, 1970–2024** (refreshed a few times a year).

### Source 3 — CEFI MOM6 NEP model
- Producer: **NOAA GFDL + PSL**, Climate, Ecosystems & Fisheries Initiative (CEFI).
- How we get it: **OPeNDAP/THREDDS from a noaa.gov server** (open, no login; also
  mirrored on AWS S3 / Google Cloud).
- Portal: NOAA CEFI data portal — <https://psl.noaa.gov/cefi_portal/>
- Exact dataset: the Northeast Pacific hindcast bottom-temperature (`btm_temp`),
  monthly, regridded, on the PSL THREDDS server under
  `.../Projects/CEFI/regional_mom6/cefi_portal/northeast_pacific/...`
- Coverage: Northeast Pacific (Baja → Chukchi), **monthly, 1993–2024** (hindcast extends
  to mid-2025). A public seasonal-**forecast** version also exists.

### How the dashboard refreshes these (for maintainers)
- Observed index + per-haul data: `mhw-fetch-coldpool` →
  `data/raw/coldpool_index_observed.parquet`, `data/raw/coldpool_hauls_observed.parquet`
- Full-shelf model series: `mhw-build-coldpool-model --source {bering10k,mom6_nep}`
  (add `--monthly` for the matched-cadence series used by the model-vs-model panel)
- Survey-replicated validation: `mhw-build-survey-replicate --source {bering10k,mom6_nep}`
  → all saved under `data/derived/cold_pool/`
- Served by the dashboard API at `/v1/cold-pool/observed`,
  `/v1/cold-pool/modelled?source=...`, and `/v1/cold-pool/survey-replicate?source=...`.

---

## 9. Beyond temperature — other variables that matter for fish

The cold-pool pages are about **temperature**. But temperature is not the only thing
that decides whether fish and crab thrive, and — importantly — **all three of our sources
carry much more than temperature.** We have not yet built dashboard pages for these, but
the data is there and is a natural next step. Here is what each source offers and why it
matters biologically:

| Variable | Why it matters for fish & crab | Survey (observed) | Bering10K | MOM6 NEP |
|---|---|---|---|---|
| **Bottom & surface temperature** | habitat limits, the cold pool itself | ✓ (full record) | ✓ | ✓ |
| **Salinity** | identifies water masses; sets layering that drives the spring plankton bloom | ✓ (recent years only) | ✓ | ✓ |
| **Sea ice** | creates the cold pool; controls bloom timing | — | ✓ | ✓ |
| **Dissolved oxygen** | low oxygen stresses or excludes fish & crab | — | ✓ | ✓ |
| **Nutrients & plankton** | the base of the food web — prey for larvae (drives *recruitment*, i.e. how many young survive) | — | ✓ | ✓ |
| **Currents** | carry larvae to or away from nursery grounds (recruitment) | — | ✓ | ✓ |
| **Ocean acidification (pH / carbon)** | weakens crab shell formation — directly relevant to crab survival | — | — | ✓ (COBALT) |

A few honest points:
- The **survey** measures temperature for its whole record, **surface temperature**, and
  **bottom salinity only in recent years** (salinity sensors were added later). The wider
  AFSC bottom-trawl survey also records the actual fish and crab catch, but that is a
  separate product from the cold-pool index used here.
- The **models** are the richer source for these other fields: Bering10K carries a full
  biology module (oxygen, nutrients, plankton), and **MOM6 additionally carries ocean
  acidification / carbon chemistry** — which is especially relevant to crab.
- **Today the dashboard uses only temperature.** Salinity, oxygen, and the
  recruitment-relevant fields (nutrients, plankton, currents, pH) are available from the
  same sources and are a clear avenue for future pages.

---

## 10. Honest limitations (please read before quoting numbers)

- **No source is real-time.** The survey is annual and only available after each summer is
  processed; the models are hindcasts running through 2024. This page shows **recent
  history**, not today's ocean.
- **Two kinds of model number, don't mix them.** The *full-shelf* model view (≤ 200 m) is
  bigger than the survey footprint, so its raw area and bottom temperature run warm/large
  relative to the survey — that is a footprint difference, not model error. The **survey-
  replicated** numbers (model sampled at the hauls) are the fair, literature-comparable ones;
  use those to judge the models against the survey.
- **The full-shelf bottom-temperature panel shows MOM6 ~1 °C warm — that is an artifact**,
  not the model's true bias. Compared fairly (survey replication), MOM6 is essentially
  unbiased (+0.0 °C) and Bering10K slightly cold (−0.16 °C). See §7.
- **This page is the eastern Bering Sea only.** Bering10K only covers the Bering Sea;
  MOM6 covers the whole Northeast Pacific, so extending to the Gulf of Alaska is feasible
  with MOM6 but is future work.
- **Two models, not the last word.** Their close agreement with the survey and with each
  other is strong, but they share some common limitations (e.g. both depend on getting sea
  ice right), so agreement is reassuring, not proof.

---

## 11. Quick FAQ

**Q: Is a big cold pool good or bad?**
It depends who you are. It is good for snow crab (cold-water habitat) and is the
"normal," healthy state of this ecosystem. A shrinking cold pool signals warming, which
has been linked to fish moving north and to the snow-crab collapse.

**Q: Is the cold pool the same as sea ice?**
No, but they are linked. Winter **sea ice** is what *creates* the cold pool (by making
cold, salty, dense water). The cold pool is the cold bottom water that remains on the
seafloor through the following summer, after the ice is gone.

**Q: Why not just use the survey — why bother with models?**
The survey is the truth, but it is once a year, it has gaps (no 2020), and it can't tell
you about the future or fill in between stations. Models that we have **shown match the
survey** can fill gaps and are the stepping stone toward forecasting.

**Q: Why two models instead of one?**
Because they are built independently by different groups. When two independent models
*and* the real survey all agree, that is strong evidence; where the two models disagree,
that gap is an honest signal of how uncertain we should be. We also get each one's
strengths: Bering10K's accuracy here, and MOM6's broader coverage and forecast capability.

**Q: Doesn't MOM6 run ~1 °C warm? I see it high on the bottom-temperature chart.**
That high line is the **full-shelf view**, where our model footprint is bigger than the
survey's and over-weights warm nearshore water — an artifact, not a model error. Judged the
fair way (survey replication, model sampled at the actual survey hauls), MOM6 is essentially
**unbiased (+0.0 °C)**, with lower error and higher correlation than Bering10K (−0.16 °C).
See §7.

**Q: Why does the agreement number change with the year slider?**
It is calculated only over the years currently shown. The full-record values are about
0.90 for Bering10K (42 years) and 0.97 for MOM6 (31 years, since MOM6 starts in 1993).

**Q: What does "≤ 2 °C" actually feel like?**
2 °C is about 36 °F — just above freezing. The cold pool is water hovering right around
the freezing point of fresh water, kept liquid because it is salty.

**Q: Can I trust these numbers for a report?**
The observed survey index is an official NOAA product (cite the Zenodo DOI in References).
The model-derived numbers are our own calculation from public NOAA model output; quote the
**pattern agreement and mean bottom temperature**, and treat the models' absolute area as
indicative (see §10).

**Q: What exactly is a "shelf"?**
The shallow, gently sloping seafloor that extends from the coast before it plunges into the
deep ocean — like the shallow end of a pool before the drop-off. It is a *place* (a region
of seafloor), not a vertical column of water. We treat water shallower than 200 m as
"shelf." The cold pool only exists on this shelf. (See §2 for a diagram.)

**Q: If a shelf isn't a vertical thing, how do you measure "its" temperature?**
Location by location. At each spot on the shelf, "bottom temperature" is the temperature of
the thin layer of water touching the seafloor there — a sensor on the trawl gear for the
survey, the deepest model layer for the models. The cold pool is just the set of those
spots that read ≤ 2 °C, and its size is an **area** (km²).

**Q: Is the *survey's* cold pool shelf-only, or does it include deep water?**
Shelf-only — automatically. The survey vessels only trawl the shelf (their footprint is
~490,000 km²), so there is no deep water in the survey to begin with. The **models**, by
contrast, simulate the whole ocean including the deep basin, so we *deliberately* trim them
to water shallower than 200 m to match what the survey naturally measures. In all three,
"cold pool" means the same thing: shallow shelf seafloor with bottom water ≤ 2 °C.

**Q: How did you actually get the data — a file download, or an API? From NOAA.gov?**
Two different ways. The **observed survey index** is a small published *file* we download
from a **GitHub** repository (`afsc-gap-products/coldpool`), archived on **Zenodo** — it is
NOAA-produced but *not* served from a noaa.gov data API. The **two models** are read
directly from **NOAA's own data servers** (PMEL and PSL) over a standard ocean-data service
called **OPeNDAP/THREDDS**, which lets us pull just the region/variable/dates we need on
demand (effectively an API). See §8 for exact URLs.

**Q: Besides temperature, do these sources have salinity, oxygen, etc.?**
Yes — and far more. All three carry **salinity**; the two models also carry **sea ice,
dissolved oxygen, nutrients, plankton, and currents**, and MOM6 additionally carries
**ocean acidification / carbon chemistry** (relevant to crab shells). The survey records
temperature for its whole record but **salinity only in recent years**. Today the dashboard
uses temperature only; the rest is available for future pages (see §9).

**Q: How do the two models compare — what's the same, what's different?**
Both are ~10 km regional ocean models that reconstruct the past from real weather and carry
far more than temperature. **Bering10K** is the Bering-Sea specialist (1970–2024, weekly, no
public forecast). **MOM6 NEP** spans the whole Northeast Pacific (1993–2024, monthly, with a
public **seasonal-forecast** version — the path to prediction). Judged fairly, both are
essentially unbiased against the survey (MOM6 +0.0 °C, Bering10K −0.16 °C), and they agree
closely with each other. See §4a and §7.

**Q: Is there a published study about MOM6's bias on the Bering shelf?**
Yes. NOAA's evaluation (Seelanki et al. 2025, see References) reports "a modest warm bias in
the shallow region and a cold bias near the continental slope," attributed to vertical
mixing. The key point: those two biases *largely cancel over the survey footprint*, which is
why our survey-replicated MOM6 bias comes out near zero. The ~1.2 °C "warm" figure you might
have seen is a full-shelf-footprint artifact, not the model's true bias (§7).

---

## References

- **Kinney, J. C., Maslowski, W., Osinski, R., Lee, Y. J., Goethel, C., Frey, K., & Craig,
  A. (2022).** *On the variability of the Bering Sea Cold Pool and implications for the
  biophysical environment.* PLOS ONE. https://doi.org/10.1371/journal.pone.0266180
  — cold-pool definition (bottom water < 2 °C), sea-ice formation mechanism, and its role
  as a barrier between Arctic and subarctic fish.
- **Szuwalski, C. S., Aydin, K., Fedewa, E. J., Garber-Yonts, B., & Litzow, M. A. (2023).**
  *The collapse of eastern Bering Sea snow crab.* Science, 382, 306–310.
  https://doi.org/10.1126/science.adf6035 — links the snow-crab collapse to the 2018–2019
  marine heatwave.
- **Seelanki, V., Cheng, W., Stabeno, P. J., Hermann, A. J., Drenkard, E. J., Stock, C. A.,
  & Hedstrom, K. (2025).** *Evaluation of a coupled ocean and sea-ice model (MOM6-NEP10k)
  over the Bering Sea and its sensitivity to turbulence decay scales.* Geosci. Model Dev.,
  18, 7681–7705. https://doi.org/10.5194/gmd-18-7681-2025 — documents MOM6's modest warm
  shelf bias and the vertical-mixing mechanism.
- **Drenkard, E. J., Stock, C. A., Ross, A. C., et al. (2025).** *A regional
  physical–biogeochemical ocean model for marine resource applications in the Northeast
  Pacific (MOM6-COBALT-NEP10k v1.0).* Geosci. Model Dev., 18, 5245–5290.
  https://doi.org/10.5194/gmd-18-5245-2025 — the MOM6 NEP model description.
- **Alaska Department of Fish & Game** — 2022 and 2023 closures of the Bering Sea snow crab
  fishery (reopened 2024).

*Note on the snow-crab author list: Erin Fedewa (a co-author of Szuwalski et al. 2023) is
the AFSC scientist who first pointed us toward this work.*

*Data sources: NOAA AFSC cold-pool index (Zenodo 10.5281/zenodo.16915337, via GitHub
afsc-gap-products/coldpool); NOAA PMEL/UW Bering10K ROMS hindcast (ACLIM, PMEL THREDDS);
NOAA GFDL/PSL CEFI MOM6 NEP hindcast (PSL THREDDS / CEFI portal). This guide describes the
"Bottom Conditions — Eastern Bering Sea Cold Pool" page of the Marine Heatwave State
Dashboard.*
