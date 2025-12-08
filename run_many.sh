#!/usr/bin/env bash
set -euo pipefail

BASELINE_COUNT=${1:-70}
ATTACK_COUNT=${2:-30}

OUT_DIR="data/raw/audit"
PROCESSED_DIR="data/processed"
ALERTS_DIR="alerts"
METRICS_DIR="metrics"

mkdir -p "$OUT_DIR" "$PROCESSED_DIR" "$ALERTS_DIR" "$METRICS_DIR"

timestamp() { date +"%Y%m%d-%H%M%S"; }

run_pipeline_once() {
  local mode=$1
  local seq=$2

  local runid="$(timestamp)_${mode}_${seq}"
  local raw_out="${OUT_DIR}/${runid}.jsonl"
  local processed_out="${PROCESSED_DIR}/${runid}.processed.jsonl"
  local alerts_out="${ALERTS_DIR}/${runid}_alerts.json"
  local metrics_out="${METRICS_DIR}/${runid}_metrics.json"

  echo "=== START RUN: ${runid} (mode=${mode}) ==="

  # 1) Generate telemetry
  echo "[${runid}] Generating telemetry -> ${raw_out}"
  python3 ./telemetry_generator.py --mode "${mode}" --out "${raw_out}" || echo "[${runid}] telemetry_generator returned non-zero"

  # 2) Ingest (calls LLM)
  echo "[${runid}] Running ingest: in=${raw_out} out=${processed_out}"
  python3 ./ingest.py --in "${raw_out}" --out "${processed_out}" || echo "[${runid}] ingest returned non-zero"

  # 3) Rule testing
  echo "[${runid}] Running rule_tester: input=${processed_out} -> ${alerts_out}"
  python3 ./rule_tester.py --input "${processed_out}" --out "${alerts_out}" || echo "[${runid}] rule_tester returned non-zero"

  # 4) Metrics (write JSON)
  echo "[${runid}] Running metrics: truth=${alerts_out} pred=${processed_out} -> ${metrics_out}"
  python3 ./metrics.py --truth "${alerts_out}" --pred "${processed_out}" --out "${metrics_out}" || echo "[${runid}] metrics returned non-zero"

  # 5) Summarize and POST to mock LLM
  echo "[${runid}] Summarizing and posting metrics to mock LLM"
  python3 ./summarize_run.py "${runid}" --raw "${raw_out}" --proc "${processed_out}" --out-dir "${METRICS_DIR}" --url "${METRICS_URL:-http://127.0.0.1:8080/v1/metrics}" || echo "[${runid}] summarize_run returned non-zero"

  echo "=== END RUN: ${runid} ==="
  echo
}

# Run baseline
for i in $(seq 1 ${BASELINE_COUNT}); do
  run_pipeline_once "baseline" "${i}"
done

# Run attacks
for i in $(seq 1 ${ATTACK_COUNT}); do
  run_pipeline_once "attack" "${i}"
done

echo "All runs finished. Baseline=${BASELINE_COUNT}, Attack=${ATTACK_COUNT}"

