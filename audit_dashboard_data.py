"""Read-only audit: lists what each dashboard JSON actually contains and
prints side-by-side any value that exists in more than one file.
Run from the project root:  python audit_dashboard_data.py
Changes nothing."""
import json, os

PUB = os.path.join("dashboard", "public")
FILES = ["stats.json", "temporal_summary.json", "model_evaluation.json",
         "validation_extra.json", "npk_points.json", "shc_status.json", "shc_validation.json"]

data = {}
for f in FILES:
    p = os.path.join(PUB, f)
    if not os.path.exists(p):
        print(f"[MISSING] {p}")
        continue
    data[f] = json.load(open(p, encoding="utf-8"))

def shape(x, depth=0):
    if isinstance(x, dict):
        return "{" + ", ".join(f"{k}: {shape(v, depth+1) if depth < 1 else type(v).__name__}" for k, v in x.items()) + "}"
    if isinstance(x, list):
        return f"list[{len(x)}]" + (" of " + shape(x[0], depth+1) if x and depth < 1 else "")
    return type(x).__name__

print("=" * 70, "\nKEYS PER FILE\n" + "=" * 70)
for f, d in data.items():
    print(f"\n{f}\n  {shape(d)}")

print("\n" + "=" * 70, "\nCROSS-FILE DUPLICATES (compare values)\n" + "=" * 70)
def g(f, *path):
    x = data.get(f)
    for k in path:
        try:
            x = x[k]
        except Exception:
            return "n/a"
    return x

print("\n1. Fertility class % (Date 1)")
print("   stats.json class_percent        :", g("stats.json", "class_percent"))
fz = g("temporal_summary.json", "fertility_zone_shift")
print("   temporal_summary date1_pct      :", {r["class"]: r["date1_pct"] for r in fz} if fz != "n/a" else fz)

print("\n2. Spatial-block Macro-F1 (Random Forest)")
mc = g("model_evaluation.json", "model_comparison")
if mc != "n/a":
    for m in mc:
        print("   model_evaluation", m["model"], ":", m.get("random_split_f1"), "/", m.get("spatial_block_f1"))
ss = g("validation_extra.json", "spatial_sensitivity")
if ss != "n/a":
    for r in ss:
        print("   validation_extra", r["grid"], ":", r["mean_f1"], "+/-", r["std_f1"])

print("\n3. Confidence")
print("   stats.json mean_confidence (map pixels)   :", g("stats.json", "mean_confidence"))
print("   validation_extra mean_confidence (test)   :", g("validation_extra.json", "calibration", "mean_confidence"))
print("   validation_extra overall_accuracy (test)  :", g("validation_extra.json", "calibration", "overall_accuracy"))

print("\n4. NPK / SHC counts")
print("   npk_points   total_locations/readings :", g("npk_points.json", "total_locations"), "/", g("npk_points.json", "total_readings"))
print("   shc_status   locations/readings       :", g("shc_status.json", "locations"), "/", g("shc_status.json", "readings"))
print("   len(npk_points.points) / len(shc_status.points):",
      len(g("npk_points.json", "points")) if g("npk_points.json", "points") != "n/a" else "n/a", "/",
      len(g("shc_status.json", "points")) if g("shc_status.json", "points") != "n/a" else "n/a")

print("\n5. Mean N/P/K")
print("   shc_status summary means:", {n: g("shc_status.json", "summary", n, "mean") for n in "NPK"})
pts = g("npk_points.json", "points")
if pts != "n/a" and pts:
    import statistics as st
    print("   npk_points mean of points:",
          {k: round(st.mean(p[k] for p in pts), 1) for k in ("nitrogen", "phosphorus", "potassium")},
          "(mean of location means, not readings)")