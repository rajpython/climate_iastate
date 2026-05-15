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
# Files are deleted via `docker compose exec -T api rm -rf` because the
# zarr files are written by the api container (running as root inside the
# container) and the host's ubuntu user lacks permission to remove them
# directly. The data directory is bind-mounted into the container at
# /app/data, so the container's `rm` can reach the same files.
#
# This script is invoked automatically at the end of daily_refresh.sh, so
# in production it runs once per day immediately before the dashboard
# restart. A standalone weekly cron entry is therefore not needed.
#
# Manual invocation (e.g., for an ad-hoc cleanup):
#   bash scripts/cleanup_old_states.sh
#
# Dry-run mode (preview without deleting):
#   DRY_RUN=1 bash scripts/cleanup_old_states.sh

set -euo pipefail
export PATH="/usr/local/bin:/usr/bin:/bin:$PATH"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

STATES_DIR="data/derived/states_grid"
CONTAINER_STATES_DIR="/app/data/derived/states_grid"
CURRENT_YEAR="$(date -u +%Y)"
DRY_RUN="${DRY_RUN:-0}"

log() { printf '[%s] %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$*"; }

if [ ! -d "$STATES_DIR" ]; then
    log "No states directory at $STATES_DIR — nothing to do."
    exit 0
fi

log "=== Cleanup current-year state zarrs in $STATES_DIR (year=$CURRENT_YEAR, dry_run=$DRY_RUN) ==="

# Collect all obsolete zarr basenames across all regions, then batch the rm.
to_delete=()
for region in goa ebs nbs chukchi beaufort; do
    pattern="${STATES_DIR}/states_${region}_${CURRENT_YEAR}-01-01_*.zarr"
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
    log "[$region] keeping ${newest##*/}; queuing $((count - 1)) older snapshots for removal"
    while IFS= read -r old; do
        basename_old="${old##*/}"
        if [ "$DRY_RUN" = "1" ]; then
            log "  [dry-run] would rm -rf ${basename_old}"
        else
            to_delete+=("${CONTAINER_STATES_DIR}/${basename_old}")
            log "  queued ${basename_old}"
        fi
    done <<< "$(echo "$matching" | tail -n +2)"
done

if [ "$DRY_RUN" = "1" ]; then
    log "=== Dry-run complete. ==="
    exit 0
fi

if [ "${#to_delete[@]}" -eq 0 ]; then
    log "=== Nothing to delete. ==="
    exit 0
fi

# Single docker exec for all deletions — avoids the ~200ms-per-call overhead
# of one exec per file. The container runs `rm` as root so it can delete the
# zarr internals regardless of who created them.
log "Executing batch rm via docker compose exec -T api (${#to_delete[@]} paths) ..."
docker compose exec -T api rm -rf "${to_delete[@]}"

log "=== Cleanup complete. ${#to_delete[@]} obsolete zarrs were removed. ==="
