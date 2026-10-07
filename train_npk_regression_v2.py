"""
train_npk_regression_v2.py

Two improvements over train_npk_regression.py:
1. AGGREGATES multiple readings per location into a single mean value per
   location before training -- this removes the within-location noise
   from the TARGET itself (the statistically correct fix, since that
   noise can never be explained by any location-based feature anyway).
   Result: 50 location-level rows instead of 171 noisy individual rows.
2. Uses Leave-One-Out Cross-Validation (LOOCV) instead of a single
   train/test split -- appropriate given the small sample size (n=50),
   and gives a much more stable performance estimate than holding out
   just ~13 points once.
3. Uses the full 5-index feature set (NDVI, NDRE, EVI, SAVI, GNDVI) +
   Elevation, instead of just EVI+SAVI+Elevation.

Compare these R^2 values against the theoretical ceilings from
npk_variance_diagnostic.py (Nitrogen: 0.321, Phosphorus: 0.071,
Potassium: 0.307) -- getting close to those ceilings would be a genuinely
strong result given the data's inherent noise floor.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import LeaveOneOut
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

RANDOM_STATE = 42
FEATURES = ["NDVI", "NDRE", "EVI", "SAVI", "GNDVI", "Elevation"]
TARGETS = ["Nitrogen_kg_ha", "Phosphorus_kg_ha", "Potassium_kg_ha"]

# Theoretical R^2 ceilings from npk_variance_diagnostic.py
CEILINGS = {"Nitrogen_kg_ha": 0.321, "Phosphorus_kg_ha": 0.071, "Potassium_kg_ha": 0.307}

df = pd.read_csv("Sakri_NPK_with_features_v2.csv")

# --- STEP 1: Aggregate to per-location means ---
agg_df = df.groupby("Location_ID").agg({
    **{f: "first" for f in FEATURES},   # same satellite features per location
    **{t: "mean" for t in TARGETS},     # AVERAGE the noisy readings
    "Village": "first",
}).reset_index()

print(f"Aggregated {len(df)} readings down to {len(agg_df)} location-level rows.\n")

X = agg_df[FEATURES].values

MODELS = {
    "Random Forest": lambda: RandomForestRegressor(n_estimators=200, max_depth=5, random_state=RANDOM_STATE),
    "Linear Regression": lambda: LinearRegression(),
    "Ridge Regression": lambda: Ridge(alpha=1.0),
}

results = []

for target in TARGETS:
    y = agg_df[target].values
    print("=" * 70)
    print(f"TARGET: {target}  (theoretical ceiling: R^2 = {CEILINGS[target]})")
    print("=" * 70)

    for model_name, model_fn in MODELS.items():
        loo = LeaveOneOut()
        preds = np.zeros(len(y))

        for train_idx, test_idx in loo.split(X):
            model = model_fn()
            model.fit(X[train_idx], y[train_idx])
            preds[test_idx] = model.predict(X[test_idx])

        r2 = r2_score(y, preds)
        mae = mean_absolute_error(y, preds)
        rmse = np.sqrt(mean_squared_error(y, preds))

        print(f"  {model_name:<20} R^2={r2:+.3f}  MAE={mae:.2f}  RMSE={rmse:.2f}")
        results.append({"target": target, "model": model_name, "r2": round(r2, 3),
                         "mae": round(mae, 2), "rmse": round(rmse, 2)})
    print()

print("=" * 70)
print("SUMMARY")
print("=" * 70)
results_df = pd.DataFrame(results)
print(results_df.to_string(index=False))

print("\nHow to read this:")
print("- R^2 approaching the theoretical ceiling = features are extracting")
print("  close to the maximum possible signal given the data's noise floor.")
print("- R^2 well below the ceiling = there may still be real signal the")
print("  current features/model aren't capturing (worth more feature")
print("  engineering or more locations).")
print("- R^2 still near zero or negative = consistent with the earlier")
print("  correlation analysis; report as a genuine negative/inconclusive")
print("  result for this feature set at this sample size.")