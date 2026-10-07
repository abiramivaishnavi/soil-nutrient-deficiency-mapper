"""
compute_indices_npk_region_v2.py

Extends compute_indices_npk_region.py to also compute NDVI, NDRE, and
GNDVI (in addition to EVI, SAVI) for the expanded Sakri Taluka NPK region.
Cheap to add since the raw 5-band imagery is already downloaded.
"""

import rasterio
import numpy as np
import os
import pickle

folder = "sakri_npk_region_imagery"
subfolders = [f for f in os.listdir(folder) if os.path.isdir(os.path.join(folder, f))]
tiff_path = os.path.join(folder, subfolders[0], "response.tiff")

with rasterio.open(tiff_path) as src:
    blue    = src.read(1).astype(float)  # B02
    green   = src.read(2).astype(float)  # B03
    red     = src.read(3).astype(float)  # B04
    rededge = src.read(4).astype(float)  # B05
    nir     = src.read(5).astype(float)  # B08
    profile = src.profile
    transform = src.transform

def safe_div(a, b):
    return np.divide(a, b, out=np.zeros_like(a), where=b != 0)

ndvi = safe_div(nir - red, nir + red)
ndre = safe_div(nir - rededge, nir + rededge)
L, C1, C2, G = 1, 6, 7.5, 2.5
evi = G * safe_div(nir - red, nir + C1 * red - C2 * blue + L)
savi = safe_div((nir - red) * 1.5, (nir + red + 0.5))
gndvi = safe_div(nir - green, nir + green)

# Clip EVI to a sane range -- the raw computation blows up at near-zero
# denominators (water/cloud/no-data pixels elsewhere in the larger region)
evi_clipped = np.clip(evi, -1, 1)

os.makedirs("sakri_npk_region_indices", exist_ok=True)
indices = {"NDVI": ndvi, "NDRE": ndre, "EVI": evi_clipped, "SAVI": savi, "GNDVI": gndvi}
for name, arr in indices.items():
    np.save(f"sakri_npk_region_indices/{name}.npy", arr)
    print(f"{name}: mean={arr.mean():.3f}, min={arr.min():.3f}, max={arr.max():.3f}")

with open("sakri_npk_region_indices/raster_profile.pkl", "wb") as f:
    pickle.dump({"profile": profile, "transform": transform}, f)

print("\nSaved NDVI, NDRE, EVI (clipped), SAVI, GNDVI, and raster_profile.pkl")