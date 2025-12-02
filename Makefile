.PHONY: llm baseline attack ingest rules metrics clean

llm:
	python3 llm_dummy.py

baseline:
	python3 telemetry_generator.py --mode baseline --out baseline.jsonl --count 300

attack:
	python3 telemetry_generator.py --mode attack --out attack.jsonl --count 300

ingest:
	python3 ingest.py --input attack.jsonl --out detections.jsonl

rules:
	python3 rule_tester.py --input attack.jsonl

metrics:
	python3 metrics.py --truth attack.jsonl --pred detections.jsonl

clean:
	rm -f *.jsonl detections.jsonl
