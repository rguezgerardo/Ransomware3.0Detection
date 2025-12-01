from setup import *
from rule_based_detector import baseline_mask

X_baseline = df.loc[baseline_mask, feature_cols].fillna(0).values

iso = IsolationForest(
    n_estimators=200,
    contamination=0.3,  
    random_state=42,
)
iso.fit(X_baseline)

raw_scores = -iso.decision_function(X)
scores = (raw_scores - raw_scores.min()) / (raw_scores.max() - raw_scores.min() + 1e-9)

auroc = roc_auc_score(y, scores)
print(f"IsolationForest AUROC: {auroc:.3f}")

threshold = np.quantile(scores, 0.70)
iso_pred = (scores >= threshold).astype(int)

cm_iso = confusion_matrix(y, iso_pred)
tn, fp, fn, tp = cm_iso.ravel()

print("IsolationForest confusion matrix (rows=true, cols=pred):")
print(cm_iso)

tpr_iso = tp / (tp + fn) if (tp + fn) > 0 else 0.0
fpr_iso = fp / (fp + tn) if (fp + tn) > 0 else 0.0
print(f"IsolationForest TPR = {tpr_iso:.3f}")
print(f"IsolationForest FPR = {fpr_iso:.3f}")
