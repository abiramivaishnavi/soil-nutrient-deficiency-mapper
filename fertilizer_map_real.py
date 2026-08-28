import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

fertility_map = np.load("sakri_predictions/fertility_map_real.npy", allow_pickle=True)

RDF_N, RDF_P, RDF_K = 60, 50, 50
RATE_MULTIPLIER = {"Low": 1.30, "Moderate": 1.00, "High": 0.70, "Very High": 0.40}

# Build fertilizer rate maps
n_map = np.vectorize(lambda c: RDF_N * RATE_MULTIPLIER[c])(fertility_map)
p_map = np.vectorize(lambda c: RDF_P * RATE_MULTIPLIER[c])(fertility_map)
k_map = np.vectorize(lambda c: RDF_K * RATE_MULTIPLIER[c])(fertility_map)

# Study area stats
PIXEL_AREA_HA = (100 / 1024) * (100 / 1024) * 111.32 * 111.32  # rough km->ha conversion for a 1024x1024 grid over ~10km
# Simpler: use actual bbox area
lat_span = 20.97004741366508 - 20.87006492254258
lon_span = 74.41998648183345 - 74.32000399071094
area_km2 = lat_span * 111.0 * lon_span * 111.0 * np.cos(np.radians(20.92))
total_area_ha = area_km2 * 100
pixel_area_ha = total_area_ha / fertility_map.size

variable_N_total = n_map.sum() * pixel_area_ha
uniform_N_total = RDF_N * total_area_ha
diff_pct = (variable_N_total - uniform_N_total) / uniform_N_total * 100

print("=== FERTILIZER RECOMMENDATION — REAL SATELLITE RASTER (Sakri, cotton) ===")
print(f"Study area: {total_area_ha:.1f} ha")
print(f"Variable-rate total N needed: {variable_N_total:.1f} kg")
print(f"Uniform RDF total N needed:   {uniform_N_total:.1f} kg")
print(f"Difference vs uniform: {diff_pct:+.1f}%")

class_colors = {"Low": "#B23A2E", "Moderate": "#D98E2B", "High": "#6E9F5E", "Very High": "#1F4A2C"}
color_map = np.vectorize(class_colors.get)(fertility_map)
rgb_map = np.zeros((*fertility_map.shape, 3), dtype=np.uint8)
for cls, hexcolor in class_colors.items():
    mask = fertility_map == cls
    rgb = tuple(int(hexcolor[i:i+2], 16) for i in (1, 3, 5))
    rgb_map[mask] = rgb

plt.imsave("sakri_predictions/fertilizer_zones_real.png", rgb_map)

np.save("sakri_predictions/n_map.npy", n_map)
np.save("sakri_predictions/p_map.npy", p_map)
np.save("sakri_predictions/k_map.npy", k_map)

print("\nSaved fertilizer_zones_real.png, n_map.npy, p_map.npy, k_map.npy")