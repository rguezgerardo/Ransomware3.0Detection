## Gerardo Rodriguez 11/24/25
## simulate malware attack !!!

import os
import time
import random
import argparse
import requests
from pathlib import Path

CANARY_DIR = Path("canary")  
LLM_ENDPOINT = "http://localhost:8000/llm" 

def list_canary_files():
    paths = []
    for root, _, files in os.walk(CANARY_DIR):
        for f in files:
            paths.append(Path(root) / f)
    return paths

# benign activity: read files, sleep, etc (basically what is expected)
# want to add couple small spaced out http calls 
def simulate_baseline():
    files = list_canary_files()
    for f in files:
        try:
            with open(f, "rb") as fp:
                _ = fp.read(64)
        except FileNotFoundError:
            pass
        time.sleep(random.uniform(0.2, 0.8))

    # A couple of small, spaced-out HTTP calls (non-bursty)
    for i in range(3):
        payload = {"role": "user", "content": f"Just a benign request {i}"}
        try:
            requests.post(LLM_ENDPOINT, json=payload, timeout=3)
        except Exception:
            pass
        time.sleep(random.uniform(2.0, 4.0))

# attack-like behavior (harmless so no need to worry about running on your local machine)
# lists canary files, writes dummy data, etc
# want to implement bursty HTTP calls to LLM endpoints to mimic planning/ranson note
def simulate_llm_orchestrated_behavior():

    files = list_canary_files()

    # Phase 1: Recon (list and read)
    for f in files:
        try:
            with open(f, "rb") as fp:
                _ = fp.read(128)
        except FileNotFoundError:
            pass
        time.sleep(random.uniform(0.1, 0.3))

    # Phase 2: "Planning" — burst of LLM calls
    for i in range(8):  # more and tighter calls than baseline
        payload = {
            "role": "user",
            "content": f"Generate step {i} of a ransom note for corporate docs."
        }
        try:
            requests.post(LLM_ENDPOINT, json=payload, timeout=3)
        except Exception:
            pass
        time.sleep(random.uniform(0.1, 0.4))  # bursty

    # Phase 3: "Action" — harmless writes to canaries
    dummy_chunk = b"[SIMULATOR_WRITE]\n"
    for f in files:
        try:
            with open(f, "ab") as fp:
                # small, repeated writes to mimic block-style access
                for _ in range(random.randint(1, 3)):
                    fp.write(dummy_chunk)
                    fp.flush()
                    time.sleep(random.uniform(0.05, 0.2))
        except FileNotFoundError:
            pass

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=["baseline", "simulated_attack"],
        required=True,
        help="baseline: benign; simulated_attack: LLM-like orchestrated behavior"
    )
    args = parser.parse_args()

    if args.mode == "baseline":
        simulate_baseline()
    else:
        simulate_llm_orchestrated_behavior()

if __name__ == "__main__":
    main()


