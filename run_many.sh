#!/usr/bin/env bash
set -euo pipefail

# CONFIG: number of baseline and attack runs
BASELINE_COUNT=${1:-70}
ATTACK_COUNT=${2:-30}

# Where to put outputs
OUT_DIR="data/raw/audit"
PROCESSED_DIR="data/processed"
ALERTS_DIR="alerts"
METRICS_DIR="metrics"

mkdir -p "$OUT_DIR" "$PROCESSED_DIR" "$ALERTS_DIR" "$METRICS_DIR"

timestamp() {
  date +"%Y%m%d-%H%M%S"
}

run_pipeline_once() {
  local mode=$1   # "baseline" or "attack"
  local seq=$2    # integer index

  local runid="$(timestamp)_${mode}_${seq}"
  local raw_out="${OUT_DIR}/${runid}.jsonl"
  local processed_out="${PROCESSED_DIR}/${runid}.processed.jsonl"
  local alerts_out="${ALERTS_DIR}/${runid}_alerts.json"
  local metrics_out="${METRICS_DIR}/${runid}_metrics.json"

  echo "=== START RUN: ${runid} (mode=${mode}) ==="

  # 1) Generate telemetry
  echo "[${runid}] Generating telemetry: mode=${mode} -> ${raw_out}"
  # NOTE: telemetry_generator.py must accept: --mode <mode> --out <path>
  python3 ./telemetry_generator.py --mode "${mode}" --out "${raw_out}"
  echo "[${runid}] Telemetry written: ${raw_out}"

  # 2) Ingest
  echo "[${runid}] Running ingest: in=${raw_out} out=${processed_out}"
  # NOTE: ingest.py must accept: --in <path> --out <path>
  python3 ./ingest.py --in "${raw_out}" --out "${processed_out}"
  echo "[${runid}] Ingestion complete: ${processed_out}"

  # 3) Rule testing (rule_tester.py prints alerts to stdout; redirect)
  echo "[${runid}] Running rule_tester: input=${processed_out} -> ${alerts_out}"
  # If rule_tester.py supports --input only and returns JSON to stdout:
  python3 ./rule_tester.py --input "${processed_out}" > "${alerts_out}" || {
    echo "[${runid}] WARNING: rule_tester returned non-zero exit; continuing"
  }
  echo "[${runid}] Alerts saved: ${alerts_out}"

  # 4) Metrics
  echo "[${runid}] Running metrics: alerts=${alerts_out} processed=${processed_out} -> ${metrics_out}"
  # Change this line if metrics.py has a different CLI
  if python3 ./metrics.py --alerts "${alerts_out}" --processed "${processed_out}" --out "${metrics_out}"; then
    echo "[${runid}] Metrics written: ${metrics_out}"
  else
    echo "[${runid}] WARNING: metrics.py failed; trying fallback to stdout redirect"
    python3 ./metrics.py --alerts "${alerts_out}" --processed "${processed_out}" > "${metrics_out}" || echo "[${runid}] metrics fallback failed"
  fi

  echo "=== END RUN: ${runid} ==="
  echo
}

# Run baseline (1..BASELINE_COUNT)
for i in $(seq 1 ${BASELINE_COUNT}); do
  run_pipeline_once "baseline" "${i}"
done

# Run attack (1..ATTACK_COUNT)
for i in $(seq 1 ${ATTACK_COUNT}); do
  run_pipeline_once "attack" "${i}"
done

echo "All runs finished. Baseline=${BASELINE_COUNT}, Attack=${ATTACK_COUNT}"

