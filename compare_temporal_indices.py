"""
compare_temporal_indices.py

Compares DATE 1 (Aug-Sep 2024, mid-monsoon) vs DATE 2 (Dec 2024-Jan 2025,
post-harvest) for Sakri:
  1. Index-level comparison (NDVI/EVI/SAVI mean shift)
  2. Fertility-zone classification shift (using the SAME clean model,
     fertility_rf_model_clean.pkl, applied to both dates' EVI+SAVI+Elevation)

This directly implements "Module 8: Temporal Analysis" from the project plan.

IMPORTANT — what this can and cannot claim:
- A shift in predicted fertility class between two dates does NOT necessarily
  mean the underlying soil fertility changed. EVI/SAVI are vegetation indices;
  changes largely reflect CROP STAGE (harvested/bare vs actively growing),
  not soil nutrient content itself. This script frames results accordingly:
  as a demonstration of index/prediction sensitivity to acquisition date,
  not as evidence of real fertility change. This caveat should also appear
  in the paper wherever these numbers are used.

Requires: date1 indices already computed (sakri_indices/), date2 indices
already computed (sakri_indices_date2/), and fertility_rf_model_clean.pkl
already trained.
"""

import numpy as np
import joblib
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import rasterio
import os

os.makedirs("dashboard/public", exist_ok=True)
os.makedirs("sakri_predictions", exist_ok=True)

# =============================================================================
# STEP 1: Index-level comparison (raw NDVI/EVI/SAVI means, both dates)
# =============================================================================
print("=" * 70)
print("STEP 1: SPECTRAL INDEX COMPARISON — DATE 1 vs DATE 2")
print("=" * 70)

indices_to_compare = ["NDVI", "NDRE", "EVI", "SAVI", "GNDVI"]
index_summary = []

for idx in indices_to_compare:
    date1_arr = np.load(f"sakri_indices/{idx}.npy")
    date2_arr = np.load(f"sakri_indices_date2/{idx}.npy")
    d1_mean, d2_mean = float(date1_arr.mean()), float(date2_arr.mean())
    change = d2_mean - d1_mean
    change_pct = (change / abs(d1_mean)) * 100 if d1_mean != 0 else float("nan")
    index_summary.append({
        "index": idx, "date1_mean": round(d1_mean, 3), "date2_mean": round(d2_mean, 3),
        "change": round(change, 3), "change_pct": round(change_pct, 1)
    })
    print(f"{idx:6s}  Date1={d1_mean:+.3f}  Date2={d2_mean:+.3f}  "
          f"Change={change:+.3f} ({change_pct:+.1f}%)")

# =============================================================================
# STEP 2: Elevation is reused (terrain doesn't change between dates)
# =============================================================================
elev_folder = "sakri_elevation"
elev_sub = os.listdir(elev_folder)[0]
with rasterio.open(f"{elev_folder}/{elev_sub}/response.tiff") as src:
    elevation = src.read(1)

# =============================================================================
# STEP 3: Predict fertility for BOTH dates using the SAME clean model
# =============================================================================
print("\n" + "=" * 70)
print("STEP 2: FERTILITY-ZONE PREDICTION — DATE 1 vs DATE 2")
print("=" * 70)

model = joblib.load("fertility_rf_model_clean.pkl")

train_df = pd.read_csv("Sakri_Soil_Fertility_Version_2.csv")
train_df = train_df[(train_df['NDVI'] >= -1) & (train_df['NDVI'] <= 1)]
train_df = train_df[(train_df['EVI'] >= -1) & (train_df['EVI'] <= 1)]

def rescale_to_match(raster_col, train_col):
    """Same domain-shift correction used in predict_real_raster.py"""
    r_min, r_max = raster_col.min(), raster_col.max()
    t_min, t_max = train_col.min(), train_col.max()
    normalized = (raster_col - r_min) / (r_max - r_min + 1e-9)
    return normalized * (t_max - t_min) + t_min

def predict_fertility_for_date(evi_path, savi_path, elevation, train_df, label):
    evi = np.load(evi_path)
    savi = np.load(savi_path)
    h, w = evi.shape

    X_raster = pd.DataFrame({
        "EVI": evi.flatten(),
        "SAVI": savi.flatten(),
        "Elevation": elevation.flatten(),
    })
    X_raster['EVI'] = rescale_to_match(X_raster['EVI'], train_df['EVI'])
    X_raster['SAVI'] = rescale_to_match(X_raster['SAVI'], train_df['SAVI'])
    X_raster['EVI'] = X_raster['EVI'].clip(-1, 1)
    X_raster['SAVI'] = X_raster['SAVI'].clip(-1, 1)
    X_raster['Elevation'] = X_raster['Elevation'].clip(0, 2000)

    predicted_class = model.predict(X_raster)
    fertility_map = predicted_class.reshape(h, w)

    unique, counts = np.unique(fertility_map, return_counts=True)
    total = fertility_map.size
    print(f"\n--- {label} ---")
    for cls, cnt in zip(unique, counts):
        print(f"  {cls}: {cnt} pixels ({cnt/total*100:.1f}%)")

    return fertility_map

