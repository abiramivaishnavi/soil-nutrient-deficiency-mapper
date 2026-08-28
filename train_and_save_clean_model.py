import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, f1_score
import joblib

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

y_pred = model.predict(X_test)
print("Macro-F1:", f1_score(y_test, y_pred, average='macro'))
print(classification_report(y_test, y_pred))

joblib.dump(model, "fertility_rf_model_clean.pkl")
print("\nSaved clean (non-leaked) model as fertility_rf_model_clean.pkl")