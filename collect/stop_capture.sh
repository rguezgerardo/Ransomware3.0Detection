#!/bin/bash
# Gerardo Rodriguez 11/26/25
# stop capture process !!!

RUN_ID="$1"
if [ -z "$RUN_ID" ]; then
  echo "Usage: $0 RUN_ID"
  exit 1
fi

PID_FILE="data/raw/pcaps/${RUN_ID}.pid"
if [ -f "$PID_FILE" ]; then
  PID=$(cat "$PID_FILE")
  kill "$PID" 2>/dev/null || true
  rm "$PID_FILE"
fi

# Optional: rotate audit logs so each run has its own copy
AUD_OUT_DIR="data/raw/audit"
mkdir -p "$AUD_OUT_DIR"
cp /var/log/audit/audit.log "$AUD_OUT_DIR/${RUN_ID}.audit.log"
