#!/usr/bin/env bash
# run_simulations.sh
# Runs multiple telemetry simulations (baseline + attack).
# Default: total=30 with 70% baseline, 30% attack.
#
# Usage:
#   ./run_simulations.sh                # run default (30 total, 70/30)
#   ./run_simulations.sh 100 0.7        # run 100 total with 70% baseline
#   ./run_simulations.sh 30 0.6         # run 30 total with 60% baseline

set -euo pipefail
IFS=$'\n\t'

# Configurable params
TOTAL=${1:-30}             # total runs
BASE_RATIO=${2:-0.7}       # fraction that are baseline (0.7 => 70% baseline)
SLEEP_DUR=${3:-300}        # time to record per run (seconds). Default 300s = 5m
OUT_ROOT=${4:-data/raw/audit}

TELEMETRY_SCRIPT="./telemetry_generator.py"   # path to telemetry generator
START_CAPTURE="./collect/start_capture.sh"
STOP_CAPTURE="./collect/stop_capture.sh"

# Sanity checks
if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 not found" >&2
  exit 1
fi

if [ ! -f "$TELEMETRY_SCRIPT" ]; then
  echo "WARNING: telemetry_generator not found at $TELEMETRY_SCRIPT"
  echo "Proceeding but script must exist to generate telemetry."
fi

# Compute counts
BASELINE_COUNT=$(python3 - <<PY
import math,sys
total=${TOTAL}
ratio=${BASE_RATIO}
print(int(round(total*ratio)))
PY)
ATTACK_COUNT=$(( TOTAL - BASELINE_COUNT ))

echo "Run parameters:"
echo "  TOTAL runs:      $TOTAL"
echo "  BASELINE runs:   $BASELINE_COUNT"
echo "  ATTACK runs:     $ATTACK_COUNT"
echo "  RECORD duration: ${SLEEP_DUR}s per run"
echo "  OUTPUT root:     $OUT_ROOT"
echo

mkdir -p "$OUT_ROOT"

run_one() {
  local mode=$1   # baseline or attack
  local idx=$2    # 1-based index for that mode
  local ts=$(date +%Y%m%d-%H%M%S)
  local runid="${ts}_${mode}_${idx}"
  local outdir="${OUT_ROOT}/${runid}"
  mkdir -p "$outdir"

  echo "=== START RUN: $runid (mode=${mode}) ==="
  # If you have start_capture/stop_capture that require sudo, we try to call them.
  if [ -x "$START_CAPTURE" ]; then
    echo "[${runid}] Running start_capture..."
    sudo "$START_CAPTURE" "$runid" || echo "[${runid}] start_capture failed or returned nonzero"
  else
    echo "[${runid}] start_capture not available or not executable; skipping capture service call."
  fi

  # Run telemetry generator (script should accept --mode and --out)
  if [ -x "$TELEMETRY_SCRIPT" ] || [ -f "$TELEMETRY_SCRIPT" ]; then
    # Some versions of telemetry_generator expect --mode and --out.
    echo "[${runid}] Running telemetry_generator.py --mode $mode --out \"$outdir\""
    python3 "$TELEMETRY_SCRIPT" --mode "$mode" --out "$outdir" || \
      echo "[${runid}] telemetry_generator returned nonzero (check args/behavior)"
  else
    echo "[${runid}] telemetry_generator missing; creating placeholder file."
    echo "{\"run_id\":\"$runid\",\"mode\":\"$mode\",\"note\":\"placeholder\"}" > "${outdir}/${runid}.jsonl"
  fi

  # If start/stop capture exist, try stop after SLEEP_DUR (if start_capture actually records)
  if [ -x "$STOP_CAPTURE" ]; then
    echo "[${runid}] Sleeping ${SLEEP_DUR}s while capture runs..."
    sleep "${SLEEP_DUR}"
    echo "[${runid}] Running stop_capture..."
    sudo "$STOP_CAPTURE" "$runid" || echo "[${runid}] stop_capture failed or returned nonzero"
  else
    # If there is no capture script, don't sleep for full duration (but you can if you want)
    echo "[${runid}] stop_capture not available. Not sleeping. If real capture is required, add collect/stop_capture.sh"
  fi

  echo "=== END RUN: $runid ==="
  echo
}

# Run baselines
for i in $(seq 1 $BASELINE_COUNT); do
  run_one baseline "$i"
done

# Run attacks
for i in $(seq 1 $ATTACK_COUNT); do
  run_one attack "$i"
done

echo "All runs complete. Output under: $OUT_ROOT"

