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
#
# Why 150 (not 60): the run-up must exceed the age of any heatwave still ongoing
# at Jan 1, or that event's *duration* (Dbar) and *cumulative intensity* (Cbar)
# are undercounted early in the year. Coverage (area_frac) and intensity (Ibar)
# are exact at any warmup ≥ the ~5-day Hobday confirmation, but duration needs
# the full history back to the event's start. 150 days reaches early August of
# the prior year — longer than any realistic single continuous MHW across the
# New Year in these waters — so all metrics are effectively exact. Cost is only
# a few extra seconds of cached-SST replay per run. The pipeline stays stateless
# and self-healing: it rebuilds Jan 1 -> today every run, so crashes, skipped
# days, and NOAA's revisions to recent OISST all self-correct on the next run.
#
# Exact-but-stateful alternative (not used): freeze the StateBuffer snapshot at
# Dec 31 once the prior December finalizes (~mid/late Jan) and seed the year from
# it via save_buffer/load_buffer (src/mhw/states/update_states.py). That makes
# duration exact even for events running continuously for many months across the
# boundary, at the cost of one snapshot file per region and a "seed only after
# December is final" rule. Prefer that only if such multi-month straddling events
# need provably-exact duration; the warmup below covers every realistic case.
WARMUP_DAYS=150

log "=== MHW daily refresh — ${TODAY} ==="

# --- Prior-year re-finalization (once per year, after ~Jan 15) --------------
# OISST publishes each day as *preliminary* and finalizes it ~2 weeks later, so
# when the year turns, the stored record for late December was computed from
# preliminary values (and the Dec 30-31 tail wasn't published at all yet).
# year_cache_stale (mhw.climatology.build_mu_theta) re-pulls the prior-year
# cache once after Jan 15; this block then recomputes the FULL prior year so
# every sealed artifact is finalized consistently:
#   - the archive grid zarr states_<r>_<Y>-01-01_<Y>-12-31.zarr (what the Live
#     MHW Map's year dropdown renders) is overwritten by the finalized run —
#     recomputing only December would finalize the parquet but leave the
#     archived December *maps* preliminary;
#   - the full-year aggregate upsert guarantees parquet == archive zarr
#     (Jan-Nov rows rewrite identically; December rows pick up the finals).
# After this block the prior year is permanently sealed: daily runs only touch
# the current year, monthly refresh only extends forward, and the prior-year
# cache staleness window closes mid-March. The marker file makes it run once
# per year (dynamic PRIOR_YEAR -> repeats automatically every January);
# failures are non-fatal and retried the next day so the live current-year
# refresh below always proceeds. cleanup_old_states.sh only prunes
# current-year snapshots, so the refreshed archive zarr is never touched.
PRIOR_YEAR=$((YEAR - 1))
SEAL_MARKER="${LOGDIR}/.refinalized_${PRIOR_YEAR}"
MMDD="$(date -u +%m%d)"
if [[ "$MMDD" > "0114" && "$MMDD" < "0316" && ! -f "$SEAL_MARKER" ]]; then
    log "=== Re-finalizing year ${PRIOR_YEAR} from final OISST ==="
    if (
        set -euo pipefail
        for region in "${REGIONS[@]}"; do
            log "[$region] ${PRIOR_YEAR} full-year states (warm-start ${WARMUP_DAYS}d) …"
            docker compose exec -T api \
                mhw-run-states --region "$region" \
                    --start "${PRIOR_YEAR}-01-01" --end "${PRIOR_YEAR}-12-31" \
                    --warmup-days "$WARMUP_DAYS"
            log "[$region] ${PRIOR_YEAR} full-year aggregates …"
            docker compose exec -T api \
                mhw-aggregate --region "$region" \
                    --start "${PRIOR_YEAR}-01-01" --end "${PRIOR_YEAR}-12-31"
        done
    ); then
        touch "$SEAL_MARKER"
        log "=== Year ${PRIOR_YEAR} sealed (marker: ${SEAL_MARKER}) ==="
    else
        log "WARNING: prior-year re-finalization failed — will retry tomorrow"
    fi
fi

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
