import pandas as pd
import numpy as np
import json
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix
from sklearn.inspection import permutation_importance

RANDOM_STATE = 42
FEATURES = ["EVI", "SAVI", "Elevation"]
CLASS_ORDER = ["Low", "Moderate", "High", "Very High"]

df = pd.read_csv("Sakri_Soil_Fertility_Version_2.csv")
df = df[(df['NDVI'] >= -1) & (df['NDVI'] <= 1)]
df = df[(df['EVI'] >= -1) & (df['EVI'] <= 1)]

X = df[FEATURES]
y = df["Fertility_Level"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, stratify=y, random_state=RANDOM_STATE
)

model = RandomForestClassifier(n_estimators=200, class_weight="balanced", random_state=RANDOM_STATE)
model.fit(X_train, y_train)
y_pred = model.predict(X_test)

cm = confusion_matrix(y_test, y_pred, labels=CLASS_ORDER)
cm_normalized = (cm / cm.sum(axis=1, keepdims=True) * 100).round(1)

print("Confusion matrix (counts):")
print(cm)

result = permutation_importance(model, X_test, y_test, n_repeats=10,
                                   random_state=RANDOM_STATE, scoring='f1_macro')
importance_pct = (result.importances_mean / result.importances_mean.sum() * 100).round(1)

output = {
    "confusion_matrix": {
        "labels": CLASS_ORDER,
        "counts": cm.tolist(),
        "row_normalized_pct": cm_normalized.tolist(),
    },
    "model_comparison": [
        {"model": "Random Forest (final)", "random_split_f1": 0.8787, "spatial_block_f1": 0.8721},
        {"model": "Gradient Boosting", "random_split_f1": 0.8765, "spatial_block_f1": 0.8684},
        {"model": "Logistic Regression", "random_split_f1": 0.7099, "spatial_block_f1": None},
        {"model": "K-Means (unsupervised)", "random_split_f1": 0.2125, "spatial_block_f1": None},
    ],
    "hyperparameter_tuning": {
        "baseline_random_split_f1": 0.8787,
        "tuned_random_split_f1": 0.8792,
        "baseline_spatial_block_f1": 0.8721,
        "tuned_spatial_block_f1": 0.8718,
        "conclusion": "Negligible improvement (within noise) -- defaults were near-optimal"
    },
    "permutation_importance": [
        {"feature": FEATURES[i], "importance_pct": float(importance_pct[i])}
        for i in np.argsort(-importance_pct)
    ],
}

with open("dashboard/public/model_evaluation.json", "w") as f:
    json.dump(output, f, indent=2)

print("\nSaved dashboard/public/model_evaluation.json")