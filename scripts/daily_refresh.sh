#!/usr/bin/env bash
# daily_refresh.sh — fetch the latest OISST source files, then restart Streamlit.
#
# HEATWAVE RECORD PAUSED (Col. Raj ruling 1, 12 Oct 2026; board plan addendum 04).
# The board shows the sealed record vintage #7 (D1), certified 1982-01-01 … 2026-08-31, staged
# read-only under data/record/mhw-d1/. No validated daily extension exists yet, so this job no
# longer runs the state engine, aggregation, risk scoring, the January–March prior-year
# re-finalization or the state clean-up. It only keeps collecting the NCEI per-day OISST source
# files (as ruled) and restarts the dashboard. The daily extension is a separate commission; the
# previous full script is in git history (commit 7403367).
#
# Designed to run via cron on the production VM while Docker Compose is up:
#
#   # /etc/cron.d/mhw  (14:00 UTC = ~15 min after OISST daily publish)
#   0 14 * * * ubuntu cd /opt/mhw && bash scripts/daily_refresh.sh >> outputs/cron.log 2>&1
#
# The fetch runs in the `api` container so the same Python environment is always used; it writes
# only the OISST cache under data/raw/ through the read-write bind-mount.
# ---------------------------------------------------------------------------

set -euo pipefail
export PATH="/usr/local/bin:/usr/bin:/bin:$PATH"   # cron has minimal PATH

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

TODAY="$(date -u +%Y-%m-%d)"
LOGDIR="${PROJECT_DIR}/outputs"

mkdir -p "$LOGDIR"

log() { printf '[%s] %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$*"; }

log "=== MHW daily refresh — ${TODAY} ==="

# OISST inputs come from NCEI per-day files, appended to the cache (final, else preliminary;
# preliminary days upgraded to final when published). The cache is the authority: nothing is
# ever re-pulled from the PFEG aggregate, which is incomplete and serves superseded files.
log "Updating OISST inputs from NCEI per-day files …"
docker compose exec -T api mhw-update-ncei
END_DAY="$(docker compose exec -T api mhw-update-ncei --print-last-day | tr -d '\r')"
log "OISST cache holds every zone through ${END_DAY}. Heatwave record paused at 2026-08-31 (vintage #7, D1); no states, aggregates or risk are written."

log "Restarting dashboard (clears Streamlit @st.cache_data) …"
docker compose restart dashboard

log "=== Refresh complete. Log saved to ${LOGDIR}/cron.log ==="
