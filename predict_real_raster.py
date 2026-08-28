import numpy as np
import rasterio
import joblib
import pickle
import matplotlib.pyplot as plt
import pandas as pd
import os

# --- Load the trained model ---
model = joblib.load("fertility_rf_model_clean.pkl")

# --- Load computed indices (EVI, SAVI) ---
evi = np.load("sakri_indices/EVI.npy")
savi = np.load("sakri_indices/SAVI.npy")

# --- Load elevation, resampled to match EVI/SAVI grid if needed ---
elev_folder = "sakri_elevation"
elev_sub = os.listdir(elev_folder)[0]
with rasterio.open(f"{elev_folder}/{elev_sub}/response.tiff") as src:
    elevation = src.read(1)

print("EVI shape:", evi.shape, " SAVI shape:", savi.shape, " Elevation shape:", elevation.shape)

# --- Flatten into a feature table (one row per pixel) ---
h, w = evi.shape
X_raster = pd.DataFrame({
    "EVI": evi.flatten(),
    "SAVI": savi.flatten(),
    "Elevation": elevation.flatten(),
})
# --- Domain-shift correction: rescale raster features to match training distribution ---
train_df = pd.read_csv("Sakri_Soil_Fertility_Version_2.csv")
train_df = train_df[(train_df['NDVI'] >= -1) & (train_df['NDVI'] <= 1)]
train_df = train_df[(train_df['EVI'] >= -1) & (train_df['EVI'] <= 1)]

def rescale_to_match(raster_col, train_col):
    r_min, r_max = raster_col.min(), raster_col.max()
    t_min, t_max = train_col.min(), train_col.max()
    normalized = (raster_col - r_min) / (r_max - r_min + 1e-9)
    return normalized * (t_max - t_min) + t_min

# --- ACTUALLY APPLY the rescaling (this was missing) ---
X_raster['EVI'] = rescale_to_match(X_raster['EVI'], train_df['EVI'])
X_raster['SAVI'] = rescale_to_match(X_raster['SAVI'], train_df['SAVI'])

# --- Safety clip after rescaling ---
X_raster['EVI'] = X_raster['EVI'].clip(-1, 1)
X_raster['SAVI'] = X_raster['SAVI'].clip(-1, 1)
X_raster['Elevation'] = X_raster['Elevation'].clip(0, 2000)

# --- Predict fertility class + confidence for every pixel ---
predicted_class = model.predict(X_raster)
probs = model.predict_proba(X_raster)
confidence = np.max(probs, axis=1)
fertility_map = predicted_class.reshape(h, w)
confidence_map = confidence.reshape(h, w)

# --- Save visual outputs ---
class_colors = {"Low": 0, "Moderate": 1, "High": 2, "Very High": 3}
color_list = ["#B23A2E", "#D98E2B", "#6E9F5E", "#1F4A2C"]

from matplotlib.colors import ListedColormap
cmap = ListedColormap(color_list)
numeric_map = np.vectorize(class_colors.get)(fertility_map)

os.makedirs("sakri_predictions", exist_ok=True)
plt.imsave("sakri_predictions/fertility_map_real.png", numeric_map, cmap=cmap)
plt.imsave("sakri_predictions/confidence_map_real.png", confidence_map, cmap="RdYlGn", vmin=0, vmax=1)

np.save("sakri_predictions/fertility_map_real.npy", fertility_map)
np.save("sakri_predictions/confidence_map_real.npy", confidence_map)

print("\n=== PREDICTION SUMMARY (real satellite imagery, Sakri) ===")
unique, counts = np.unique(fertility_map, return_counts=True)
for cls, cnt in zip(unique, counts):
    print(f"{cls}: {cnt} pixels ({cnt/fertility_map.size*100:.1f}%)")
print(f"\nMean confidence: {confidence_map.mean():.3f}")
print("\nSaved fertility_map_real.png and confidence_map_real.png to sakri_predictions/")