# mock_llm.py
from flask import Flask, request, jsonify
import time, json, os

app = Flask(__name__)

METRICS_LOG = os.environ.get("MOCK_METRICS_LOG", "metrics_received.jsonl")

@app.route('/v1/infer', methods=['POST'])
def infer():
    payload = request.get_json(silent=True) or {}
    response = {
        'id': int(time.time() * 1000),
        'model': 'dummy-llm',
        'output': 'ok',
        'input_summary': str(payload)[:200]
    }
    return jsonify(response)

@app.route('/v1/metrics', methods=['POST'])
def metrics():
    """
    Accept per-run metrics JSON, append to METRICS_LOG for inspection.
    Expected payload example:
      {
        "run_id": "...",
        "file_reads": 300,
        "file_writes": 0,
        "llm_packets": 300,
        "llm_total_bytes": 12345,
        "llm_packet_rate": 500.0,
        "timestamp": "2025-12-08T12:34:56Z"
      }
    """
    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({"error": "no json payload"}), 400

    # add server receipt time
    payload['_received_at'] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    # append to metrics file (JSONL)
    try:
        with open(METRICS_LOG, "a") as fh:
            fh.write(json.dumps(payload) + "\n")
    except Exception as ex:
        # log to stdout on failure
        print("Warning: failed to write metrics file:", ex)

    print("Received metrics:", json.dumps(payload))  # stdout log
    return jsonify({"status": "ok", "received": True}), 200

if __name__ == '__main__':
    # ensure metrics log exists
    try:
        open(METRICS_LOG, "a").close()
    except Exception:
        pass
    app.run(host='0.0.0.0', port=8080)

