import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, f1_score
import joblib

df = pd.read_csv("Sakri_Soil_Fertility_Version_2.csv")

# --- Clean impossible outlier values ---
before = len(df)
df = df[(df['NDVI'] >= -1) & (df['NDVI'] <= 1)]
df = df[(df['EVI'] >= -1) & (df['EVI'] <= 1)]
after = len(df)
print(f"Removed {before - after} outlier rows ({before} -> {after})")

features = ["NDVI", "EVI", "SAVI", "Soil_Moisture", "Elevation"]
X = df[features]
y = df["Fertility_Level"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, stratify=y, random_state=42
)

model = RandomForestClassifier(n_estimators=200, random_state=42, class_weight="balanced")
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
print("\nAccuracy:", accuracy_score(y_test, y_pred))
print("Macro-F1:", f1_score(y_test, y_pred, average='macro'))
print("Weighted-F1:", f1_score(y_test, y_pred, average='weighted'))
print("\nClassification Report:\n", classification_report(y_test, y_pred))
print("\nConfusion Matrix:\n", confusion_matrix(y_test, y_pred))

importances = pd.Series(model.feature_importances_, index=features).sort_values(ascending=False)
print("\nFeature Importance:\n", importances)

joblib.dump(model, "fertility_rf_model.pkl")
print("\nModel saved.")