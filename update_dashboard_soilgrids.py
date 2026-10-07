import numpy as np
import json

# Load existing stats.json so we add to it, not overwrite everything
with open("dashboard/public/stats.json", "r") as f:
    stats = json.load(f)

nitrogen = np.load("sakri_predictions/nitrogen_gkg.npy")
cec = np.load("sakri_predictions/cec_mmolkg.npy")

stats["soilgrids_layers"] = {
    "nitrogen": {
        "mean_g_per_kg": round(float(np.nanmean(nitrogen)), 3),
        "min_g_per_kg": round(float(np.nanmin(nitrogen)), 3),
        "max_g_per_kg": round(float(np.nanmax(nitrogen)), 3),
        "source": "SoilGrids v2.0 (ISRIC) — globally modelled reference layer, 250m resolution",
    },
    "cec_potassium_proxy": {
        "mean_mmol_per_kg": round(float(np.nanmean(cec)), 3),
        "min_mmol_per_kg": round(float(np.nanmin(cec)), 3),
        "max_mmol_per_kg": round(float(np.nanmax(cec)), 3),
        "source": "SoilGrids v2.0 (ISRIC) — Cation Exchange Capacity, used as an established proxy for potassium-holding capacity",
    }
}

with open("dashboard/public/stats.json", "w") as f:
    json.dump(stats, f, indent=2)

print("Added SoilGrids Nitrogen and CEC(K-proxy) stats to stats.json")
print(json.dumps(stats["soilgrids_layers"], indent=2))