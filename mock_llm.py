from flask import Flask, request, jsonify
import time


app = Flask(__name__)


@app.route('/v1/infer', methods=['POST'])
def infer():
	payload = request.get_json(silent=True) or {}
	# simple deterministic dummy response; you can extend to check payload
	response = {
		'id': int(time.time()*1000),
		'model': 'dummy-llm',
		'output': 'ok',
		'input_summary': str(payload)[:200]
	}
	return jsonify(response)


if __name__ == '__main__':
	app.run(host='0.0.0.0', port=8080)
