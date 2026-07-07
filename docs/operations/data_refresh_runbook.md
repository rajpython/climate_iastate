# Data refresh runbook

How every data layer on **marine.iastate.ai** gets refreshed: what runs **automatically**
on the production VM, what must be **rebuilt locally and rsynced** (too heavy for the 4 GB
box), and what is a **manual annual download** with no live API. Deployment facts (host, SSH,
mounts) live in the memory note `project-deployment-infra`; this file is the operational SOP.

Production VM: `ubuntu@3.137.98.10`, project dir `/opt/iastate-ai/projects/mhw`.
Cron jobs live in the **`ubuntu` user crontab** (`crontab -l`), **not** `/etc/cron.d/mhw`.
The `./data:/app/data` bind-mount is **`:rw` on the `api` service, `:ro` on `dashboard`** —
so all VM-side fetches run through the `api` container.

---

## 1. Automatic — VM cron (light, network-only)

These are pure downloads plus cheap recompute; safe on 4 GB. Each delegates to the running
`api` container and then `docker compose restart dashboard` to bust Streamlit's `@st.cache_data`.
Logs append to `outputs/cron.log`.

| Cron (UTC)        | Script                        | Refreshes                                                                 |
|-------------------|-------------------------------|---------------------------------------------------------------------------|
| `0 14 * * *`      | `scripts/daily_refresh.sh`    | OISST → current-year MHW states + aggregates + risk, all 12 ESR regions   |
| `0 15 1 * *`      | `scripts/monthly_indices_refresh.sh` | AO + PDO climate indices (`mhw-fetch-indices`, full-record defaults) |
| `0 16 2 * *`      | `scripts/bottom_state_refresh.sh`    | Observed cold-pool index (EBS/NBS) + GOA/AI bottom-temp + FOSS survey catch (8 species) |

**New-Year self-heal:** `daily_refresh.sh` runs the state engine with `--warmup-days 150`
**unconditionally every night** (`WARMUP_DAYS=150`, `daily_refresh.sh:65`). This replays a
150-day lead-in before Jan 1 so the Hobday `StateBuffer` is never cold-started, which is what
caused the Jan 2026 Aleutian-heatwave "gap". 150 days (not 60) guarantees exact event
*duration/cumulative-intensity* across a New-Year-straddling event, not just the headline area.
Because it rebuilds from scratch nightly, glitches, OISST prelim→final revisions, and bugfixes
auto-correct — the refresh is **self-healing / stateless by design** (see `project-cron-gap-backlog`).

To verify cron is actually installed and firing (run yourself — SSH to prod is a gated action):

```bash
ssh -i ~/.ssh/LightsailDefaultKey-us-east-2.pem ubuntu@3.137.98.10 \
  'crontab -l; echo ---; tail -20 /opt/iastate-ai/projects/mhw/outputs/cron.log'
```

---

## 2. Semi-automatic — local rebuild + rsync (heavy)

The bottom-state **model** layer (Bering10K ROMS + CEFI MOM6 NEP cold-pool / bottom-temp series
and survey-replicated validation) does an OPeNDAP pull + full-shelf curvilinear regrid that needs
more RAM than the VM has. Build it **on the Mac**, then rsync to the VM. Cadence: **~annual**, when
ACLIM (Bering10K K20/CORECFS) or CEFI MOM6 NEP publish a new hindcast year.

```bash
bash scripts/rebuild_bottom_models.sh            # build through current UTC year (prints the rsync cmd)
END=2025 bash scripts/rebuild_bottom_models.sh   # ...or through a specific year
```

Companion `scripts/rebuild_sst_esr.sh` rebuilds the full MHW SST history for the 12 ESR regions
(after a climatology/region change); `scripts/monthly_refresh.sh [YYYY-MM-DD]` extends the MHW
backfill locally to a target date. Escape hatch: resize Lightsail to ≥8 GB to move the model
rebuild into VM cron.

---

## 3. Manual annual download — AKFIN Economic SAFE (E2 groundfish + E3 crab)

**There is no live API for this layer.** AKFIN publishes the Economic SAFE only as interactive
Oracle-APEX reports (`reports.psmfc.org/akfin`), which export to CSV but have no stable scriptable
data URL (the E2 access probe confirmed this; an API request email was sent 2026-07-05, recorded in
`docs/outreach/`). Until AKFIN publishes a web-service endpoint, this is a hands-on annual refresh.
The Economic SAFE finalizes with a lag, so refresh once per year when the new vintage posts.

**Reports (22 CSVs total):**

- **Groundfish (GFSAFE):** `GFSAFE001`–`GFSAFE019`, **excluding 005 and 006** (never issued) = **17 reports**.
  `GFSAFE004` is split into two files (`2003-2009` + `2010-2024`) by an export size limit; the ingest
  merges them.
- **Crab (CRSAFE):** `CRSAFEEXEC01`, `CRSAFEEXEC02`, `CRSAFEEXEC03`, `CRSAFE004`, `CRSAFE005` = **5 reports**.

**Procedure:**

1. Log in to `reports.psmfc.org/akfin`, run each report above at its full year range, and **export CSV**.
2. Drop every CSV into `data/raw/akfin_exports/` (gitignored; the `.csv` is the ingest source — the
   `.numbers` twins Raj also saves are not machine-read).
3. Ingest to tidy parquet:

   ```bash
   .venv/bin/mhw-ingest-econ-safe          # → data/raw/econ_safe/*.parquet (one per report)
   ```

   Suppression/NA handling is automatic: AKFIN sentinels (`-9999`, `-8888`, any negative — all SAFE
   measures are non-negative) are blanked to `NaN`; band-string suppression columns are kept and
   annotated, not nulled.
4. Verify locally (`.venv/bin/pytest -k econ`), then deploy to the VM:

   ```bash
   rsync -av data/raw/akfin_exports/*.csv ubuntu@3.137.98.10:/opt/iastate-ai/projects/mhw/data/raw/akfin_exports/
   ssh -i ~/.ssh/LightsailDefaultKey-us-east-2.pem ubuntu@3.137.98.10 \
     'cd /opt/iastate-ai/projects/mhw && docker compose exec -T api mhw-ingest-econ-safe && docker compose restart dashboard'
   ```

   (The ingest must run inside the `api` container — that's the `:rw` mount; there is no `.venv` on the VM.)

---

## 4. Manual on demand — FOSS commercial landings (E1)

FOSS commercial landings (`mhw-fetch-landings-foss` → `data/raw/landings_foss_ak.parquet`, statewide
Alaska 1950–present) **is** a live REST fetch, but it is **not** wired into any cron job — refresh it
by hand when a new landings year posts (annual). On the VM: `docker compose exec -T api
mhw-fetch-landings-foss` then `docker compose restart dashboard`.

---

## Quick map: layer → refresh mechanism

| Layer                                   | Mechanism                        | Cadence  |
|-----------------------------------------|----------------------------------|----------|
| MHW / SST states, aggregates, risk      | VM cron (`daily_refresh.sh`)     | daily    |
| AO / PDO indices                        | VM cron (`monthly_indices_refresh.sh`) | monthly |
| Observed cold pool + bottom temp + catch| VM cron (`bottom_state_refresh.sh`) | monthly |
| Bottom-state **model** series           | local rebuild + rsync            | ~annual  |
| Economic SAFE groundfish (E2) + crab (E3)| **manual CSV download** + ingest | annual   |
| FOSS commercial landings (E1)           | manual live fetch                | annual   |
