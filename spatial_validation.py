import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score, classification_report

df = pd.read_csv("Sakri_Soil_Fertility_Version_2.csv")
df = df[(df['NDVI'] >= -1) & (df['NDVI'] <= 1)]
df = df[(df['EVI'] >= -1) & (df['EVI'] <= 1)]

features = ["EVI", "SAVI", "Elevation"]  # using the non-leaked set

# Divide region into a grid of spatial blocks using lat/lon bins
n_blocks = 4  # 4x4 grid = 16 blocks
df['lat_bin'] = pd.cut(df['Latitude'], bins=n_blocks, labels=False)
df['lon_bin'] = pd.cut(df['Longitude'], bins=n_blocks, labels=False)
df['block_id'] = df['lat_bin'] * n_blocks + df['lon_bin']

# Hold out ~25% of blocks entirely for testing (geographic generalization test)
unique_blocks = df['block_id'].unique()
np.random.seed(42)
test_blocks = np.random.choice(unique_blocks, size=int(len(unique_blocks) * 0.25), replace=False)

train_df = df[~df['block_id'].isin(test_blocks)]
test_df = df[df['block_id'].isin(test_blocks)]

print(f"Train rows: {len(train_df)}  |  Test rows: {len(test_df)}")
print(f"Train blocks: {len(unique_blocks) - len(test_blocks)}  |  Test blocks: {len(test_blocks)}")

X_train, y_train = train_df[features], train_df['Fertility_Level']
X_test, y_test = test_df[features], test_df['Fertility_Level']

model = RandomForestClassifier(n_estimators=200, random_state=42, class_weight="balanced")
model.fit(X_train, y_train)
y_pred = model.predict(X_test)

print("\n=== SPATIAL-BLOCK HOLD-OUT RESULTS (EVI+SAVI+Elevation) ===")
print("Macro-F1:", f1_score(y_test, y_pred, average='macro'))
print(classification_report(y_test, y_pred, zero_division=0))