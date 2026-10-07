import pandas as pd
import json

df = pd.read_csv("Sakri_NPK_with_features_v2.csv")

agg = df.groupby("Location_ID").agg({
    "Village": "first",
    "Latitude": "first",
    "Longitude": "first",
    "Nitrogen_kg_ha": "mean",
    "Phosphorus_kg_ha": "mean",
    "Potassium_kg_ha": "mean",
}).reset_index()

reading_counts = df.groupby("Location_ID").size().rename("num_readings")
agg = agg.merge(reading_counts, on="Location_ID")

points = []
for _, row in agg.iterrows():
    points.append({
        "village": row["Village"],
        "lat": round(row["Latitude"], 6),
        "lon": round(row["Longitude"], 6),
        "nitrogen": round(row["Nitrogen_kg_ha"], 1),
        "phosphorus": round(row["Phosphorus_kg_ha"], 1),
        "potassium": round(row["Potassium_kg_ha"], 1),
        "num_readings": int(row["num_readings"]),
    })

output = {
    "points": points,
    "total_locations": len(points),
    "total_readings": len(df),
    "source": "Soil Health Card portal, cross-verified against SLUSI Sakri Taluka boundary maps",
    "bounds": [
        [df["Latitude"].min(), df["Longitude"].min()],
        [df["Latitude"].max(), df["Longitude"].max()]
    ]
}

with open("dashboard/public/npk_points.json", "w") as f:
    json.dump(output, f, indent=2)

print(f"Exported {len(points)} NPK sample locations ({len(df)} total readings) "
      f"to dashboard/public/npk_points.json")