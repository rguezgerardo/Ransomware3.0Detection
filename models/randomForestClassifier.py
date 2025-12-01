from setup import *

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42, stratify=y
)

rf = RandomForestClassifier(
    n_estimators=200,
    max_depth=None,
    random_state=42,
)
rf.fit(X_train, y_train)

y_pred = rf.predict(X_test)

print("RandomForest confusion matrix (rows=true, cols=pred):")
print(confusion_matrix(y_test, y_pred))

print("\nRandomForest classification report:")
print(classification_report(y_test, y_pred, digits=3))

print("RandomForest feature importances:")
for name, imp in sorted(
    zip(feature_cols, rf.feature_importances_),
    key=lambda x: x[1],
    reverse=True,
):
    print(f"  {name}: {imp:.3f}")
