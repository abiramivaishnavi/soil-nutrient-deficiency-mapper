import pandas as pd
from pathlib import Path
import re

DATA_DIR = Path(r"E:\Soil Nutrient Deficiency Mapper\WoSIS_2023_December")

profiles = pd.read_csv(DATA_DIR / "wosis_202312_profiles.tsv", sep="\t", low_memory=False)
nitrogen = pd.read_csv(DATA_DIR / "wosis_202312_nitkjd.tsv", sep="\t", low_memory=False)

india_profiles = profiles[profiles["country_name"].astype(str).str.strip().str.lower() == "india"]
merged = india_profiles.merge(nitrogen, on="profile_id", how="inner", suffixes=("_profile", "_nitrogen"))

# Clean the value column: "{1.40}" -> 1.40
merged['N_value'] = merged['value'].astype(str).str.extract(r'([\d.]+)').astype(float)

# Keep only topsoil layer (smallest upper_depth) per profile
merged_sorted = merged.sort_values('upper_depth')
topsoil = merged_sorted.drop_duplicates(subset='profile_id', keep='first')

clean = topsoil[['profile_id', 'latitude_profile', 'longitude_profile', 'upper_depth', 'lower_depth', 'N_value']].copy()
clean.columns = ['profile_id', 'latitude', 'longitude', 'upper_depth_cm', 'lower_depth_cm', 'nitrogen_g_per_kg']

clean = clean.dropna(subset=['nitrogen_g_per_kg', 'latitude', 'longitude'])
clean = clean[(clean['latitude'] != 0) & (clean['longitude'] != 0)]  # remove bad coordinates

print(f"Clean, unique India topsoil nitrogen points: {len(clean)}")
print(clean.describe())
print("\nSample:")
print(clean.head(10))

clean.to_csv("wosis_india_nitrogen_clean.csv", index=False)
print("\nSaved wosis_india_nitrogen_clean.csv")