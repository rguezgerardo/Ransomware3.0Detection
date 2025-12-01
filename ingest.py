"""
Very small ingestion stub that reads a jsonl and POSTs to the llm endpoint for scoring.
Outputs detections to `detections.jsonl` in project root.
"""
import argparse, json, requests


LLM_URL = 'http://127.0.0.1:8080/v1/infer'


if __name__=='__main__':
	p=argparse.ArgumentParser()
	p.add_argument('--input', required=True)
	p.add_argument('--out', default='detections.jsonl')
	args=p.parse_args()


	with open(args.input) as fin, open(args.out,'w') as fout:
		for line in fin:
			evt=json.loads(line)
			# simple scoring request
			try:
				resp=requests.post(LLM_URL, json={'event': evt}, timeout=2)
				score = resp.json().get('output','ok')
			except Exception as ex:
				score = f'error:{ex}'
			detection = {
				'event_id': evt.get('event_id'),
				'timestamp': evt.get('timestamp'),
				'event_type': evt.get('event_type'),
				'score': score,
				'label': evt.get('label','normal')
			}
			fout.write(json.dumps(detection)+"\n")
	print('Ingestion complete, wrote', args.out)
