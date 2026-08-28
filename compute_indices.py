import rasterio
import numpy as np
import matplotlib.pyplot as plt
import os

dates = ["2026-01-05", "2026-02-24", "2026-03-06"]

for date in dates:
    folder = f"data/{date}"
    subfolders = [f for f in os.listdir(folder) if os.path.isdir(os.path.join(folder, f))]
    tiff_path = os.path.join(folder, subfolders[0], "response.tiff")

    with rasterio.open(tiff_path) as src:
        red = src.read(1).astype(float)       # B04
        red_edge = src.read(2).astype(float)  # B05
        nir = src.read(3).astype(float)       # B08

    # NDVI = (NIR - Red) / (NIR + Red)
    ndvi = np.divide((nir - red), (nir + red), out=np.zeros_like(nir), where=(nir + red) != 0)

    # NDRE = (NIR - RedEdge) / (NIR + RedEdge)
    ndre = np.divide((nir - red_edge), (nir + red_edge), out=np.zeros_like(nir), where=(nir + red_edge) != 0)

    print(f"{date}: NDVI mean={ndvi.mean():.3f}, NDRE mean={ndre.mean():.3f}")

    # Save visual outputs
    plt.imsave(f"data/{date}/ndvi_{date}.png", ndvi, cmap="RdYlGn", vmin=-1, vmax=1)
    plt.imsave(f"data/{date}/ndre_{date}.png", ndre, cmap="RdYlGn", vmin=-1, vmax=1)

    # Save raw arrays for later steps (zoning)
    np.save(f"data/{date}/ndvi_{date}.npy", ndvi)
    np.save(f"data/{date}/ndre_{date}.npy", ndre)

print("Done — check each data/<date>/ folder for ndvi_*.png and ndre_*.png")