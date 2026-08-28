import numpy as np
import matplotlib.pyplot as plt
import os

os.makedirs("dashboard/public", exist_ok=True)

indices = ["NDVI", "NDRE", "EVI", "SAVI", "GNDVI"]
index_ranges = {
    "NDVI": (-1, 1), "NDRE": (-1, 1), "EVI": (-1, 1), "SAVI": (-1, 1), "GNDVI": (-1, 1)
}

means = {}
for idx in indices:
    arr = np.load(f"sakri_indices/{idx}.npy")
    arr_clipped = np.clip(arr, *index_ranges[idx])
    vmin, vmax = index_ranges[idx]
    plt.imsave(f"dashboard/public/{idx.lower()}_overlay.png", arr_clipped, cmap="RdYlGn", vmin=vmin, vmax=vmax)
    means[idx] = round(float(arr_clipped.mean()), 3)
    print(f"{idx}: mean={means[idx]}")

import json
with open("dashboard/public/index_stats.json", "w") as f:
    json.dump(means, f, indent=2)

print("\nSaved 5 index overlays to dashboard/public/")