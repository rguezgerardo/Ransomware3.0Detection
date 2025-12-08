#!/usr/bin/env python3
import argparse, json, os
from datetime import datetime

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=["baseline", "attack"], required=True)
    p.add_argument("--out", required=True, help="Output FILE or DIRECTORY")
    p.add_argument("--count", type=int, default=300)
    p.add_argument("--run-id", default=None)
    return p.parse_args()

def generate_event(i, mode, run_id):
    ts = datetime.utcnow().isoformat() + "Z"
    if mode == "baseline":
        etype = "file_read"
        note = "baseline read"
    else:
        etype = "file_write"
        note = "attack write"

    # produce both 'id' and canonical 'event_id' to be robust to consumers
    event_id = f"{run_id}-{i}"
    return {
        "timestamp": ts,
        "id": i,
        "event_id": event_id,
        "event_type": etype,
        "filename": "canary/doc1.txt",
        "note": note
    }

def main():
    args = parse_args()

    out_arg = args.out
    run_id = args.run_id or datetime.utcnow().strftime("%Y%m%d-%H%M%S")

    # CASE 1: --out is a directory ➝ create <dir>/<run-id>.jsonl
    if os.path.isdir(out_arg) or out_arg.endswith("/"):
        os.makedirs(out_arg, exist_ok=True)
        out_file = os.path.join(out_arg, f"{run_id}.jsonl")
    else:
        parent = os.path.dirname(out_arg)
        if parent:
            os.makedirs(parent, exist_ok=True)
        out_file = out_arg

    if out_file is None:
        raise RuntimeError("Internal error: out_file was not set")

    with open(out_file, "w") as f:
        for i in range(args.count):
            evt = generate_event(i, args.mode, run_id)
            f.write(json.dumps(evt) + "\n")

    print(out_file)

if __name__ == "__main__":
    main()

