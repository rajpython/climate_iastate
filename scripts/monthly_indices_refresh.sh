#!/usr/bin/env bash
# scripts/monthly_indices_refresh.sh — re-fetch AO and PDO climate indices
# under the dashboard's full-record defaults, then bust the Streamlit cache.
#
# Designed to run via cron on the production VM while Docker Compose is up.
# AO publishes daily and PDO publishes monthly; a monthly fetch keeps both
# current enough for the Regime Analysis tab and the Predictability panel.
#
# Companion to `daily_refresh.sh`, which handles SST-derived state/agg/risk
# but does NOT touch the AO/PDO parquet files.
#
# Cron registration (add alongside the daily refresh in /etc/cron.d/mhw):
#
#   # 15:00 UTC on the 1st of each month — one hour after the daily refresh
#   0 15 1 * * ubuntu cd /opt/iastate-ai/projects/mhw && bash scripts/monthly_indices_refresh.sh >> outputs/cron.log 2>&1
#
# Manual invocation (e.g. after a config change):
#
#   bash scripts/monthly_indices_refresh.sh

set -euo pipefail
export PATH="/usr/local/bin:/usr/bin:/bin:$PATH"   # cron has a minimal PATH

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

log() { printf '[%s] %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$*"; }

log "=== AO/PDO indices refresh ==="

# -T disables pseudo-TTY allocation, which is required when running from cron.
# mhw-fetch-indices uses full-record defaults (~1950 for AO, 1870 for PDO).
docker compose exec -T api mhw-fetch-indices

log "Restarting dashboard to bust Streamlit @st.cache_data …"
docker compose restart dashboard

log "=== Refresh complete ==="
