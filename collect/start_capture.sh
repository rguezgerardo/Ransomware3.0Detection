#!/bin/bash
# Gerardo Rodriguez 11/26/25
# capture telemetry data !!!

set -e

RUN_ID="$1"
if [ -z "$RUN_ID" ]; then
  echo "Usage: $0 RUN_ID"
  exit 1
fi

OUT_DIR="data/raw/pcaps"
mkdir -p "$OUT_DIR"

# Capture only traffic from LLM endpoint port (we used port 8000 - here is the url endpoint we will use - "http://localhost:8000/llm" ) for 5 minutes max
tcpdump -i any port 8000 -w "$OUT_DIR/${RUN_ID}.pcap" &
echo $! > "data/raw/pcaps/${RUN_ID}.pid"
