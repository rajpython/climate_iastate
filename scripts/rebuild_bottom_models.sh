#!/usr/bin/env bash
# scripts/rebuild_bottom_models.sh — rebuild the MODELLED Bering bottom-state layers
# (Bering10K ROMS + CEFI MOM6 NEP cold-pool / bottom-temperature series + survey-replicated
# validation), then print the rsync command to push them to the production VM.
#
# RUN THIS LOCALLY (e.g. your Mac), NOT on the 4 GB Lightsail box: mhw-build-coldpool-model
# does an OPeNDAP pull + full-shelf curvilinear regrid that needs more RAM than the VM has.
# The hindcasts (ACLIM Bering10K K20/CORECFS, CEFI MOM6 NEP) publish ~annually, so run this
# when a new hindcast year lands, then rsync to the VM. The light observed/catch fetches
# refresh automatically on the VM (scripts/bottom_state_refresh.sh).
#
# Usage:
#   bash scripts/rebuild_bottom_models.sh                 # build through current UTC year
#   END=2025 bash scripts/rebuild_bottom_models.sh        # build through a specific year
#   VM=ubuntu@3.137.98.10 VM_DIR=/opt/iastate-ai/projects/mhw bash scripts/rebuild_bottom_models.sh
#
# Note: set END to the latest available hindcast year — the model build errors if END
# exceeds the data on the server (each source/region is guarded so one miss won't abort).
# ---------------------------------------------------------------------------

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

if [ -f .venv/bin/activate ]; then
    # shellcheck disable=SC1091
    source .venv/bin/activate
fi

SOURCES=(bering10k mom6_nep)
REGIONS=(ebs nbs slope)
END="${END:-$(date -u +%Y)}"
VM="${VM:-ubuntu@3.137.98.10}"
VM_DIR="${VM_DIR:-/opt/iastate-ai/projects/mhw}"

log() { printf '[%s] %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$*"; }

log "=== Rebuild modelled bottom-state — sources=[${SOURCES[*]}] regions=[${REGIONS[*]}] end=${END} ==="

for src in "${SOURCES[@]}"; do
    for region in "${REGIONS[@]}"; do
        log "[${src}/${region}] cold-pool model series (annual + monthly) …"
        mhw-build-coldpool-model --source "${src}" --region "${region}" --end "${END}" \
            || log "WARN: model build failed for ${src}/${region} (continuing)"
        mhw-build-coldpool-model --source "${src}" --region "${region}" --end "${END}" --monthly \
            || log "WARN: monthly model build failed for ${src}/${region} (continuing)"
        log "[${src}/${region}] survey-replicated validation …"
        mhw-build-survey-replicate --source "${src}" --region "${region}" \
            || log "WARN: survey replicate failed for ${src}/${region} (continuing)"
    done
done

log "=== Build complete. Push the rebuilt model data to the VM with: ==="
cat <<EOF

  rsync -avz --progress \\
    "${PROJECT_DIR}/data/derived/cold_pool/" \\
    ${VM}:${VM_DIR}/data/derived/cold_pool/

EOF
