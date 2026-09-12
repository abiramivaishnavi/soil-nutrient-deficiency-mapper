"""
hyperparameter_tuning.py

Tunes the Random Forest fertility classifier (EVI + SAVI + Elevation, the
non-leaked feature set) using RandomizedSearchCV, then re-checks the tuned
model against BOTH validation methods already used in this project:
  1. Random 70/30 stratified split (baseline: Macro-F1 = 0.8787)
  2. Spatial-block hold-out, 4x4 grid (baseline: Macro-F1 = 0.8721)

The tuned model is saved to a SEPARATE file (fertility_rf_model_tuned.pkl)
so it does NOT overwrite fertility_rf_model_clean.pkl until you've verified
it's actually better on both validation methods.

Run from the project root (same folder as Sakri_Soil_Fertility_Version_2.csv).
"""

import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split, RandomizedSearchCV, StratifiedKFold
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score, classification_report

RANDOM_STATE = 42
FEATURES = ["EVI", "SAVI", "Elevation"]

# --- Baselines already documented in the project (for comparison printout) ---
BASELINE_RANDOM_SPLIT_F1 = 0.8787
BASELINE_SPATIAL_BLOCK_F1 = 0.8721

print("=" * 70)
print("HYPERPARAMETER TUNING — Random Forest (EVI + SAVI + Elevation)")
print("=" * 70)

# --- Load + clean (identical to existing scripts) ---
df = pd.read_csv("Sakri_Soil_Fertility_Version_2.csv")
df = df[(df['NDVI'] >= -1) & (df['NDVI'] <= 1)]
df = df[(df['EVI'] >= -1) & (df['EVI'] <= 1)]

X = df[FEATURES]
y = df["Fertility_Level"]

# =============================================================================
# STEP 1: Random 70/30 split — same split used everywhere else in the project
# =============================================================================
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, stratify=y, random_state=RANDOM_STATE
)

param_dist = {
    "n_estimators": [100, 150, 200, 300],       # dropped 400/500 — marginal gains, big time cost
    "max_depth": [10, 15, 20, 25, 30],          # dropped None (unbounded) — was causing very slow fits
    "min_samples_split": [2, 5, 10],
    "min_samples_leaf": [1, 2, 4],
    "max_features": ["sqrt", "log2"],           # dropped None — sqrt/log2 already cover the useful range
}

base_model = RandomForestClassifier(class_weight="balanced", random_state=RANDOM_STATE)

cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=RANDOM_STATE)  # 5 -> 3 folds

search = RandomizedSearchCV(
    estimator=base_model,
    param_distributions=param_dist,
    n_iter=15,                  # 40 -> 15 random combos x 3-fold CV = 45 fits total (was 200)
    scoring="f1_macro",
    cv=cv,
    random_state=RANDOM_STATE,
    n_jobs=-1,
    verbose=2,                  # more visible progress so you can see it's moving
)

print("\nRunning RandomizedSearchCV on the random 70/30 split (this may take a few minutes)...")
search.fit(X_train, y_train)

print("\n--- BEST PARAMETERS FOUND ---")
for k, v in search.best_params_.items():
    print(f"  {k}: {v}")
print(f"\nBest cross-validated Macro-F1 (on training folds): {search.best_score_:.4f}")

best_model = search.best_estimator_

# Evaluate tuned model on the held-out test set
y_pred = best_model.predict(X_test)
tuned_random_split_f1 = f1_score(y_test, y_pred, average="macro")

print("\n--- TUNED MODEL ON HELD-OUT TEST SET (random split) ---")
print(f"Macro-F1: {tuned_random_split_f1:.4f}  (baseline was {BASELINE_RANDOM_SPLIT_F1:.4f})")
print(classification_report(y_test, y_pred, zero_division=0))

# =============================================================================
# STEP 2: Re-validate tuned hyperparameters on SPATIAL-BLOCK hold-out
# (This is the stricter, more honest test — same 4x4 grid setup as
#  spatial_validation.py, so results are directly comparable.)
# =============================================================================
print("\n" + "=" * 70)
print("RE-VALIDATING TUNED HYPERPARAMETERS ON SPATIAL-BLOCK HOLD-OUT")
print("=" * 70)

df_spatial = df.copy()
n_blocks = 4
df_spatial['lat_bin'] = pd.cut(df_spatial['Latitude'], bins=n_blocks, labels=False)
df_spatial['lon_bin'] = pd.cut(df_spatial['Longitude'], bins=n_blocks, labels=False)
df_spatial['block_id'] = df_spatial['lat_bin'] * n_blocks + df_spatial['lon_bin']

unique_blocks = df_spatial['block_id'].unique()
np.random.seed(RANDOM_STATE)
test_blocks = np.random.choice(unique_blocks, size=int(len(unique_blocks) * 0.25), replace=False)

train_df = df_spatial[~df_spatial['block_id'].isin(test_blocks)]
test_df = df_spatial[df_spatial['block_id'].isin(test_blocks)]

X_train_sp, y_train_sp = train_df[FEATURES], train_df['Fertility_Level']
X_test_sp, y_test_sp = test_df[FEATURES], test_df['Fertility_Level']

# Re-fit a fresh model with the SAME tuned hyperparameters on the spatial split
spatial_model = RandomForestClassifier(
    **search.best_params_, class_weight="balanced", random_state=RANDOM_STATE
)
spatial_model.fit(X_train_sp, y_train_sp)
y_pred_sp = spatial_model.predict(X_test_sp)
tuned_spatial_f1 = f1_score(y_test_sp, y_pred_sp, average="macro")

print(f"\nMacro-F1 (spatial-block): {tuned_spatial_f1:.4f}  (baseline was {BASELINE_SPATIAL_BLOCK_F1:.4f})")
print(classification_report(y_test_sp, y_pred_sp, zero_division=0))

# =============================================================================
# SUMMARY
# =============================================================================
print("\n" + "=" * 70)
print("SUMMARY: BASELINE (n_estimators=200, defaults) vs TUNED")
print("=" * 70)
print(f"{'Validation method':<25} {'Baseline Macro-F1':<20} {'Tuned Macro-F1':<20} {'Change'}")
print(f"{'Random 70/30 split':<25} {BASELINE_RANDOM_SPLIT_F1:<20.4f} {tuned_random_split_f1:<20.4f} "
      f"{tuned_random_split_f1 - BASELINE_RANDOM_SPLIT_F1:+.4f}")
print(f"{'Spatial-block hold-out':<25} {BASELINE_SPATIAL_BLOCK_F1:<20.4f} {tuned_spatial_f1:<20.4f} "
      f"{tuned_spatial_f1 - BASELINE_SPATIAL_BLOCK_F1:+.4f}")

improved_both = (tuned_random_split_f1 > BASELINE_RANDOM_SPLIT_F1) and (tuned_spatial_f1 > BASELINE_SPATIAL_BLOCK_F1)

if improved_both:
    print("\n✅ Tuned model improved on BOTH validation methods.")
    print("   Recommendation: safe to adopt as the new model, after your own review.")
else:
    print("\n⚠️  Tuned model did NOT improve on both methods.")
    print("   This can legitimately happen — n_estimators=200 with defaults may already")
    print("   be near-optimal for this feature set. Do NOT force-adopt the tuned model")
    print("   just because tuning was performed; report both results honestly either way.")

# Always save the tuned model separately — does NOT overwrite the clean baseline model
joblib.dump(best_model, "fertility_rf_model_tuned.pkl")
print("\nSaved tuned model as fertility_rf_model_tuned.pkl")
print("(fertility_rf_model_clean.pkl was NOT overwritten — decide after reviewing results above)")