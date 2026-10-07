"""
extract_features_at_npk_points.py

For each of the 171 NPK sample points (SHC_Sakri_NPK_All_Observations.csv),
looks up the corresponding EVI, SAVI, and Elevation values from the rasters
computed for the expanded Sakri Taluka region, using each point's lat/lon.

Output: Sakri_NPK_with_features.csv -- one row per observation, with
Nitrogen_kg_ha, Phosphorus_kg_ha, Potassium_kg_ha, EVI, SAVI, Elevation,
plus a Location_ID column (grouping by unique lat/lon) needed for the
group-based train/test split in the next script, since many observations
share identical coordinates (multiple readings at the same village point).

IMPORTANT: update NPK_CSV_PATH below to match wherever you saved the
Soil Health Card CSV in your project.
"""

import pandas as pd
import numpy as np
import rasterio
import pickle
import os

NPK_CSV_PATH = "SHC_Sakri_NPK_All_Observations.csv"  # <-- update if your filename differs

# --- Load NPK observations ---
npk_df = pd.read_csv(NPK_CSV_PATH)
print(f"Loaded {len(npk_df)} NPK observations across "
      f"{npk_df['Village'].nunique()} villages.")

# --- Load EVI/SAVI + transform ---
evi = np.load("sakri_npk_region_indices/EVI.npy")
savi = np.load("sakri_npk_region_indices/SAVI.npy")
with open("sakri_npk_region_indices/raster_profile.pkl", "rb") as f:
    saved = pickle.load(f)
    transform = saved["transform"]

# --- Load Elevation (same bbox/grid, so same transform applies) ---
elev_folder = "sakri_npk_region_elevation"
elev_sub = os.listdir(elev_folder)[0]
with rasterio.open(f"{elev_folder}/{elev_sub}/response.tiff") as src:
    elevation = src.read(1)

h, w = evi.shape
print(f"Raster grid: {h} x {w} pixels")

# --- Extract feature values at each point ---
rows_out = []
out_of_bounds = 0

for _, row in npk_df.iterrows():
    lat, lon = row["Latitude"], row["Longitude"]
    pixel_row, pixel_col = rasterio.transform.rowcol(transform, lon, lat)

    if not (0 <= pixel_row < h and 0 <= pixel_col < w):
        out_of_bounds += 1
        continue

    rows_out.append({
        "Record_ID": row["Record_ID"],
        "Village": row["Village"],
        "Latitude": lat,
        "Longitude": lon,
        "Location_ID": f"{lat:.5f}_{lon:.5f}",  # groups duplicate-coordinate readings
        "Nitrogen_kg_ha": row["Nitrogen_kg_ha"],
        "Phosphorus_kg_ha": row["Phosphorus_kg_ha"],
        "Potassium_kg_ha": row["Potassium_kg_ha"],
        "EVI": evi[pixel_row, pixel_col],
        "SAVI": savi[pixel_row, pixel_col],
        "Elevation": elevation[pixel_row, pixel_col],
    })

if out_of_bounds:
    print(f"\nWARNING: {out_of_bounds} points fell outside the fetched raster bounds "
          f"and were skipped. Check the bbox in fetch_sakri_npk_region_imagery.py.")

merged_df = pd.DataFrame(rows_out)
merged_df.to_csv("Sakri_NPK_with_features.csv", index=False)

print(f"\nSuccessfully matched {len(merged_df)} / {len(npk_df)} observations to satellite features.")
print(f"Unique locations (for group-based validation): {merged_df['Location_ID'].nunique()}")
print(f"\nFeature summary:")
print(merged_df[["EVI", "SAVI", "Elevation", "Nitrogen_kg_ha", "Phosphorus_kg_ha", "Potassium_kg_ha"]].describe())
print("\nSaved Sakri_NPK_with_features.csv")