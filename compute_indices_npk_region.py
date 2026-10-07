"""
compute_indices_npk_region.py

Computes EVI and SAVI (the two spectral indices used in the Phase 1 model)
for the EXPANDED Sakri Taluka NPK region, using the same formulas as
compute_all_indices.py for consistency.

Also saves the raster's affine transform/profile, which the next script
(extract_features_at_npk_points.py) needs to convert each NPK sample's
lat/lon into a pixel row/col.
"""

import rasterio
import numpy as np
import os
import pickle

folder = "sakri_npk_region_imagery"
subfolders = [f for f in os.listdir(folder) if os.path.isdir(os.path.join(folder, f))]
tiff_path = os.path.join(folder, subfolders[0], "response.tiff")

with rasterio.open(tiff_path) as src:
    blue  = src.read(1).astype(float)  # B02
    red   = src.read(3).astype(float)  # B04
    nir   = src.read(5).astype(float)  # B08
    profile = src.profile
    transform = src.transform

def safe_div(a, b):
    return np.divide(a, b, out=np.zeros_like(a), where=b != 0)

L, C1, C2, G = 1, 6, 7.5, 2.5
evi = G * safe_div(nir - red, nir + C1 * red - C2 * blue + L)
savi = safe_div((nir - red) * 1.5, (nir + red + 0.5))

os.makedirs("sakri_npk_region_indices", exist_ok=True)
np.save("sakri_npk_region_indices/EVI.npy", evi)
np.save("sakri_npk_region_indices/SAVI.npy", savi)

with open("sakri_npk_region_indices/raster_profile.pkl", "wb") as f:
    pickle.dump({"profile": profile, "transform": transform}, f)

print(f"EVI: mean={evi.mean():.3f}, min={evi.min():.3f}, max={evi.max():.3f}")
print(f"SAVI: mean={savi.mean():.3f}, min={savi.min():.3f}, max={savi.max():.3f}")
print("\nSaved EVI.npy, SAVI.npy, and raster_profile.pkl to sakri_npk_region_indices/")