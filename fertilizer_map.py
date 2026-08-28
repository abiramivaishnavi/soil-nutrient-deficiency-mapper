import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

df = pd.read_csv("full_predictions.csv")

# --- Rule-based fertilizer recommendation ---
# Reference: Maharashtra cotton RDF (N:P:K = 60:50:50 kg/ha)
RDF_N, RDF_P, RDF_K = 60, 50, 50

RATE_MULTIPLIER = {
    "Low": 1.30,
    "Moderate": 1.00,
    "High": 0.70,
    "Very High": 0.40,
}

df['rate_multiplier'] = df['predicted_fertility'].map(RATE_MULTIPLIER)
df['N_kg_ha'] = (RDF_N * df['rate_multiplier']).round(1)
df['P_kg_ha'] = (RDF_P * df['rate_multiplier']).round(1)
df['K_kg_ha'] = (RDF_K * df['rate_multiplier']).round(1)

# --- Summary: total fertilizer needed vs uniform baseline ---
PIXEL_AREA_HA = 0.09  # 30m x 30m = 900 sq.m = 0.09 ha
total_area_ha = len(df) * PIXEL_AREA_HA

variable_N_total = (df['N_kg_ha'] * PIXEL_AREA_HA).sum()
uniform_N_total = RDF_N * total_area_ha

print("=== FERTILIZER RECOMMENDATION SUMMARY (Nitrogen, cotton) ===")
print(f"Study area: {total_area_ha:.1f} ha")
print(f"Variable-rate total N needed: {variable_N_total:.1f} kg")
print(f"Uniform RDF total N needed:   {uniform_N_total:.1f} kg")
diff_pct = (variable_N_total - uniform_N_total) / uniform_N_total * 100
print(f"Difference vs uniform: {diff_pct:+.1f}%")

print("\nRate distribution by class:")
print(df.groupby('predicted_fertility')[['N_kg_ha', 'P_kg_ha', 'K_kg_ha']].first())

# --- Map: N application rate ---
rate_colors = {"Low": "#B23A2E", "Moderate": "#D98E2B", "High": "#6E9F5E", "Very High": "#1F4A2C"}
colors = df['predicted_fertility'].map(rate_colors)

plt.figure(figsize=(10, 8))
plt.scatter(df['Longitude'], df['Latitude'], c=colors, s=1)
plt.title("Variable-Rate Nitrogen Application Zones — Cotton (Sakri Region)")
plt.xlabel("Longitude")
plt.ylabel("Latitude")
handles = [plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=c, markersize=8,
           label=f"{lbl} ({RATE_MULTIPLIER[lbl]*100:.0f}% RDF = {RDF_N*RATE_MULTIPLIER[lbl]:.0f} kg N/ha)")
           for lbl, c in rate_colors.items()]
plt.legend(handles=handles, title="Fertility Class → N Rate", fontsize=8)
plt.tight_layout()
plt.savefig("fertilizer_map.png", dpi=150)
print("\nSaved fertilizer_map.png")

df.to_csv("fertilizer_recommendations.csv", index=False)
print("Saved fertilizer_recommendations.csv")