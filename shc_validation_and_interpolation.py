import pandas as pd
import numpy as np
import joblib
import json
from scipy.stats import spearmanr, kruskal, rankdata

FEATS = ["EVI", "SAVI", "Elevation"]
CLASS_ORDER = {"Low": 0, "Moderate": 1, "High": 2, "Very High": 3}

# ---------- load SHC locations (one row per unique location) ----------
df = pd.read_csv("Sakri_NPK_with_features_v2.csv")
loc = df.groupby("Location_ID").agg(
    Village=("Village", "first"),
    Latitude=("Latitude", "first"), Longitude=("Longitude", "first"),
    EVI=("EVI", "first"), SAVI=("SAVI", "first"), Elevation=("Elevation", "first"),
    N=("Nitrogen_kg_ha", "mean"), P=("Phosphorus_kg_ha", "mean"),
    K=("Potassium_kg_ha", "mean"),
).reset_index()
print(f"{len(loc)} unique SHC locations\n")

model = joblib.load("fertility_rf_model_clean.pkl")
train = pd.read_csv("Sakri_Soil_Fertility_Version_2.csv")
train = train[(train["NDVI"] >= -1) & (train["NDVI"] <= 1)]
train = train[(train["EVI"] >= -1) & (train["EVI"] <= 1)]

results = {"fertility_vs_shc": {}, "interpolation": {}}

# ---------- PART A: predicted fertility class vs measured N/P/K ----------
print("=" * 64)
print("PART A: PREDICTED FERTILITY CLASS vs MEASURED SHC N/P/K")
print("=" * 64)

def quantile_map(values, ref):
    q = rankdata(values) / (len(values) + 1)
    return np.quantile(ref, q)

variants = {"no_correction": loc[FEATS].copy()}
qm = loc[FEATS].copy()
for f in ["EVI", "SAVI", "Elevation"]:
    qm[f] = quantile_map(loc[f].values, train[f].values)
variants["quantile_mapped"] = qm

for name, X in variants.items():
    pred = model.predict(X[FEATS])
    ordinal = pd.Series(pred).map(CLASS_ORDER).values
    counts = pd.Series(pred).value_counts().to_dict()
    print(f"\n[{name}] predicted class counts: {counts}")
    results["fertility_vs_shc"][name] = {"class_counts": counts}
    for t in ["N", "P", "K"]:
        if len(set(ordinal)) < 2:
            print(f"  {t}: all points got the same class, cannot test")
            continue
        rho, p = spearmanr(ordinal, loc[t])
        groups = [loc[t].values[ordinal == c] for c in sorted(set(ordinal))
                  if (ordinal == c).sum() >= 2]
        try:
            kw_p = kruskal(*groups).pvalue if len(groups) >= 2 else float("nan")
        except ValueError:
            kw_p = float("nan")
        print(f"  {t}: Spearman rho = {rho:+.3f} (p={p:.3f}),  Kruskal-Wallis p = {kw_p:.3f}")
        results["fertility_vs_shc"][name][t] = {
            "spearman_rho": round(float(rho), 3), "p": round(float(p), 3),
            "kruskal_p": None if np.isnan(kw_p) else round(float(kw_p), 3)}

# ---------- PART B: is N/P/K spatially structured? ----------
print("\n" + "=" * 64)
print("PART B: SPATIAL AUTOCORRELATION AND INTERPOLATION (LOOCV)")
print("=" * 64)

lat0, lon0 = loc["Latitude"].mean(), loc["Longitude"].mean()
x = (loc["Longitude"].values - lon0) * 111.32 * np.cos(np.radians(lat0))
y = (loc["Latitude"].values - lat0) * 110.57
D = np.sqrt((x[:, None] - x[None, :]) ** 2 + (y[:, None] - y[None, :]) ** 2)
n = len(loc)
np.fill_diagonal(D, np.inf)

def r2(obs, pred):
    return 1 - np.sum((obs - pred) ** 2) / np.sum((obs - obs.mean()) ** 2)

def morans_i(z, W):
    z = z - z.mean()
    return (len(z) / W.sum()) * (z @ W @ z) / (z @ z)

W = 1.0 / np.where(np.isinf(D), np.inf, np.maximum(D, 0.05))
np.fill_diagonal(W, 0.0)
rng = np.random.RandomState(42)

print(f"{'Target':<8}{'Moran I':>9}{'perm p':>9}{'IDW R2':>9}{'1-NN R2':>9}{'mean R2':>9}")
for t in ["N", "P", "K"]:
    v = loc[t].values
    I = morans_i(v, W)
    perm = [morans_i(rng.permutation(v), W) for _ in range(999)]
    p = (1 + np.sum(np.array(perm) >= I)) / 1000

    idw, nn, mean_b = np.zeros(n), np.zeros(n), np.zeros(n)
    for i in range(n):
        d = np.maximum(D[i], 0.05)
        w = 1.0 / d ** 2
        w[i] = 0.0
        idw[i] = np.sum(w * v) / w.sum()
        nn[i] = v[np.argmin(D[i])]
        mean_b[i] = np.delete(v, i).mean()

    print(f"{t:<8}{I:>+9.3f}{p:>9.3f}{r2(v, idw):>+9.3f}{r2(v, nn):>+9.3f}{r2(v, mean_b):>+9.3f}")
    results["interpolation"][t] = {
        "morans_I": round(float(I), 3), "perm_p": round(float(p), 3),
        "idw_r2": round(float(r2(v, idw)), 3),
        "nn_r2": round(float(r2(v, nn)), 3),
        "mean_baseline_r2": round(float(r2(v, mean_b)), 3)}

print("\nMedian distance to nearest other SHC location: "
      f"{np.median(D.min(axis=1)):.1f} km")
print("Moran I > 0 with small p = neighbouring locations are similar.")
print("IDW R2 clearly above the mean baseline = interpolation adds real skill.")

with open("dashboard/public/shc_validation.json", "w") as f:
    json.dump(results, f, indent=2)
print("\nSaved dashboard/public/shc_validation.json")