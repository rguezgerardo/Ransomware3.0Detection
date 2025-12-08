# ingest.py
"""
Very small ingestion stub that reads a jsonl and POSTs to the llm endpoint for scoring.
Outputs detections to `detections.jsonl` by default.
Each detection includes llm_req_bytes and llm_resp_bytes for accurate byte accounting.
"""
import argparse
import json
import requests
import sys
import os

LLM_URL = os.environ.get('LLM_URL', 'http://127.0.0.1:8080/v1/infer')

def parse_args():
    p = argparse.ArgumentParser()
    # Accept both variants used across run scripts
    p.add_argument('--input', dest='input', help='Input JSONL file (one JSON object per line)')
    p.add_argument('--in', dest='input_alias', help='Alias for --input (compat)')
    p.add_argument('--out', default='detections.jsonl', help='Output JSONL detections file')
    p.add_argument('--timeout', type=float, default=2.0, help='HTTP request timeout seconds')
    return p.parse_args()

if __name__ == '__main__':
    args = parse_args()
    input_path = args.input or args.input_alias
    if not input_path:
        print("Error: must provide --input or --in", file=sys.stderr)
        sys.exit(2)

    # ensure parent dir for out exists
    out_parent = os.path.dirname(args.out)
    if out_parent:
        os.makedirs(out_parent, exist_ok=True)

    with open(input_path) as fin, open(args.out, 'w') as fout:
        for line_no, line in enumerate(fin, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                evt = json.loads(line)
            except Exception as e:
                print(f"Warning: skipping malformed JSON on line {line_no}: {e}", file=sys.stderr)
                continue

            # prepare payload and measure request size
            payload = {'event': evt}
            try:
                req_bytes = len(json.dumps(payload).encode())
            except Exception:
                # fallback conservative estimate
                req_bytes = 0

            # perform request
            score = None
            resp_bytes = 0
            try:
                resp = requests.post(LLM_URL, json=payload, timeout=args.timeout)
                try:
                    resp_json = resp.json()
                except Exception:
                    # if response isn't JSON, record text
                    resp_json = {'output': resp.text}
                score = resp_json.get('output', 'ok')
                # measure response bytes
                try:
                    resp_bytes = len(resp.content)
                except Exception:
                    resp_bytes = len(str(resp.text).encode()) if hasattr(resp, 'text') else 0
            except Exception as ex:
                score = f'error:{ex}'
                resp_bytes = 0

            # unify event id and timestamp keys
            event_id = evt.get('event_id') or evt.get('id') or evt.get('eventId') or None
            timestamp = evt.get('timestamp') or evt.get('time') or None

            detection = {
                'event_id': event_id,
                'timestamp': timestamp,
                'event_type': evt.get('event_type') or evt.get('type') or None,
                'score': score,
                'label': evt.get('label', 'normal'),
                'llm_req_bytes': req_bytes,
                'llm_resp_bytes': resp_bytes
            }

            fout.write(json.dumps(detection) + "\n")

    print('Ingestion complete, wrote', args.out)

