# Ransomware3.0Detection — quickstart

Pre-reqs:
- python3 (3.8+), pip

Steps:
1. create venv: `python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt`
2. start dummy LLM: `python3 llm_dummy.py` (or `make llm`)
3. generate baseline and attack: `make baseline` and `make attack`
4. ingest the attack sample: `make ingest`
5. run rules and metrics: `make rules` and `make metrics`
