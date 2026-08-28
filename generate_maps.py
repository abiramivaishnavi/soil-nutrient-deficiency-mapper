import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

df = pd.read_csv("Sakri_Soil_Fertility_Version_2.csv")
df = df[(df['NDVI'] >= -1) & (df['NDVI'] <= 1)]
df = df[(df['EVI'] >= -1) & (df['EVI'] <= 1)]

features = ["EVI", "SAVI", "Elevation"]
X = df[features]
y = df["Fertility_Level"]

# Train final model on ALL data (not just train split) for the production map
model = RandomForestClassifier(n_estimators=200, random_state=42, class_weight="balanced")
model.fit(X, y)

probs = model.predict_proba(X)
predicted_class = model.classes_[np.argmax(probs, axis=1)]
confidence = np.max(probs, axis=1)

df['predicted_fertility'] = predicted_class
df['confidence'] = confidence

# --- Map 1: Fertility classification map ---
class_colors = {"Low": "#B23A2E", "Moderate": "#D98E2B", "High": "#6E9F5E", "Very High": "#1F4A2C"}
colors = df['predicted_fertility'].map(class_colors)

plt.figure(figsize=(10, 8))
plt.scatter(df['Longitude'], df['Latitude'], c=colors, s=1)
plt.title("Predicted Soil Fertility Map — Sakri Region")
plt.xlabel("Longitude")
plt.ylabel("Latitude")
handles = [plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=c, markersize=8, label=lbl)
           for lbl, c in class_colors.items()]
plt.legend(handles=handles, title="Fertility Class")
plt.tight_layout()
plt.savefig("fertility_map.png", dpi=150)
print("Saved fertility_map.png")

# --- Map 2: Confidence map ---
plt.figure(figsize=(10, 8))
sc = plt.scatter(df['Longitude'], df['Latitude'], c=df['confidence'], cmap='RdYlGn', s=1, vmin=0, vmax=1)
plt.colorbar(sc, label="Prediction Confidence")
plt.title("Prediction Confidence Map — Sakri Region")
plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.tight_layout()
plt.savefig("confidence_map.png", dpi=150)
print("Saved confidence_map.png")

df.to_csv("full_predictions.csv", index=False)
print("Saved full_predictions.csv")