fertility_date1 = predict_fertility_for_date(
    "sakri_indices/EVI.npy", "sakri_indices/SAVI.npy", elevation, train_df, "DATE 1 (Aug-Sep 2024)"
)
fertility_date2 = predict_fertility_for_date(
    "sakri_indices_date2/EVI.npy", "sakri_indices_date2/SAVI.npy", elevation, train_df, "DATE 2 (Dec 2024-Jan 2025)"
)

# =============================================================================
# STEP 4: Zone-shift table + change map
# =============================================================================
print("\n" + "=" * 70)
print("STEP 3: ZONE-SHIFT SUMMARY")
print("=" * 70)

classes = ["Low", "Moderate", "High", "Very High"]
total_pixels = fertility_date1.size

shift_table = []
for cls in classes:
    pct1 = (fertility_date1 == cls).sum() / total_pixels * 100
    pct2 = (fertility_date2 == cls).sum() / total_pixels * 100
    shift_table.append({"class": cls, "date1_pct": round(pct1, 1),
                         "date2_pct": round(pct2, 1), "shift_pct_points": round(pct2 - pct1, 1)})
    print(f"{cls:12s}  Date1={pct1:5.1f}%  Date2={pct2:5.1f}%  Shift={pct2-pct1:+.1f} pts")

# How many pixels changed class at all (regardless of direction)
pixels_changed = (fertility_date1 != fertility_date2).sum()
pct_changed = pixels_changed / total_pixels * 100
print(f"\nTotal pixels that changed predicted class between dates: "
      f"{pixels_changed} ({pct_changed:.1f}%)")

# --- Save comparison overlays for the dashboard ---
class_colors = {"Low": "#B23A2E", "Moderate": "#D98E2B", "High": "#6E9F5E", "Very High": "#1F4A2C"}

def save_overlay(fertility_map, filename):
    rgb_map = np.zeros((*fertility_map.shape, 3), dtype=np.uint8)
    for cls, hexcolor in class_colors.items():
        mask = fertility_map == cls
        rgb = tuple(int(hexcolor[i:i+2], 16) for i in (1, 3, 5))
        rgb_map[mask] = rgb
    plt.imsave(filename, rgb_map)

save_overlay(fertility_date1, "dashboard/public/fertility_date1_overlay.png")
save_overlay(fertility_date2, "dashboard/public/fertility_date2_overlay.png")

# Binary "did this pixel change class" map — useful visual for the paper
change_mask = (fertility_date1 != fertility_date2).astype(np.uint8)
plt.imsave("dashboard/public/fertility_change_overlay.png", change_mask, cmap="Reds", vmin=0, vmax=1)

np.save("sakri_predictions/fertility_map_date1.npy", fertility_date1)
np.save("sakri_predictions/fertility_map_date2.npy", fertility_date2)

# --- Save a summary JSON for the dashboard / paper ---
import json
temporal_summary = {
    "date1_range": "2024-08-01 to 2024-09-30 (mid-monsoon, peak vegetative)",
    "date2_range": "2024-12-01 to 2025-01-31 (post-harvest, dry season)",
    "index_comparison": index_summary,
    "fertility_zone_shift": shift_table,
    "pct_pixels_changed_class": round(pct_changed, 1),
    "important_caveat": (
        "Fertility-zone shifts here largely reflect crop growth stage "
        "(vegetation cover) differences between acquisition dates, not "
        "necessarily real changes in underlying soil fertility. EVI/SAVI "
        "are vegetation indices, sensitive to canopy state."
    )
}
with open("dashboard/public/temporal_summary.json", "w") as f:
    json.dump(temporal_summary, f, indent=2)

print("\nSaved: fertility_date1_overlay.png, fertility_date2_overlay.png,")
print("       fertility_change_overlay.png, temporal_summary.json")
print("\nIMPORTANT: report these results as index/prediction sensitivity to")
print("acquisition date -- NOT as evidence of real soil fertility change.")