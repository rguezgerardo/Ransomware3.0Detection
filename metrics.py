#!/usr/bin/env python3
"""
Robust metrics calculator.

Accepts truth and prediction inputs that are:
 - a JSONL file (one JSON object per line)
 - a single JSON array file (one top-level [...])
 - mixed (some lines are objects, some are arrays)

Usage:
  python3 metrics.py --truth alerts/<run>_alerts.json --pred data/processed/<run>.processed.jsonl --out metrics/<run>_metrics.json
"""
import argparse
import json
import sys
import os

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--truth', help='Ground truth file (JSONL or JSON array)')
    p.add_argument('--alerts', help='Alias for --truth')
    p.add_argument('--pred', default='detections.jsonl', help='Predictions/detections file (JSONL or JSON array)')
    p.add_argument('--processed', help='Alias for --pred')
    p.add_argument('--out', help='Optional JSON output file for metrics')
    return p.parse_args()

def iter_json_objects_from_file(path):
    """
    Yields JSON objects found in path. Accepts:
      - entire file is a JSON array -> yields each element
      - file is JSONL -> yields each parsed object per line
      - mixed content: tries per-line parse, if a line parses to list -> yields each element
    """
    with open(path, 'r') as fh:
        text = fh.read().strip()
        if not text:
            return
        # Try: file is a single JSON array/object
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                for item in parsed:
                    if item is None:
                        continue
                    yield item
                return
            elif isinstance(parsed, dict):
                yield parsed
                return
        except Exception:
            # Not a single JSON document; fall back to per-line parsing
            pass

    # per-line parsing
    with open(path, 'r') as fh:
        for ln_no, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception as exc:
                # skip malformed but warn
                print(f"Warning: skipping malformed JSON on line {ln_no} of {path}: {exc}", file=sys.stderr)
                continue

            if isinstance(obj, list):
                for item in obj:
                    yield item
            else:
                yield obj

def get_id_label(obj, ln_desc=""):
    """
    Extract event id and label from an object that may have different schemas.
    Returns tuple (eid, label) or (None, None) if not found.
    """
    if not isinstance(obj, dict):
        # not a dict -> skip
        return (None, None)
    eid = obj.get('event_id') or obj.get('id') or obj.get('eventId') or obj.get('run_id') or None
    label = obj.get('label') or obj.get('truth') or obj.get('ground_truth') or obj.get('y') or 'normal'
    return (eid, label)

if __name__ == '__main__':
    args = parse_args()
    truth_path = args.truth or args.alerts
    pred_path = args.pred or args.processed or 'detections.jsonl'

    if not truth_path or not os.path.exists(truth_path):
        print("Error: truth file not found. Provide --truth or --alerts pointing to a file.", file=sys.stderr)
        sys.exit(2)
    if not os.path.exists(pred_path):
        print(f"Error: predictions file not found: {pred_path}", file=sys.stderr)
        sys.exit(2)

    # Build truth map
    truth_labels = {}
    for obj in iter_json_objects_from_file(truth_path):
        eid, label = get_id_label(obj)
        if eid is None:
            print(f"Warning: truth entry missing event id (skipping): {obj}", file=sys.stderr)
            continue
        truth_labels[eid] = label

    # Evaluate predictions
    TP = FP = FN = 0
    pred_count = 0
    for obj in iter_json_objects_from_file(pred_path):
        pred_count += 1
        # get prediction id and event_type
        if not isinstance(obj, dict):
            print(f"Warning: prediction entry is not an object (skipping): {obj}", file=sys.stderr)
            continue
        eid = obj.get('event_id') or obj.get('id') or obj.get('eventId') or None
        if eid is None:
            print(f"Warning: prediction missing event id (skipping): {obj}", file=sys.stderr)
            continue
        # heuristic: consider these event types as attack
        evt_type = obj.get('event_type') or obj.get('type') or ''
        pred_label = 'attack' if evt_type in ['file_encrypt', 'mass_write', 'delete_files', 'file_write'] else 'normal'

        truth_label = truth_labels.get(eid, 'normal')
        if pred_label == 'attack' and truth_label == 'attack':
            TP += 1
        elif pred_label == 'attack' and truth_label != 'attack':
            FP += 1
        elif pred_label != 'attack' and truth_label == 'attack':
            FN += 1
        # else both normal -> TN (ignored)

    prec = TP / (TP + FP) if (TP + FP) > 0 else 0.0
    rec = TP / (TP + FN) if (TP + FN) > 0 else 0.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0

    summary = {
        'pred_count': pred_count,
        'TP': TP,
        'FP': FP,
        'FN': FN,
        'precision': round(prec, 3),
        'recall': round(rec, 3),
        'f1': round(f1, 3)
    }

    print(f"pred_count={pred_count} TP={TP} FP={FP} FN={FN} Precision={prec:.3f} Recall={rec:.3f} F1={f1:.3f}")

    if args.out:
        out_parent = os.path.dirname(args.out)
        if out_parent:
            os.makedirs(out_parent, exist_ok=True)
        with open(args.out, 'w') as ofh:
            json.dump(summary, ofh, indent=2)
        print("Wrote metrics JSON to", args.out)

