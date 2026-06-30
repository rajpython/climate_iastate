#!/usr/bin/env bash
# scripts/bottom_state_refresh.sh — refresh the OBSERVED Bering bottom-state layers
# (AFSC cold-pool index + survey hauls, FOSS survey catch) on the production VM, then
# bust the Streamlit cache. Light and network-only — safe on the 4 GB Lightsail box.
#
# These sources are annual/lagged (AFSC summer bottom-trawl survey + FOSS catch), so a
# MONTHLY cadence picks up each year's release promptly without reprocessing unchanged
# data. The HEAVY model rebuild (mhw-build-coldpool-model + survey-replicate: OPeNDAP +
# full-shelf curvilinear regrid) is NOT here — it needs more RAM than the VM has and runs
# locally + rsync (see scripts/rebuild_bottom_models.sh).
#
# Delegates to the running `api` container (same Python env), writing through the rw
# bind-mount (./data:/app/data:rw). Companion to daily_refresh.sh / monthly_indices_refresh.sh.
#
# Cron registration (add alongside the others in /etc/cron.d/mhw):
#
#   # 16:00 UTC on the 2nd of each month (after the monthly indices refresh)
#   0 16 2 * * ubuntu cd /opt/iastate-ai/projects/mhw && bash scripts/bottom_state_refresh.sh >> outputs/cron.log 2>&1
#
# Manual invocation:
#   bash scripts/bottom_state_refresh.sh
# ---------------------------------------------------------------------------

set -euo pipefail
export PATH="/usr/local/bin:/usr/bin:/bin:$PATH"   # cron has a minimal PATH

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

# Observed survey products with an annual release: cold pool (EBS/NBS) + the packaged
# mean-bottom-temperature index (GOA/AI). The slope survey is discontinued (static) and the
# Arctic has no survey, so neither is re-fetched. Catch is the 8-species union across groups,
# fetched over every survey at once (single fetch per species avoids clobbering shared species).
OBSERVED_REGIONS=(sebs nbs goa wgoa egoa ai ai_west ai_central ai_east)
CATCH_SPECIES=(68580 69322 21720 21740 10110 20510 30060 21921)
# 68580 snow crab · 69322 red king · 21720 cod · 21740 pollock · 10110 arrowtooth
# · 20510 sablefish · 30060 Pacific ocean perch · 21921 Atka mackerel
CATCH_SRVYS=(EBS NBS BSS GOA AI)

log() { printf '[%s] %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$*"; }

log "=== Bering bottom-state observed refresh ==="

for region in "${OBSERVED_REGIONS[@]}"; do
    log "[observed] fetching survey index + hauls — ${region} …"
    docker compose exec -T api mhw-fetch-coldpool --region "${region}" \
        || log "WARN: observed fetch failed for ${region} (continuing)"
done

for sp in "${CATCH_SPECIES[@]}"; do
    log "[catch] fetching FOSS catch — species ${sp} …"
    docker compose exec -T api mhw-fetch-catch --species "${sp}" --regions "${CATCH_SRVYS[@]}" \
        || log "WARN: catch fetch failed for species ${sp} (continuing)"
done

log "Restarting dashboard to bust Streamlit @st.cache_data …"
docker compose restart dashboard

log "=== Refresh complete ==="
