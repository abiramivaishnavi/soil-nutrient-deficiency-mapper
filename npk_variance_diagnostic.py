"""
npk_variance_diagnostic.py

Diagnoses WHY the N/P/K regression (train_npk_regression.py) performed
poorly, by decomposing variance into:
  - WITHIN-location variance: how much N/P/K varies between multiple
    readings taken at the exact same coordinate (same EVI/SAVI/Elevation)
  - TOTAL variance: how much N/P/K varies across the whole dataset

If within-location variance is a large fraction of total variance, that
sets a hard ceiling on how well ANY location-based feature (satellite or
otherwise) could ever predict these values -- the unexplainable noise
floor is high regardless of model choice.

Also reports simple Pearson correlations between each feature and each
target, to check whether there is any linear signal at all before
concluding the relationship is genuinely weak/absent.
"""

import pandas as pd
import numpy as np

df = pd.read_csv("Sakri_NPK_with_features.csv")
TARGETS = ["Nitrogen_kg_ha", "Phosphorus_kg_ha", "Potassium_kg_ha"]
FEATURES = ["EVI", "SAVI", "Elevation"]

print("=" * 70)
print("VARIANCE DECOMPOSITION: within-location vs total")
print("=" * 70)

loc_counts = df["Location_ID"].value_counts()
multi_reading_locs = loc_counts[loc_counts > 1].index
print(f"\n{len(multi_reading_locs)} of {df['Location_ID'].nunique()} locations "
      f"have multiple readings (needed for this diagnostic).\n")

for target in TARGETS:
    total_var = df[target].var()

    # Pooled within-location variance (average variance across locations
    # that have >1 reading, weighted by group size)
    within_var_list = []
    weights = []
    for loc in multi_reading_locs:
        group = df[df["Location_ID"] == loc][target]
        within_var_list.append(group.var())
        weights.append(len(group))

    pooled_within_var = np.average(within_var_list, weights=weights)
    explainable_fraction = 1 - (pooled_within_var / total_var)

    print(f"{target}:")
    print(f"  Total variance:                {total_var:.1f}")
    print(f"  Pooled within-location variance: {pooled_within_var:.1f}")
    print(f"  Max theoretically explainable variance (R^2 ceiling): "
          f"{explainable_fraction:.3f}")
    print(f"  -> Even a PERFECT model using only location-level features")
    print(f"     could not exceed R^2 = {explainable_fraction:.3f} for this target,")
    print(f"     because {(1-explainable_fraction)*100:.1f}% of the variance is")
    print(f"     noise BETWEEN readings at the identical same coordinate.\n")

print("=" * 70)
print("SIMPLE CORRELATIONS: feature vs target (Pearson r)")
print("=" * 70)
corr_matrix = df[FEATURES + TARGETS].corr()
print(corr_matrix.loc[FEATURES, TARGETS].round(3))

print("\nInterpretation guide:")
print("|r| < 0.1  : essentially no linear relationship")
print("|r| 0.1-0.3: weak")
print("|r| 0.3-0.5: moderate")
print("|r| > 0.5  : strong")