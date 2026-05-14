#!/usr/bin/env bash
# scripts/cleanup_old_states.sh — remove obsolete daily-refresh state zarrs.
#
# daily_refresh.sh creates a new zarr per region per day for the current year:
#   states_<region>_<YEAR>-01-01_<YYYY-MM-DD>.zarr
# Each day's zarr fully supersedes the prior day's (same year, same region),
# so older snapshots are obsolete the moment a newer one is written.
#
# This script keeps the newest current-year zarr per region and deletes the
# older daily snapshots. Closed-year archive zarrs — e.g.,
# states_<region>_2024-01-01_2024-12-31.zarr — are NEVER touched, because
# the script only looks at zarrs whose start date matches the current year.
#
# Cron registration (weekly Sunday at 16:00 UTC, 2 hours after the daily
# refresh and 1 hour after the monthly indices refresh — no conflicts):
#
#   0 16 * * 0 cd /opt/iastate-ai/projects/mhw && bash scripts/cleanup_old_states.sh >> outputs/cron.log 2>&1
#
# Dry-run mode (preview without deleting):
#   DRY_RUN=1 bash scripts/cleanup_old_states.sh

set -euo pipefail
export PATH="/usr/local/bin:/usr/bin:/bin:$PATH"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

STATES_DIR="data/derived/states_grid"
CURRENT_YEAR="$(date -u +%Y)"
DRY_RUN="${DRY_RUN:-0}"

log() { printf '[%s] %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$*"; }

if [ ! -d "$STATES_DIR" ]; then
    log "No states directory at $STATES_DIR — nothing to do."
    exit 0
fi

log "=== Cleanup current-year state zarrs in $STATES_DIR (year=$CURRENT_YEAR, dry_run=$DRY_RUN) ==="

cd "$STATES_DIR"
total_deleted=0

for region in goa ebs nbs chukchi beaufort; do
    pattern="states_${region}_${CURRENT_YEAR}-01-01_*.zarr"
    # shellcheck disable=SC2086
    matching=$(ls -1 -d $pattern 2>/dev/null | sort -r || true)
    if [ -z "$matching" ]; then
        continue
    fi
    count=$(echo "$matching" | wc -l)
    if [ "$count" -le 1 ]; then
        log "[$region] only ${count} zarr — nothing to remove"
        continue
    fi
    newest=$(echo "$matching" | head -n 1)
    log "[$region] keeping ${newest}; removing $((count - 1)) older daily snapshots"
    while IFS= read -r old; do
        if [ "$DRY_RUN" = "1" ]; then
            log "  [dry-run] would rm -rf $old"
        else
            rm -rf "$old"
            log "  rm -rf $old"
        fi
        total_deleted=$((total_deleted + 1))
    done <<< "$(echo "$matching" | tail -n +2)"
done

if [ "$DRY_RUN" = "1" ]; then
    log "=== Dry-run complete. ${total_deleted} obsolete zarrs would be removed. ==="
else
    log "=== Cleanup complete. ${total_deleted} obsolete zarrs were removed. ==="
fi
