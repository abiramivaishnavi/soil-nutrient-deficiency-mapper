import pandas as pd
import numpy as np
import json
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score, accuracy_score

RANDOM_STATE = 42
FEATURES = ["EVI", "SAVI", "Elevation"]

df = pd.read_csv("Sakri_Soil_Fertility_Version_2.csv")
df = df[(df["NDVI"] >= -1) & (df["NDVI"] <= 1)]
df = df[(df["EVI"] >= -1) & (df["EVI"] <= 1)]

def make_rf():
    return RandomForestClassifier(n_estimators=100, class_weight="balanced",
                                  random_state=RANDOM_STATE, n_jobs=-1)

# ---------------------------------------------------------------
# PART 1: spatial-block sensitivity (grid size x repeated hold-outs)
# ---------------------------------------------------------------
print("=" * 60)
print("PART 1: SPATIAL-BLOCK SENSITIVITY (Macro-F1)")
print("=" * 60)

N_REPEATS = 5
sens_results = []

for n_blocks in [3, 4, 5, 6]:
    d = df.copy()
    d["lat_bin"] = pd.cut(d["Latitude"], bins=n_blocks, labels=False)
    d["lon_bin"] = pd.cut(d["Longitude"], bins=n_blocks, labels=False)
    d["block_id"] = d["lat_bin"] * n_blocks + d["lon_bin"]
    blocks = d["block_id"].unique()
    n_test = max(1, int(len(blocks) * 0.25))

    scores = []
    for rep in range(N_REPEATS):
        rng = np.random.RandomState(RANDOM_STATE + rep)
        test_blocks = rng.choice(blocks, size=n_test, replace=False)
        train = d[~d["block_id"].isin(test_blocks)]
        test = d[d["block_id"].isin(test_blocks)]
        m = make_rf().fit(train[FEATURES], train["Fertility_Level"])
        pred = m.predict(test[FEATURES])
        scores.append(f1_score(test["Fertility_Level"], pred, average="macro"))

    mean, std = float(np.mean(scores)), float(np.std(scores))
    print(f"{n_blocks}x{n_blocks} grid ({len(blocks)} non-empty blocks, {n_test} held out): "
          f"Macro-F1 = {mean:.4f} +/- {std:.4f}  (min {min(scores):.4f}, max {max(scores):.4f})")
    sens_results.append({"grid": f"{n_blocks}x{n_blocks}", "blocks": int(len(blocks)),
                         "mean_f1": round(mean, 4), "std_f1": round(std, 4)})

# ---------------------------------------------------------------
# PART 2: calibration (is confidence a good guide to accuracy?)
# ---------------------------------------------------------------
print("\n" + "=" * 60)
print("PART 2: CONFIDENCE CALIBRATION")
print("=" * 60)

X, y = df[FEATURES], df["Fertility_Level"]
X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.3, stratify=y,
                                          random_state=RANDOM_STATE)
rf = make_rf().fit(X_tr, y_tr)
proba = rf.predict_proba(X_te)
conf = proba.max(axis=1)
pred = rf.classes_[proba.argmax(axis=1)]
correct = (pred == y_te.values)

edges = [0.0, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0001]
rows = []
ece = 0.0
print(f"{'Confidence bin':<16}{'n':>8}{'mean conf':>12}{'accuracy':>11}{'gap':>9}")
for lo, hi in zip(edges[:-1], edges[1:]):
    mask = (conf >= lo) & (conf < hi)
    if mask.sum() == 0:
        continue
    mc, acc = conf[mask].mean(), correct[mask].mean()
    ece += mask.mean() * abs(mc - acc)
    label = f"{lo:.1f}-{min(hi,1.0):.1f}"
    print(f"{label:<16}{mask.sum():>8}{mc:>12.3f}{acc:>11.3f}{mc-acc:>+9.3f}")
    rows.append({"bin": label, "n": int(mask.sum()),
                 "mean_confidence": round(float(mc), 3), "accuracy": round(float(acc), 3)})

print(f"\nOverall accuracy: {correct.mean():.4f}")
print(f"Mean confidence:  {conf.mean():.4f}")
print(f"Expected Calibration Error (ECE): {ece:.4f}")
print("Gap > 0 = overconfident in that bin, gap < 0 = underconfident.")

with open("dashboard/public/validation_extra.json", "w") as f:
    json.dump({"spatial_sensitivity": sens_results,
               "calibration": {"bins": rows, "ece": round(float(ece), 4),
                               "overall_accuracy": round(float(correct.mean()), 4),
                               "mean_confidence": round(float(conf.mean()), 4)}}, f, indent=2)
print("\nSaved dashboard/public/validation_extra.json")