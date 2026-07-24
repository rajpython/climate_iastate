#!/usr/bin/env bash
# scripts/monthly_refresh.sh — extend MHW backfill to a target end date.
#
# Auto-detects the latest date in the existing GOA region_daily parquet and
# runs the state engine, aggregation, and risk pipeline for the gap from
# (latest_date + 1) through the target end date (default: today UTC).
# Also refreshes AO and PDO indices unconditionally.
#
# Usage:
#   bash scripts/monthly_refresh.sh                 # extend through today UTC
#   bash scripts/monthly_refresh.sh 2026-06-30      # extend through a specific date
#
# Pre-flight:
#   - Stop the local Streamlit dashboard first (avoids file lock contention).
#   - Requires network access to NOAA ERDDAP (OISST) and NOAA CPC/PSL (AO/PDO).
#   - Uses .venv if present; otherwise relies on whatever Python is on PATH.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

if [ -f .venv/bin/activate ]; then
    # shellcheck disable=SC1091
    source .venv/bin/activate
fi

# ESR regions: Bering ebs(combined)+sebs+nbs, GOA goa(combined)+wgoa+egoa,
# Aleutians ai(combined)+W/C/E, + Arctic boxes.
REGIONS=(ebs sebs nbs goa wgoa egoa ai ai_west ai_central ai_east chukchi beaufort)
TARGET_END="${1:-$(date -u +%Y-%m-%d)}"

# Latest date already in the canonical GOA parquet
LATEST=$(python -c "
import pandas as pd
df = pd.read_parquet('data/derived/aggregates_region/region_daily_goa.parquet')
print(pd.to_datetime(df['date']).max().strftime('%Y-%m-%d'))
")

# Start from the day after that
START=$(python -c "
from datetime import datetime, timedelta
d = datetime.strptime('$LATEST', '%Y-%m-%d') + timedelta(days=1)
print(d.strftime('%Y-%m-%d'))
")

if [[ "$START" > "$TARGET_END" ]]; then
    echo "Already up to date through $LATEST (target was $TARGET_END). Nothing to do."
    exit 0
fi

log() { printf '[%s] %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$*"; }

log "=== MHW monthly refresh: $START → $TARGET_END ==="

_run_parallel() {
    local stage="$1" cmd_template="$2" success_grep="$3"
    log "[$stage] starting (parallel across ${#REGIONS[@]} regions)..."
    for r in "${REGIONS[@]}"; do
        eval "${cmd_template//__REGION__/$r}" > "/tmp/mhw_${stage}_${r}.log" 2>&1 &
    done
    wait
    for r in "${REGIONS[@]}"; do
        if ! grep -q "$success_grep" "/tmp/mhw_${stage}_${r}.log"; then
            log "FAILED: $stage for $r — see /tmp/mhw_${stage}_${r}.log"
            tail -20 "/tmp/mhw_${stage}_${r}.log"
            exit 1
        fi
        log "  $r ok"
    done
}

_run_parallel "states" \
    "mhw-run-states --region __REGION__ --start $START --end $TARGET_END" \
    "Done\."

_run_parallel "aggregate" \
    "mhw-aggregate --region __REGION__ --start $START --end $TARGET_END" \
    "Saved"

_run_parallel "risk" \
    "mhw-compute-risk --region __REGION__" \
    "Saved"

log "[indices] refreshing AO (~1950), PDO (1854) and NPI (Aleutian Low proxy, 1948)..."
# Pass --ao-years/--pdo-years/--npi-years explicitly (with values that exceed
# available history) so the refresh is robust even if the upstream defaults change.
# NPI (NOAA PSL np.data) updates more slowly than AO/PDO — it may trail by ~1 yr.
mhw-fetch-indices --ao-years 100 --pdo-years 200 --npi-years 100

log "=== Refresh complete. Data now extends through $TARGET_END ==="
