"""
train_npk_regression.py

Trains Random Forest REGRESSION models (not classification) to predict
Nitrogen, Phosphorus, and Potassium (kg/ha) from EVI + SAVI + Elevation,
using the SLUSI-verified Soil Health Card ground truth for Sakri Taluka.

CRITICAL METHODOLOGICAL POINT:
Many observations share IDENTICAL coordinates (multiple soil readings at
the same village sampling point) -- e.g. Kuruswade has 7 readings all at
the exact same lat/lon. A naive random train/test split could place
readings from the SAME location in both train and test, which would leak
(the model would see nearly-identical EVI/SAVI/Elevation in training and
just needs to "remember" the answer, not generalize). To prevent this, we
split by GROUP (unique Location_ID) instead of by row -- same principle as
the spatial-block validation used in the Phase 1 fertility classifier.

We report BOTH a naive random row-split (to demonstrate the leakage risk,
same pedagogical point as the original label-leakage discovery) AND the
proper group-based split (the honest, reportable number).
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, GroupShuffleSplit
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

RANDOM_STATE = 42
FEATURES = ["EVI", "SAVI", "Elevation"]
TARGETS = ["Nitrogen_kg_ha", "Phosphorus_kg_ha", "Potassium_kg_ha"]

df = pd.read_csv("Sakri_NPK_with_features.csv")
print(f"Loaded {len(df)} observations, {df['Location_ID'].nunique()} unique locations.\n")

X = df[FEATURES]

results_summary = []

for target in TARGETS:
    y = df[target]

    print("=" * 70)
    print(f"TARGET: {target}")
    print("=" * 70)

    # -------------------------------------------------------------------
    # METHOD 1: Naive random row-split (DEMONSTRATES LEAKAGE RISK)
    # -------------------------------------------------------------------
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=RANDOM_STATE
    )
    model_naive = RandomForestRegressor(n_estimators=200, random_state=RANDOM_STATE)
    model_naive.fit(X_train, y_train)
    pred_naive = model_naive.predict(X_test)

    r2_naive = r2_score(y_test, pred_naive)
    mae_naive = mean_absolute_error(y_test, pred_naive)
    rmse_naive = np.sqrt(mean_squared_error(y_test, pred_naive))

    print(f"\n[Naive random split -- may be OPTIMISTIC due to duplicate-location leakage]")
    print(f"  R^2:  {r2_naive:.3f}")
    print(f"  MAE:  {mae_naive:.2f} kg/ha")
    print(f"  RMSE: {rmse_naive:.2f} kg/ha")

    # -------------------------------------------------------------------
    # METHOD 2: Group-based split by unique Location_ID (HONEST NUMBER)
    # -------------------------------------------------------------------
    gss = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=RANDOM_STATE)
    train_idx, test_idx = next(gss.split(X, y, groups=df["Location_ID"]))

    X_train_g, X_test_g = X.iloc[train_idx], X.iloc[test_idx]
    y_train_g, y_test_g = y.iloc[train_idx], y.iloc[test_idx]

    model_group = RandomForestRegressor(n_estimators=200, random_state=RANDOM_STATE)
    model_group.fit(X_train_g, y_train_g)
    pred_group = model_group.predict(X_test_g)

    r2_group = r2_score(y_test_g, pred_group)
    mae_group = mean_absolute_error(y_test_g, pred_group)
    rmse_group = np.sqrt(mean_squared_error(y_test_g, pred_group))

    n_train_locs = df.iloc[train_idx]["Location_ID"].nunique()
    n_test_locs = df.iloc[test_idx]["Location_ID"].nunique()

    print(f"\n[Group-based split by location -- HONEST, REPORTABLE result]")
    print(f"  Train locations: {n_train_locs}  |  Test locations: {n_test_locs}")
    print(f"  R^2:  {r2_group:.3f}")
    print(f"  MAE:  {mae_group:.2f} kg/ha")
    print(f"  RMSE: {rmse_group:.2f} kg/ha")

    results_summary.append({
        "target": target,
        "r2_naive": round(r2_naive, 3), "r2_group": round(r2_group, 3),
        "mae_naive": round(mae_naive, 2), "mae_group": round(mae_group, 2),
        "rmse_naive": round(rmse_naive, 2), "rmse_group": round(rmse_group, 2),
    })

    # Save the group-validated model (the one to actually use/report)
    import joblib
    joblib.dump(model_group, f"npk_{target.split('_')[0].lower()}_model.pkl")

print("\n" + "=" * 70)
print("SUMMARY -- NAIVE (RISK OF LEAKAGE) vs GROUP-BASED (HONEST)")
print("=" * 70)
print(f"{'Target':<20} {'R2 (naive)':<12} {'R2 (group)':<12} {'MAE (group)':<14} {'RMSE (group)'}")
for r in results_summary:
    print(f"{r['target']:<20} {r['r2_naive']:<12} {r['r2_group']:<12} "
          f"{r['mae_group']:<14} {r['rmse_group']}")

print("\nIMPORTANT CAVEATS FOR THE PAPER:")
print("- Only 50 unique sample locations underpin this analysis -- R^2 estimates")
print("  from such a small test set (roughly 12-13 locations held out) carry")
print("  substantial uncertainty. Report as an initial/preliminary regression")
print("  result, not a final, fully validated production model.")
print("- Report the GROUP-based numbers as the honest result. If naive and group")
print("  numbers differ substantially, that gap itself is worth reporting --")
print("  it quantifies how much of the naive score was leakage, same lesson as")
print("  the Phase 1 label-leakage discovery.")