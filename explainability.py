import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance

df = pd.read_csv("Sakri_Soil_Fertility_Version_2.csv")
df = df[(df['NDVI'] >= -1) & (df['NDVI'] <= 1)]
df = df[(df['EVI'] >= -1) & (df['EVI'] <= 1)]

features = ["EVI", "SAVI", "Elevation"]
X = df[features]
y = df["Fertility_Level"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, stratify=y, random_state=42
)

model = RandomForestClassifier(n_estimators=200, random_state=42, class_weight="balanced")
model.fit(X_train, y_train)

result = permutation_importance(
    model, X_test, y_test, n_repeats=10, random_state=42, scoring='f1_macro'
)

importance_df = pd.DataFrame({
    'feature': features,
    'importance_mean': result.importances_mean,
    'importance_std': result.importances_std
}).sort_values('importance_mean', ascending=False)

print("=== PERMUTATION IMPORTANCE (impact on Macro-F1) ===")
print(importance_df)