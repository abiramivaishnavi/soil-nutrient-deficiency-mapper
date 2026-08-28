import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
import os

dates = ["2026-01-05", "2026-02-24", "2026-03-06"]

for date in dates:
    ndvi = np.load(f"data/{date}/ndvi_{date}.npy")
    ndre = np.load(f"data/{date}/ndre_{date}.npy")

    # Stack NDVI and NDRE as features per pixel
    h, w = ndvi.shape
    features = np.stack([ndvi.flatten(), ndre.flatten()], axis=1)

    # K-Means into 3 zones
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    labels = kmeans.fit_predict(features)

    # Sort cluster centers by NDVI so 0=Severe, 1=Moderate, 2=Healthy consistently
    centers = kmeans.cluster_centers_
    order = np.argsort(centers[:, 0])  # sort by NDVI value
    label_map = {old: new for new, old in enumerate(order)}
    sorted_labels = np.array([label_map[l] for l in labels])

    zone_map = sorted_labels.reshape(h, w)
    np.save(f"data/{date}/zonemap_{date}.npy", zone_map)
    # Visualize: 0=red(severe), 1=yellow(moderate), 2=green(healthy)
    from matplotlib.colors import ListedColormap
    cmap = ListedColormap(["#B23A2E", "#D98E2B", "#1F4A2C"])
    
    plt.imsave(f"data/{date}/zones_{date}.png", zone_map, cmap=cmap)

    # Print zone area breakdown
    unique, counts = np.unique(zone_map, return_counts=True)
    total = zone_map.size
    zone_names = {0: "Severe", 1: "Moderate", 2: "Healthy"}
    print(f"\n{date}:")
    for u, c in zip(unique, counts):
        print(f"  {zone_names[u]}: {c/total*100:.1f}% of area")

print("\nDone — check data/<date>/zones_<date>.png")