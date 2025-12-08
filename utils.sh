#!/usr/bin/env bash
set -euo pipefail


log(){ echo "[$(date +%Y%m%d-%H%M%S)] $*"; }


safe_mkdir(){ mkdir -p "$1" || true; }


die(){ log "ERROR: $*"; exit 1; }
