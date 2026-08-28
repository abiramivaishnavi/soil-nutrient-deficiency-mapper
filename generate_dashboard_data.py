import numpy as np
import matplotlib.pyplot as plt
import json
import os

fertility_map = np.load("sakri_predictions/fertility_map_real.npy", allow_pickle=True)
confidence_map = np.load("sakri_predictions/confidence_map_real.npy")

lat_min, lat_max = 20.87006492254258, 20.97004741366508
lon_min, lon_max = 74.32000399071094, 74.41998648183345

class_colors = {"Low": "#B23A2E", "Moderate": "#D98E2B", "High": "#6E9F5E", "Very High": "#1F4A2C"}

os.makedirs("dashboard/public", exist_ok=True)

# --- Fertility overlay ---
rgb_map = np.zeros((*fertility_map.shape, 3), dtype=np.uint8)
for cls, hexcolor in class_colors.items():
    mask = fertility_map == cls
    rgb = tuple(int(hexcolor[i:i+2], 16) for i in (1, 3, 5))
    rgb_map[mask] = rgb
plt.imsave("dashboard/public/fertility_overlay.png", rgb_map)

# --- Confidence overlay ---
plt.imsave("dashboard/public/confidence_overlay.png", confidence_map, cmap="RdYlGn", vmin=0, vmax=1)

# --- Fertilizer overlay (same colors, different legend meaning) ---
plt.imsave("dashboard/public/fertilizer_overlay.png", rgb_map)

# --- Stats ---
unique, counts = np.unique(fertility_map, return_counts=True)
class_counts = dict(zip(unique.tolist(), counts.tolist()))
total = fertility_map.size
class_percent = {k: round(v / total * 100, 1) for k, v in class_counts.items()}

RDF_N, RDF_P, RDF_K = 60, 50, 50
RATE_MULTIPLIER = {"Low": 1.30, "Moderate": 1.00, "High": 0.70, "Very High": 0.40}

lat_span = lat_max - lat_min
lon_span = lon_max - lon_min
area_km2 = lat_span * 111.0 * lon_span * 111.0 * np.cos(np.radians((lat_min+lat_max)/2))
total_area_ha = round(area_km2 * 100, 1)
n_map = np.load("sakri_predictions/n_map.npy")
pixel_area_ha = total_area_ha / fertility_map.size
variable_N_total = round(float(n_map.sum() * pixel_area_ha), 1)
uniform_N_total = round(RDF_N * total_area_ha, 1)
diff_pct = round((variable_N_total - uniform_N_total) / uniform_N_total * 100, 1)

stats = {
    "fertilizer_totals": {
        "variable_rate_N_kg": variable_N_total,
        "uniform_N_kg": uniform_N_total,
        "difference_pct": diff_pct,
    },
    "bounds": [[lat_min, lon_min], [lat_max, lon_max]],
    "center": [(lat_min + lat_max) / 2, (lon_min + lon_max) / 2],
    "class_counts": class_counts,
    "class_percent": class_percent,
    "mean_confidence": round(float(confidence_map.mean()), 3),
    "total_area_ha": total_area_ha,
    "data_source": "Real Sentinel-2 imagery (Aug-Sep 2024) + Copernicus DEM, Sakri region",
    "fertilizer_rates": {
        cls: {"N": RDF_N * mult, "P": RDF_P * mult, "K": RDF_K * mult}
        for cls, mult in RATE_MULTIPLIER.items()
    }
}

with open("dashboard/public/stats.json", "w") as f:
    json.dump(stats, f, indent=2)

print("Dashboard now shows REAL satellite-derived analysis.")
print(json.dumps(stats, indent=2))