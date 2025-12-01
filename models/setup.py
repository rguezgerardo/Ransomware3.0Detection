import numpy as np
import pandas as pd

from sklearn.metrics import (
    confusion_matrix,
    classification_report,
    roc_auc_score
)
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, IsolationForest

df = pd.read_csv("/Users/gerardorodriguez/Documents/CSE598_Forensics/CSE598_Project/synthetic_features.csv") 

print(df.columns)

# baseline -> 0, attack -> 1
df["y"] = df["label"].map({"baseline": 0, "attack": 1}).astype(int)

feature_cols = [
    "canary_writes",
    "llm_packets",
    "llm_total_bytes",
    "llm_packet_rate",
]

X = df[feature_cols].fillna(0).values
y = df["y"].values
