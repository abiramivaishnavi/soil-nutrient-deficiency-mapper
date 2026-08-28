import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

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

# Get class probabilities for every test point
probs = model.predict_proba(X_test)
predicted_class = model.classes_[np.argmax(probs, axis=1)]
confidence = np.max(probs, axis=1)  # highest probability = model's confidence

results = pd.DataFrame({
    'predicted_class': predicted_class,
    'confidence': confidence
})

# Bucket into High / Medium / Low confidence
def confidence_bucket(c):
    if c >= 0.75:
        return "High"
    elif c >= 0.5:
        return "Medium"
    else:
        return "Low"

results['confidence_level'] = results['confidence'].apply(confidence_bucket)

print("=== CONFIDENCE DISTRIBUTION ===")
print(results['confidence_level'].value_counts())
print("\nMean confidence:", results['confidence'].mean())
print("\nSample predictions:")
print(results.head(10))

results.to_csv("predictions_with_confidence.csv", index=False)
print("\nSaved to predictions_with_confidence.csv")