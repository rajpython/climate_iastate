#!/usr/bin/env bash
# daily_refresh.sh — fetch latest OISST, rebuild current-year states for all
# 5 regions, recompute risk scores, then restart Streamlit to clear its cache.
#
# Designed to run via cron on the production VM while Docker Compose is up:
#
#   # /etc/cron.d/mhw  (14:00 UTC = ~15 min after OISST daily publish)
#   0 14 * * * ubuntu cd /opt/mhw && bash scripts/daily_refresh.sh >> outputs/cron.log 2>&1
#
# The script delegates actual computation to the running `api` container so
# the same Python environment is always used.  Data is written through the
# read-write bind-mount (./data:/app/data:rw in docker-compose.yml).
#
# State engine note: for a single-day run, StateBuffer starts from zero, which
# may undercount event duration near the start of a new sequence.  Running from
# YEAR_START (Jan 1 of the current year) restores full continuity for the
# current calendar year at a modest extra cost (~seconds on cached SST).
# ---------------------------------------------------------------------------

set -euo pipefail
export PATH="/usr/local/bin:/usr/bin:/bin:$PATH"   # cron has minimal PATH

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

REGIONS=(goa ebs nbs chukchi beaufort)
TODAY="$(date -u +%Y-%m-%d)"
YEAR="$(date -u +%Y)"
YEAR_START="${YEAR}-01-01"
LOGDIR="${PROJECT_DIR}/outputs"

mkdir -p "$LOGDIR"

log() { printf '[%s] %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$*"; }

log "=== MHW daily refresh — ${TODAY} ==="

for region in "${REGIONS[@]}"; do
    log "[$region] Running state engine  ${YEAR_START} → ${TODAY} …"
    docker compose exec -T api \
        mhw-run-states --region "$region" --start "$YEAR_START" --end "$TODAY"

    log "[$region] Aggregating …"
    docker compose exec -T api \
        mhw-aggregate --region "$region" --start "$YEAR_START" --end "$TODAY"

    log "[$region] Recomputing risk scores …"
    docker compose exec -T api \
        mhw-compute-risk --region "$region"
done

log "Restarting dashboard (clears Streamlit @st.cache_data) …"
docker compose restart dashboard

log "=== Refresh complete. Log saved to ${LOGDIR}/cron.log ==="
