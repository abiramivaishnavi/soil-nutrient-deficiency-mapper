import pandas as pd

df = pd.read_csv("Sakri_Soil_Fertility_Version_2.csv")

print("Shape (rows, columns):", df.shape)
print("\nColumn names:")
print(df.columns.tolist())
print("\nFirst 5 rows:")
print(df.head())
print("\nData types:")
print(df.dtypes)
print("\nMissing values per column:")
print(df.isnull().sum())
print("\nFertility_Level class distribution:")
print(df['Fertility_Level'].value_counts())
print("\nLatitude range:", df['Latitude'].min(), "to", df['Latitude'].max())
print("Longitude range:", df['Longitude'].min(), "to", df['Longitude'].max())