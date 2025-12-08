#!/usr/bin/env python3
"""
Compute per-run summary metrics and POST them to metrics endpoint.

Usage:
  python3 summarize_run.py <runid> \
      --raw data/raw/audit/<runid>.jsonl \
      --proc data/processed/<runid>.processed.jsonl \
      --out-dir metrics \
      --url http://127.0.0.1:8080/v1/metrics

If --url is omitted it defaults to http://127.0.0.1:8080/v1/metrics
"""
import argparse, json, os, sys, datetime, time, requests

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('runid', help='Run id (used for filenames and run_id in payload)')
    p.add_argument('--raw', required=True, help='Path to raw telemetry JSONL (data/raw/audit/<runid>.jsonl)')
    p.add_argument('--proc', required=True, help='Path to processed detections JSONL (data/processed/<runid>.processed.jsonl)')
    p.add_argument('--out-dir', default='metrics', help='Directory to write local summary JSON')
    p.add_argument('--url', default=os.environ.get('METRICS_URL', 'http://127.0.0.1:8080/v1/metrics'), help='Metrics POST URL')
    p.add_argument('--timeout', type=float, default=3.0, help='HTTP timeout seconds')
    return p.parse_args()

def read_jsonl(path):
    """Yield parsed JSON objects from a file. Handles JSON array too."""
    if not os.path.exists(path):
        return
    txt = open(path).read().strip()
    if not txt:
        return
    # try whole-file parse (array or object)
    try:
        parsed = json.loads(txt)
        if isinstance(parsed, list):
            for el in parsed:
                yield el
            return
        elif isinstance(parsed, dict):
            yield parsed
            return
    except Exception:
        pass
    # fallback to per-line JSON
    with open(path) as fh:
        for ln in fh:
            ln = ln.strip()
            if not ln:
                continue
            try:
                obj = json.loads(ln)
            except Exception:
                continue
            if isinstance(obj, list):
                for el in obj:
                    yield el
            else:
                yield obj

def isoparse(t):
    """Parse a handful of ISO variants to naive datetime in UTC."""
    if not t:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return datetime.datetime.strptime(t, fmt)
        except Exception:
            pass
    # fallback
    try:
        t2 = t.replace("Z", "")
        return datetime.datetime.fromisoformat(t2)
    except Exception:
        return None

def compute(runid, raw_path, proc_path):
    # file reads/writes from raw
    file_reads = 0
    file_writes = 0
    for obj in read_jsonl(raw_path):
        et = obj.get('event_type') or obj.get('type') or ''
        if et == 'file_read':
            file_reads += 1
        elif et == 'file_write':
            file_writes += 1

    # llm packets, bytes, timestamps from processed file
    llm_packets = 0
    total_bytes = 0
    timestamps = []
    for obj in read_jsonl(proc_path):
        llm_packets += 1
        req_b = obj.get('llm_req_bytes') or 0
        resp_b = obj.get('llm_resp_bytes') or 0
        try:
            total_bytes += int(req_b) + int(resp_b)
        except Exception:
            pass
        ts = obj.get('timestamp')
        dt = isoparse(ts)
        if dt:
            timestamps.append(dt)

    # packet rate: packets / duration (seconds)
    packet_rate = None
    if timestamps:
        start = min(timestamps)
        end = max(timestamps)
        duration = (end - start).total_seconds()
        if duration > 0:
            packet_rate = llm_packets / duration
        else:
            packet_rate = float('inf')
    else:
        packet_rate = 0.0

    summary = {
        "run_id": runid,
        "file_reads": file_reads,
        "file_writes": file_writes,
        "llm_packets": llm_packets,
        "llm_total_bytes": total_bytes,
        "llm_packet_rate": packet_rate,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    return summary

def main():
    args = parse_args()
    os.makedirs(args.out_dir, exist_ok=True)
    summary = compute(args.runid, args.raw, args.proc)

    # write local copy
    outpath = os.path.join(args.out_dir, f"{args.runid}_summary.json")
    with open(outpath, "w") as fh:
        json.dump(summary, fh, indent=2)
    print("Wrote local summary:", outpath)

    # POST to metrics URL
    try:
        resp = requests.post(args.url, json=summary, timeout=args.timeout)
        resp.raise_for_status()
        print("Posted metrics to", args.url)
    except Exception as e:
        print("Warning: failed to post metrics:", e, file=sys.stderr)
        # still exit non-zero? we keep exit 0 so pipeline continues

if __name__ == '__main__':
    main()

