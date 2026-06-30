#!/usr/bin/env bash
# scripts/rebuild_sst_esr.sh — ONE-TIME rebuild of the SST/MHW pipeline onto the ESR ecosystem
# regions (Bering: ebs=combined, sebs, nbs; GOA: goa=combined, wgoa, egoa). Chukchi/Beaufort are
# unchanged and NOT rebuilt here. Run LOCALLY (heavy: OISST fetch + 44-yr states per region),
# then rsync data/derived + data/raw OISST to the VM.
#
# IMPORTANT: the OISST yearly cache (data/raw/oisst_<id>_<year>.nc) is keyed by region id, not
# extent — so the reshaped `goa`/`nbs` and repurposed `ebs` (now combined) must drop their stale
# box-era caches first. New ids (sebs/wgoa/egoa) fetch fresh; chukchi/beaufort caches are kept.
#
# Usage: bash scripts/rebuild_sst_esr.sh [END_DATE]
# ---------------------------------------------------------------------------
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$(dirname "$SCRIPT_DIR")"
[ -f .venv/bin/activate ] && source .venv/bin/activate

END="${1:-$(date -u +%Y-%m-%d)}"
# Regions to (re)build. Override to re-run a subset, e.g. REGIONS="nbs goa ebs".
REGIONS="${REGIONS:-egoa wgoa sebs nbs goa ebs ai ai_west ai_central ai_east}"
# Drop stale box-era OISST caches for reshaped/repurposed ids ONLY on a full run (set
# DROP_OISST=0 when re-running a subset so the partially-fetched new-grid cache is reused).
DROP_OISST="${DROP_OISST:-1}"
log() { printf '[%s] %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$*"; }

if [ "$DROP_OISST" = "1" ]; then
    log "Dropping stale box-era OISST caches for reshaped/repurposed ids (goa, nbs, ebs) …"
    rm -f data/raw/oisst_goa_*.nc data/raw/oisst_nbs_*.nc data/raw/oisst_ebs_*.nc
fi

log "=== SST ESR rebuild — regions=[${REGIONS}] end=${END} ==="
for r in ${REGIONS}; do
    # Clean per-region derived artifacts so the build is fresh on the new ESR grid (prevents
    # mixing old box-grid states zarr / merging stale aggregate rows).
    log "[$r] cleaning stale derived artifacts …"
    rm -rf data/derived/states_grid/states_${r}_*.zarr
    rm -f  data/derived/aggregates_region/region_daily_${r}.parquet data/derived/risk/risk_${r}.parquet
    log "[$r] climatology (1991–2020 baseline) …"
    mhw-build-climatology --region "$r" || { log "FAIL climatology $r"; continue; }
    log "[$r] backfill states + aggregate + risk (1982→${END}) …"
    ok=0
    for attempt in 1 2 3; do   # ERDDAP can throw transient NetCDF I/O failures under load; cache makes retries cheap
        if mhw-backfill --region "$r" --start 1982-01-01 --end "$END"; then ok=1; break; fi
        log "[$r] backfill attempt $attempt failed — retrying after 60s …"; sleep 60
    done
    [ "$ok" = "1" ] && log "[$r] done." || log "FAIL backfill $r (after 3 attempts)"
done
log "=== SST ESR rebuild complete. Rsync data/raw/oisst_*.nc + data/derived/ to the VM. ==="
