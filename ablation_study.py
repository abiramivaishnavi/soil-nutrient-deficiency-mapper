import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score, classification_report

df = pd.read_csv("Sakri_Soil_Fertility_Version_2.csv")
df = df[(df['NDVI'] >= -1) & (df['NDVI'] <= 1)]
df = df[(df['EVI'] >= -1) & (df['EVI'] <= 1)]

y = df["Fertility_Level"]

feature_sets = {
    "A: NDVI+EVI+SAVI":                     ["NDVI", "EVI", "SAVI"],
    "B: + Soil_Moisture":                   ["NDVI", "EVI", "SAVI", "Soil_Moisture"],
    "C: + Elevation (full)":                ["NDVI", "EVI", "SAVI", "Soil_Moisture", "Elevation"],
    "D: WITHOUT leaked features (EVI+SAVI+Elevation only)": ["EVI", "SAVI", "Elevation"],
}

results = []
for name, feats in feature_sets.items():
    X = df[feats]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, stratify=y, random_state=42
    )
    model = RandomForestClassifier(n_estimators=200, random_state=42, class_weight="balanced")
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    macro_f1 = f1_score(y_test, y_pred, average='macro')
    results.append((name, macro_f1))
    print(f"\n=== {name} ===")
    print(f"Macro-F1: {macro_f1:.4f}")
    print(classification_report(y_test, y_pred, zero_division=0))

print("\n\n=== SUMMARY TABLE ===")
for name, score in results:
    print(f"{name:55s}  Macro-F1 = {score:.4f}")