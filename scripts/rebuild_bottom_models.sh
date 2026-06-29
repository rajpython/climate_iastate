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

END="${END:-$(date -u +%Y)}"
VM="${VM:-ubuntu@3.137.98.10}"
VM_DIR="${VM_DIR:-/opt/iastate-ai/projects/mhw}"

# Region coverage by model + product (mirrors mhw.bottom.regions descriptors):
#   * Bering (ebs/nbs/slope): BOTH models; build the monthly field too (the model-vs-model
#     panel needs identical monthly cadence) + survey-replicated validation.
#   * GOA/AI: MOM6 only (Bering10K is out of domain); annual + survey-replicate (FOSS hauls).
#   * Arctic (chukchi/beaufort): MOM6 only, MODEL-ONLY (no survey → no replicate).
#   * Cold-pool regions (ebs/nbs): also build the apples-to-apples KRIGED area.
#   * OISST regions (ebs/nbs/goa/chukchi/beaufort): summer shelf-surface diagnostic.
BERING_REGIONS=(ebs nbs slope)          # both models + monthly + replicate
MOM6_SURVEY_REGIONS=(goa ai)            # mom6 only, annual + replicate
MOM6_MODELONLY_REGIONS=(chukchi beaufort)   # mom6 only, annual only
COLDPOOL_REGIONS=(ebs nbs)              # kriged apples-to-apples area
OISST_REGIONS=(ebs nbs goa chukchi beaufort)  # shelf-surface diagnostic

log() { printf '[%s] %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$*"; }

log "=== Rebuild modelled bottom-state — end=${END} ==="

# --- Bering: both models, annual + monthly + survey replicate ---
for region in "${BERING_REGIONS[@]}"; do
    for src in bering10k mom6_nep; do
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

# --- GOA/AI: MOM6 only, annual + survey replicate ---
for region in "${MOM6_SURVEY_REGIONS[@]}"; do
    log "[mom6_nep/${region}] cold-pool model series (annual) …"
    mhw-build-coldpool-model --source mom6_nep --region "${region}" --end "${END}" \
        || log "WARN: model build failed for mom6_nep/${region} (continuing)"
    log "[mom6_nep/${region}] survey-replicated validation …"
    mhw-build-survey-replicate --source mom6_nep --region "${region}" \
        || log "WARN: survey replicate failed for mom6_nep/${region} (continuing)"
done

# --- Arctic: MOM6 only, model-only (no survey) ---
for region in "${MOM6_MODELONLY_REGIONS[@]}"; do
    log "[mom6_nep/${region}] cold-pool model series (annual, model-only) …"
    mhw-build-coldpool-model --source mom6_nep --region "${region}" --end "${END}" \
        || log "WARN: model build failed for mom6_nep/${region} (continuing)"
done

# --- Apples-to-apples KRIGED cold-pool area (ebs/nbs, both models) ---
for region in "${COLDPOOL_REGIONS[@]}"; do
    for src in bering10k mom6_nep; do
        log "[${src}/${region}] kriged cold-pool area …"
        mhw-build-kriged-area --source "${src}" --region "${region}" \
            || log "WARN: kriged-area build failed for ${src}/${region} (continuing)"
    done
done

# --- Summer shelf-surface (OISST) diagnostic ---
for region in "${OISST_REGIONS[@]}"; do
    log "[oisst/${region}] shelf-surface series …"
    mhw-build-shelf-surface --region "${region}" \
        || log "WARN: shelf-surface build failed for ${region} (continuing)"
done

# --- Arctic depth profile (Simpson's-paradox panel) ---
log "[arctic] depth profile …"
mhw-build-arctic-profile || log "WARN: arctic-profile build failed (continuing)"

log "=== Build complete. Push the rebuilt model data to the VM with: ==="
cat <<EOF

  rsync -avz --progress \\
    "${PROJECT_DIR}/data/derived/cold_pool/" \\
    ${VM}:${VM_DIR}/data/derived/cold_pool/

EOF
