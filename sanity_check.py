import pandas as pd

df = pd.read_csv("Sakri_Soil_Fertility_Version_2.csv")

print("=== 1. CLASS COUNTS ===")
print(df['Fertility_Level'].value_counts())
print("\nClass proportions (%):")
print((df['Fertility_Level'].value_counts(normalize=True) * 100).round(2))

print("\n=== 2. DUPLICATE COORDINATES ===")
dupe_coords = df.duplicated(subset=['Latitude', 'Longitude']).sum()
print(f"Duplicate (Lat, Lon) rows: {dupe_coords}")

print("\n=== 3. FEATURE RANGES ===")
features = ["NDVI", "EVI", "SAVI", "Soil_Moisture", "Elevation"]
print(df[features].describe())

print("\n=== 4. POSSIBLE TARGET LEAKAGE CHECK ===")
# Check if any single feature perfectly separates classes (a sign of leakage)
for feat in features:
    grouped = df.groupby('Fertility_Level')[feat].agg(['min', 'max', 'mean'])
    print(f"\n--- {feat} by class ---")
    print(grouped)