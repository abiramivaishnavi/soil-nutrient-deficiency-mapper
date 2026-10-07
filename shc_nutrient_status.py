import pandas as pd
import numpy as np
import json

LIMITS = {  # kg/ha: (low_below, high_above)  -- ICAR / national SHC ratings
    "Nitrogen_kg_ha":   (280, 560),
    "Phosphorus_kg_ha": (10, 25),
    "Potassium_kg_ha":  (120, 280),
}
SHORT = {"Nitrogen_kg_ha": "N", "Phosphorus_kg_ha": "P", "Potassium_kg_ha": "K"}

def rate(v, lo, hi):
    return "Low" if v < lo else ("High" if v > hi else "Medium")

df = pd.read_csv("Sakri_NPK_with_features_v2.csv")
loc = df.groupby("Location_ID").agg(
    Village=("Village", "first"), Latitude=("Latitude", "first"),
    Longitude=("Longitude", "first"),
    **{c: (c, "mean") for c in LIMITS}).reset_index()

out = {"limits_kg_ha": {SHORT[k]: {"low_below": v[0], "high_above": v[1]}
                        for k, v in LIMITS.items()},
       "source": "ICAR-IISS Harit Dhara 4(1), 2021 (Soil Health Card critical limits)",
       "readings": len(df), "locations": len(loc), "summary": {}, "points": []}

print(f"{'':<4}{'level':<8}{'readings %':>12}{'locations %':>13}   range (mean) kg/ha")
for col, (lo, hi) in LIMITS.items():
    t = SHORT[col]
    r_cls = df[col].apply(lambda v: rate(v, lo, hi))
    l_cls = loc[col].apply(lambda v: rate(v, lo, hi))
    out["summary"][t] = {
        "readings_pct": {c: round(float((r_cls == c).mean() * 100), 1) for c in ["Low", "Medium", "High"]},
        "locations_pct": {c: round(float((l_cls == c).mean() * 100), 1) for c in ["Low", "Medium", "High"]},
        "min": round(float(df[col].min()), 1), "max": round(float(df[col].max()), 1),
        "mean": round(float(df[col].mean()), 1)}
    for c in ["Low", "Medium", "High"]:
        print(f"{t:<4}{c:<8}{(r_cls == c).mean()*100:>11.1f}%{(l_cls == c).mean()*100:>12.1f}%"
              + (f"   {df[col].min():.0f}-{df[col].max():.0f} ({df[col].mean():.0f})" if c == "Low" else ""))
    loc[t + "_status"] = l_cls

# readings that straddle a class boundary within one location
print("\nLocations whose individual readings disagree on class (sample-level mix):")
for col, (lo, hi) in LIMITS.items():
    mixed = df.groupby("Location_ID")[col].apply(
        lambda s: s.apply(lambda v: rate(v, lo, hi)).nunique() > 1).sum()
    print(f"  {SHORT[col]}: {mixed} of {len(loc)} locations")

for _, r in loc.iterrows():
    out["points"].append({"village": r["Village"], "lat": round(r["Latitude"], 6),
        "lon": round(r["Longitude"], 6),
        **{SHORT[c]: round(float(r[c]), 1) for c in LIMITS},
        **{SHORT[c] + "_status": r[SHORT[c] + "_status"] for c in LIMITS}})

with open("dashboard/public/shc_status.json", "w") as f:
    json.dump(out, f, indent=2)
print("\nSaved dashboard/public/shc_status.json")