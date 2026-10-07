import pandas as pd
from pathlib import Path

DATA_DIR = Path(r"E:\Soil Nutrient Deficiency Mapper\WoSIS_2023_December")

profiles = pd.read_csv(DATA_DIR / "wosis_202312_profiles.tsv", sep="\t", low_memory=False)
nitrogen = pd.read_csv(DATA_DIR / "wosis_202312_nitkjd.tsv", sep="\t", low_memory=False)

india_profiles = profiles[profiles["country_name"].astype(str).str.strip().str.lower() == "india"]
print(f"India profiles: {len(india_profiles)}")

merged = india_profiles.merge(nitrogen, on="profile_id", how="inner", suffixes=("_profile", "_nitrogen"))
print(f"India profiles WITH nitrogen data: {len(merged)}")

print("\nColumns after merge:", merged.columns.tolist())

print("\nSample of merged data:")
print(merged[["profile_id", "latitude_profile", "longitude_profile", "value"]].head(10))

# Check how many fall roughly within/near Maharashtra
maha_bbox = merged[
    (merged["latitude_profile"] >= 15.5) & (merged["latitude_profile"] <= 22.0) &
    (merged["longitude_profile"] >= 72.5) & (merged["longitude_profile"] <= 80.5)
]
print(f"\nIndia nitrogen profiles roughly within/near Maharashtra: {len(maha_bbox)}")