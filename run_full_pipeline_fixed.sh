#!/usr/bin/env bash
set -euo pipefail


# Fixed full pipeline runner
# Assumptions (edit these if your scripts take different args):
# - collect/start_capture.sh RUN_ID
# - collect/stop_capture.sh RUN_ID
# - telemetry_generator.py --mode <baseline|attack> --out <file or dir> [--count N] [--run-id RUNID]
# - ingest.py --in <raw.jsonl> --out <processed.jsonl>
# - rule_tester.py --in <processed.jsonl> --out <alerts.json>
# - metrics.py --alerts <alerts.json> --out <metrics.json>


SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/utils.sh"


TS=$(date +%Y%m%d-%H%M%S)
WORKDIR="$SCRIPT_DIR/data"
RAW_DIR="$WORKDIR/raw/audit"
PROC_DIR="$WORKDIR/processed"
ALERT_DIR="$SCRIPT_DIR/alerts"
METRICS_DIR="$SCRIPT_DIR/metrics_out"


safe_mkdir "$RAW_DIR"
safe_mkdir "$PROC_DIR"
safe_mkdir "$ALERT_DIR"
safe_mkdir "$METRICS_DIR"


run_capture_and_telemetry(){
MODE="$1" # baseline or attack
RUN_ID="${TS}_${MODE}"
RAW_FILE="${RAW_DIR}/${RUN_ID}.jsonl"
PROC_FILE="${PROC_DIR}/${RUN_ID}.processed.jsonl"
ALERT_FILE="${ALERT_DIR}/${RUN_ID}_alerts.json"
METRICS_FILE="${METRICS_DIR}/${RUN_ID}_metrics.json"


log "=== START $MODE run: $RUN_ID ==="


# Start capture (needs RUN_ID argument)
if ! sudo "$SCRIPT_DIR/collect/start_capture.sh" "$RUN_ID"; then
log "Warning: start_capture failed or returned non-zero. Continuing anyway."
fi


# Generate telemetry
log "Generating telemetry: mode=$MODE runid=$RUN_ID -> $RAW_FILE"
if ! python3 "$SCRIPT_DIR/telemetry_generator.py" --mode "$MODE" --out "$RAW_FILE" --count 300 --run-id "$RUN_ID"; then
die "telemetry_generator failed for $RUN_ID"
fi


# Stop capture
if ! sudo "$SCRIPT_DIR/collect/stop_capture.sh" "$RUN_ID"; then
log "Warning: stop_capture failed or returned non-zero. Continuing anyway."
fi


# Ingest
log "Running ingest: in=$RAW_FILE out=$PROC_FILE"
if ! python3 "$SCRIPT_DIR/ingest.py" --in "$RAW_FILE" --out "$PROC_FILE"; then
die "ingest.py failed for $RAW_FILE"
fi


# Rule tester
log "Running rule_tester: in=$PROC_FILE out=$ALERT_FILE"
if ! python3 "$SCRIPT_DIR/rule_tester.py" --in "$PROC_FILE" --out "$ALERT_FILE"; then
die "rule_tester.py failed for $PROC_FILE"
fi


# Metrics
log "Running metrics: alerts=$ALERT_FILE out=$METRICS_FILE"
if ! python3 "$SCRIPT_DIR/metrics.py" --alerts "$ALERT_FILE" --out "$METRICS_FILE"; then
die "metrics.py failed for $ALERT_FILE"
fi


log "=== FINISHED $MODE run: $RUN_ID ==="
}


# Run baseline then attack
run_capture_and_telemetry baseline
run_capture_and_telemetry attack


log "All runs completed. Results in: $RAW_DIR, $PROC_DIR, $ALERT_DIR, $METRICS_DIR"
