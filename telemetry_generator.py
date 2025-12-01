"""
Simple telemetry generator that emits JSON Lines
Usage:
python3 telemetry_generator.py --mode baseline --out baseline.jsonl --count 100
python3 telemetry_generator.py --mode attack --out attack.jsonl --count 200
"""
import argparse, json, random, time, uuid
from datetime import datetime


EVENT_TYPES_BASELINE = ['process_start', 'file_open', 'net_connect', 'execve']
EVENT_TYPES_ATTACK = EVENT_TYPES_BASELINE + ['file_encrypt','mass_write','delete_files']


PROCS = ['bash','python','sshd','gnome-shell','nautilus','systemd']
FILES = ['/home/user/documents/report.docx','/home/user/pics/image1.png','/tmp/tmpfile']

def now_ts():
	return datetime.utcnow().isoformat()+'Z'


def gen_event(mode):
	evt = {}
	evt['event_id'] = str(uuid.uuid4())
	evt['timestamp'] = now_ts()
	if mode=='baseline':
		evt['event_type'] = random.choice(EVENT_TYPES_BASELINE)
	else:
		# bias towards attack events
		evt['event_type'] = random.choices(EVENT_TYPES_ATTACK, weights=[10,10,5,8,40,20,5])[0]
	evt['pid'] = random.randint(1000,9000)
	evt['proc'] = random.choice(PROCS)
	evt['path'] = random.choice(FILES)
	# simple labels for evaluation
	evt['label'] = 'attack' if mode=='attack' and evt['event_type'] in ['file_encrypt','mass_write','delete_files'] else 'normal'
	return evt




if __name__=='__main__':
	p=argparse.ArgumentParser()
	p.add_argument('--mode',choices=['baseline','attack'],required=True)
	p.add_argument('--out',required=True)
	p.add_argument('--count',type=int,default=200)
	args=p.parse_args()

	with open(args.out,'w') as f:
		for _ in range(args.count):
			e=gen_event(args.mode)
			f.write(json.dumps(e)+"\n")
			time.sleep(0.005)


	print(f'Wrote {args.out}')
