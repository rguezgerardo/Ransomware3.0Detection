"""
Compute TP/FP/FN and precision/recall/F1 using detections.jsonl and ground truth labels in telemetry.
Assumes each line in detections.jsonl has 'event_id' and 'label' and that the truth file contains 'event_id' and 'label'.
"""
import argparse, json


if __name__=='__main__':
	p=argparse.ArgumentParser()
	p.add_argument('--truth', required=True)
	p.add_argument('--pred', default='detections.jsonl')
	args=p.parse_args()


	truth_labels={}
	with open(args.truth) as f:
		for line in f:
			e=json.loads(line); truth_labels[e['event_id']]=e.get('label','normal')


	TP=FP=FN=0
	with open(args.pred) as f:
		for line in f:
			d=json.loads(line)
			eid=d['event_id']; pred = 'attack' if d.get('event_type') in ['file_encrypt','mass_write','delete_files'] else 'normal'
			truth = truth_labels.get(eid,'normal')
			if pred=='attack' and truth=='attack': TP+=1
			if pred=='attack' and truth!='attack': FP+=1
			if pred!='attack' and truth=='attack': FN+=1


	prec = TP/(TP+FP) if (TP+FP)>0 else 0.0
	rec = TP/(TP+FN) if (TP+FN)>0 else 0.0
	f1 = 2*prec*rec/(prec+rec) if (prec+rec)>0 else 0.0
	print(f'TP={TP} FP={FP} FN={FN} Precision={prec:.3f} Recall={rec:.3f} F1={f1:.3f}')
