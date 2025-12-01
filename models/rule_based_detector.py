from setup import *

baseline_mask = df["label"] == "baseline"
attack_mask   = df["label"] == "attack"

T_canary = df.loc[baseline_mask, "canary_writes"].max()
T_rate   = df.loc[baseline_mask, "llm_packet_rate"].median()

print(f"Rule thresholds: canary_writes > {T_canary}, llm_packet_rate > {T_rate:.3f}")

rule_pred = (
    (df["canary_writes"] > T_canary) &
    (df["llm_packet_rate"] > T_rate)
).astype(int)  

cm = confusion_matrix(y, rule_pred)
tn, fp, fn, tp = cm.ravel()

print("Rule-based detector confusion matrix (rows=true, cols=pred):")
print(cm)
print(f"TN={tn} FP={fp} FN={fn} TP={tp}")

tpr = tp / (tp + fn) if (tp + fn) > 0 else 0.0  
fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0  
print(f"TPR (recall for attack) = {tpr:.3f}")
print(f"FPR (baseline misclassified as attack) = {fpr:.3f}")
