#!/usr/bin/env python3
"""
Simple rule tester.

Reads a processed JSONL file (one JSON object per line) and applies simple rules.
Outputs alerts as a JSON array to --out (file).
"""

import argparse
import json
import os
import sys

def parse_args():
    p = argparse.ArgumentParser(description="Run rules over processed telemetry JSONL")
    p.add_argument("--input", "-i", required=True, help="Input processed JSONL file (one JSON object per line)")
    p.add_argument("--out", "-o", "--output", required=True, dest="out", help="Output alerts JSON file (array)")
    return p.parse_args()

def load_events(path):
    events = []
    if not os.path.exists(path):
        raise FileNotFoundError(f"Input file not found: {path}")
    with open(path, "r") as fh:
        for ln_no, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except Exception as e:
                # skip malformed lines but print warning
                print(f"Warning: failed to parse JSON on line {ln_no}: {e}", file=sys.stderr)
    return events

def apply_rules(events):
    """
    Minimal example rules:
      - WRITE_CANARY: any file_write where filename contains 'canary' -> HIGH
      - MANY_EXEC: if a single pid executes > 20 execve events in this file -> MEDIUM
      - SUSPICIOUS_DELETE: any file_delete on 'canary' -> HIGH
    Returns list of alert dicts.
    """
    alerts = []
    # simple counters used by some rules
    exec_count_by_pid = {}

    for ev in events:
        # normalize keys (robust against small schema differences)
        ev_type = ev.get("event_type") or ev.get("type") or ""
        ts = ev.get("timestamp") or ev.get("time") or None
        pid = ev.get("pid") or ev.get("process_pid") or None
        filename = ev.get("filename") or ev.get("path") or ""

        # Rule: WRITE_CANARY
        if ev_type == "file_write" and "canary" in filename.lower():
            alerts.append({
                "timestamp": ts,
                "rule": "WRITE_CANARY",
                "severity": "HIGH",
                "description": f"Write to canary file: {filename}",
                "evidence": ev
            })

        # Rule: SUSPICIOUS_DELETE
        if ev_type == "file_delete" and "canary" in filename.lower():
            alerts.append({
                "timestamp": ts,
                "rule": "SUSPICIOUS_DELETE",
                "severity": "HIGH",
                "description": f"Delete of canary file: {filename}",
                "evidence": ev
            })

        # Track execs for MANY_EXEC
        if ev_type == "execve" or ev_type == "process_exec" or ev_type == "exec":
            if pid is not None:
                exec_count_by_pid[pid] = exec_count_by_pid.get(pid, 0) + 1

    # Post-pass rules using counters
    for pid, cnt in exec_count_by_pid.items():
        if cnt > 20:
            alerts.append({
                "timestamp": None,
                "rule": "MANY_EXEC",
                "severity": "MEDIUM",
                "description": f"PID {pid} executed {cnt} times in this run",
                "evidence": {"pid": pid, "exec_count": cnt}
            })

    return alerts

def write_alerts(alerts, out_path):
    # ensure parent dir
    parent = os.path.dirname(out_path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    # write JSON list
    with open(out_path, "w") as fh:
        json.dump(alerts, fh, indent=2)
    print(out_path)

def main():
    args = parse_args()
    events = load_events(args.input)
    alerts = apply_rules(events)
    write_alerts(alerts, args.out)

if __name__ == "__main__":
    main()

