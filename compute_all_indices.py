import rasterio
import numpy as np
import matplotlib.pyplot as plt
import os
import pickle

folder = "sakri_imagery"
subfolders = [f for f in os.listdir(folder) if os.path.isdir(os.path.join(folder, f))]
tiff_path = os.path.join(folder, subfolders[0], "response.tiff")

with rasterio.open(tiff_path) as src:
    blue    = src.read(1).astype(float)  # B02
    green   = src.read(2).astype(float)  # B03
    red     = src.read(3).astype(float)  # B04
    rededge = src.read(4).astype(float)  # B05
    nir     = src.read(5).astype(float)  # B08
    profile = src.profile

def safe_div(a, b):
    return np.divide(a, b, out=np.zeros_like(a), where=b != 0)

ndvi = safe_div(nir - red, nir + red)
ndre = safe_div(nir - rededge, nir + rededge)

# Proper EVI, now using the real Blue band
L, C1, C2, G = 1, 6, 7.5, 2.5
evi = G * safe_div(nir - red, nir + C1 * red - C2 * blue + L)

savi = safe_div((nir - red) * 1.5, (nir + red + 0.5))
gndvi = safe_div(nir - green, nir + green)

indices = {"NDVI": ndvi, "NDRE": ndre, "EVI": evi, "SAVI": savi, "GNDVI": gndvi}

os.makedirs("sakri_indices", exist_ok=True)
for name, arr in indices.items():
    plt.imsave(f"sakri_indices/{name}.png", arr, cmap="RdYlGn", vmin=-1, vmax=1)
    np.save(f"sakri_indices/{name}.npy", arr)
    print(f"{name}: mean={arr.mean():.3f}, min={arr.min():.3f}, max={arr.max():.3f}")

with open("sakri_indices/raster_profile.pkl", "wb") as f:
    pickle.dump(profile, f)

print("\nAll 5 indices computed correctly (real Blue band used for EVI) and saved to sakri_indices/")