"""
A tiny rule tester: simple heuristic rules applied to jsonl events.
"""
import argparse, json

RULES = [
	# masses of writes/ deletes are represented by event types here
	lambda e: e.get('event_type')=='file_encrypt',
	lambda e: e.get('event_type')=='mass_write',
	lambda e: e.get('event_type')=='delete_files'
]


if __name__=='__main__':
	p=argparse.ArgumentParser()
	p.add_argument('--input', required=True)
	args=p.parse_args()

	detections=[]
	with open(args.input) as f:
		for line in f:
			e=json.loads(line)
			matched=False
			for r in RULES:
				if r(e):
					matched=True
					break
			if matched:
				detections.append(e)


	print(f'Detections: {len(detections)}')
	# print some examples
	for d in detections[:5]:
		print(d.get('timestamp'), d.get('event_type'), d.get('path'))
