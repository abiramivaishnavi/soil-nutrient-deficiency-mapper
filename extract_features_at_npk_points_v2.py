"""
extract_features_at_npk_points_v2.py

Extends extract_features_at_npk_points.py to pull all 5 spectral indices
(NDVI, NDRE, EVI, SAVI, GNDVI) plus Elevation at each of the 171 NPK
sample points, instead of just EVI+SAVI+Elevation.
"""

import pandas as pd
import numpy as np
import rasterio
import pickle
import os

NPK_CSV_PATH = "SHC_Sakri_NPK_All_Observations.csv"

npk_df = pd.read_csv(NPK_CSV_PATH)
print(f"Loaded {len(npk_df)} NPK observations across {npk_df['Village'].nunique()} villages.")

INDEX_NAMES = ["NDVI", "NDRE", "EVI", "SAVI", "GNDVI"]
index_arrays = {name: np.load(f"sakri_npk_region_indices/{name}.npy") for name in INDEX_NAMES}

with open("sakri_npk_region_indices/raster_profile.pkl", "rb") as f:
    transform = pickle.load(f)["transform"]

elev_folder = "sakri_npk_region_elevation"
elev_sub = os.listdir(elev_folder)[0]
with rasterio.open(f"{elev_folder}/{elev_sub}/response.tiff") as src:
    elevation = src.read(1)

h, w = index_arrays["NDVI"].shape
rows_out = []
out_of_bounds = 0

for _, row in npk_df.iterrows():
    lat, lon = row["Latitude"], row["Longitude"]
    pixel_row, pixel_col = rasterio.transform.rowcol(transform, lon, lat)

    if not (0 <= pixel_row < h and 0 <= pixel_col < w):
        out_of_bounds += 1
        continue

    record = {
        "Record_ID": row["Record_ID"],
        "Village": row["Village"],
        "Latitude": lat,
        "Longitude": lon,
        "Location_ID": f"{lat:.5f}_{lon:.5f}",
        "Nitrogen_kg_ha": row["Nitrogen_kg_ha"],
        "Phosphorus_kg_ha": row["Phosphorus_kg_ha"],
        "Potassium_kg_ha": row["Potassium_kg_ha"],
        "Elevation": elevation[pixel_row, pixel_col],
    }
    for name in INDEX_NAMES:
        record[name] = index_arrays[name][pixel_row, pixel_col]

    rows_out.append(record)

if out_of_bounds:
    print(f"\nWARNING: {out_of_bounds} points fell outside raster bounds and were skipped.")

merged_df = pd.DataFrame(rows_out)
merged_df.to_csv("Sakri_NPK_with_features_v2.csv", index=False)

print(f"\nMatched {len(merged_df)} / {len(npk_df)} observations.")
print(f"Unique locations: {merged_df['Location_ID'].nunique()}")
print("\nSaved Sakri_NPK_with_features_v2.csv (5 spectral indices + Elevation)")