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

# ESR ecosystem regions (combined areas + subareas) + Arctic; AI chain crosses the dateline.
REGIONS=(ebs sebs nbs goa wgoa egoa ai ai_west ai_central ai_east chukchi beaufort)
TODAY="$(date -u +%Y-%m-%d)"
YEAR="$(date -u +%Y)"
YEAR_START="${YEAR}-01-01"
LOGDIR="${PROJECT_DIR}/outputs"

mkdir -p "$LOGDIR"

log() { printf '[%s] %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$*"; }

# --- Warm-start guard (fixes the New-Year cold-start gap) ------------------
# The state engine confirms a MHW only after the Hobday minimum duration
# (consecutive hot days). Running from Jan 1 with an empty buffer cannot see a
# MHW that was already ongoing across the New Year, so its first ~5 days read
# area_frac 0 for the whole year (e.g. the Jan 1–4 2026 W. Aleutian event).
# --warmup-days processes a lead window before YEAR_START so the buffer is
# already locked onto any straddling event; the lead days are dropped from the
# output, so the saved zarr and aggregates still cover only the current year.
WARMUP_DAYS=60

log "=== MHW daily refresh — ${TODAY} ==="

for region in "${REGIONS[@]}"; do
    log "[$region] Running state engine  ${YEAR_START} → ${TODAY} (warm-start ${WARMUP_DAYS}d) …"
    docker compose exec -T api \
        mhw-run-states --region "$region" --start "$YEAR_START" --end "$TODAY" --warmup-days "$WARMUP_DAYS"

    log "[$region] Aggregating …"
    docker compose exec -T api \
        mhw-aggregate --region "$region" --start "$YEAR_START" --end "$TODAY"

    log "[$region] Recomputing risk scores …"
    docker compose exec -T api \
        mhw-compute-risk --region "$region"
done

# Prune yesterday's daily-snapshot state zarrs so the Live MHW Map dropdown
# always shows exactly one current-year zarr per region. Non-fatal — if the
# cleanup somehow errors, still proceed to the dashboard restart below.
log "Cleaning up obsolete daily-snapshot state zarrs …"
bash "${SCRIPT_DIR}/cleanup_old_states.sh" \
    || log "WARNING: cleanup_old_states.sh exited non-zero (continuing)"

log "Restarting dashboard (clears Streamlit @st.cache_data) …"
docker compose restart dashboard

log "=== Refresh complete. Log saved to ${LOGDIR}/cron.log ==="
