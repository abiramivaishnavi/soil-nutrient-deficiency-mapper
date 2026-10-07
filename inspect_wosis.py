import pandas as pd
from pathlib import Path

# WoSIS dataset folder
DATA_DIR = Path(r"E:\Soil Nutrient Deficiency Mapper\WoSIS_2023_December")

print("Checking WoSIS folder...")
print(DATA_DIR)

# --------------------------------------------------
# 1. Read profiles
# --------------------------------------------------

profiles_file = DATA_DIR / "wosis_202312_profiles.tsv"

profiles = pd.read_csv(
    profiles_file,
    sep="\t",
    low_memory=False
)

print("\nPROFILE COLUMNS:")
print(profiles.columns.tolist())

print("\nNumber of profiles:", len(profiles))

# --------------------------------------------------
# 2. Check India
# --------------------------------------------------

if "country_name" in profiles.columns:

    india = profiles[
        profiles["country_name"]
        .astype(str)
        .str.strip()
        .str.lower()
        == "india"
    ]

    print("\nIndia profiles:", len(india))

else:
    print("\nCould not find country_name column.")

# --------------------------------------------------
# 3. Check coordinates
# --------------------------------------------------

print("\nCOORDINATE COLUMNS:")

for col in profiles.columns:
    if "lat" in col.lower() or "lon" in col.lower():
        print(col)

# --------------------------------------------------
# 4. List all soil-property files
# --------------------------------------------------

print("\nSOIL PROPERTY FILES:")

for file in sorted(DATA_DIR.glob("wosis_202312_*.tsv")):

    print(file.name)

print("\nDone.")