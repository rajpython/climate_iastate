#!/usr/bin/env bash
# Rebuild per-cell MHW states + aggregates for all 12 zones from the staged OISST cache.
# MHW_FROZEN_INPUTS=1: the cache is the authority; nothing is (re)fetched from PFEG.
# Usage: ./run_rebuild.sh [END_DATE]   (default 2026-08-31)
set -uo pipefail
END="${1:-2026-08-31}"
export MHW_FROZEN_INPUTS=1
cd "$(dirname "$0")"
mkdir -p logs
for z in sebs nbs wgoa egoa ai_west ai_central ai_east chukchi beaufort ebs goa ai; do
  echo "=== $z  $(date -u +%H:%M:%S) ==="
  .venv/bin/mhw-backfill --region "$z" --start 1982-01-01 --end "$END" \
      > "logs/backfill_$z.log" 2>&1
  rc=$?
  tail -3 "logs/backfill_$z.log" | sed 's/^/    /'
  echo "    rc=$rc"
  [ $rc -ne 0 ] && echo "    *** FAILED: $z ***"
done
echo "=== ALL DONE $(date -u +%H:%M:%S) ==="
