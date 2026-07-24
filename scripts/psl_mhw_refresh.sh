#!/usr/bin/env bash
# scripts/psl_mhw_refresh.sh — refresh the NOAA PSL marine-heatwave FORECAST layer
# on the production VM, then bust the Streamlit cache. Runs DAILY but is cheap: it
# HEADs the PSL files and downloads only when they changed (they refresh ~monthly,
# sometimes mid-month), so on most days it transfers nothing and exits early.
#
# When PSL does update, the download is ~0.75 GB (the two *_latest.nc forecasts)
# and the rebuild lazily slices the Alaska window — both fit the 4 GB Lightsail box.
#
# The HEAVY one-time SEDI skill build (mhw-build-psl-mhw --sedi from the 2×1.1 GB
# 1991-2020 hindcast) is NOT here: it is built locally and rsynced (like
# scripts/rebuild_bottom_models.sh). This script never fetches the hindcast files
# and never passes --sedi.
#
# Delegates to the running `api` container (same Python env), writing through the rw
# bind-mount (./data:/app/data:rw). Companion to daily_refresh.sh.
#
# Cron registration (ubuntu crontab — see docs/operations/data_refresh_runbook.md):
#
#   # 15:30 UTC daily (after the 14:00 daily_refresh)
#   30 15 * * * cd /opt/iastate-ai/projects/mhw && bash scripts/psl_mhw_refresh.sh >> outputs/cron.log 2>&1
#
# Manual invocation:
#   bash scripts/psl_mhw_refresh.sh
# ---------------------------------------------------------------------------

set -euo pipefail
export PATH="/usr/local/bin:/usr/bin:/bin:$PATH"   # cron has a minimal PATH

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

log() { printf '[%s] %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$*"; }

log "=== PSL marine-heatwave forecast refresh ==="

# Conditional fetch. Exit 3 = nothing changed → skip the rebuild; 0 = something
# downloaded; anything else = a real error (propagate). `|| rc=$?` keeps set -e happy.
rc=0
docker compose exec -T api mhw-fetch-psl-mhw || rc=$?
if [ "$rc" -eq 3 ]; then
    log "PSL files unchanged — skipping rebuild."
    exit 0
elif [ "$rc" -ne 0 ]; then
    log "ERROR: fetch failed (rc=$rc)."
    exit "$rc"
fi

log "PSL files updated — rebuilding Alaska derived artifacts …"
docker compose exec -T api mhw-build-psl-mhw --flavor both

log "Restarting dashboard to bust Streamlit @st.cache_data …"
docker compose restart dashboard

log "=== PSL forecast refresh complete ==="
