import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import f1_score, classification_report

RANDOM_STATE = 42
FEATURES = ["EVI", "SAVI", "Elevation"]

df = pd.read_csv("Sakri_Soil_Fertility_Version_2.csv")
df = df[(df['NDVI'] >= -1) & (df['NDVI'] <= 1)]
df = df[(df['EVI'] >= -1) & (df['EVI'] <= 1)]

X = df[FEATURES]
y = df["Fertility_Level"]

print("=" * 70)
print("GRADIENT BOOSTING — RANDOM 70/30 SPLIT")
print("=" * 70)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, stratify=y, random_state=RANDOM_STATE
)

class_counts = y_train.value_counts()
sample_weights = y_train.map(lambda c: len(y_train) / (len(class_counts) * class_counts[c]))

gb_model = GradientBoostingClassifier(
    n_estimators=200, max_depth=3, learning_rate=0.1, random_state=RANDOM_STATE
)
gb_model.fit(X_train, y_train, sample_weight=sample_weights)

y_pred = gb_model.predict(X_test)
random_split_f1 = f1_score(y_test, y_pred, average="macro")

print(f"\nMacro-F1 (random split): {random_split_f1:.4f}")
print(classification_report(y_test, y_pred, zero_division=0))

print("\n" + "=" * 70)
print("GRADIENT BOOSTING — SPATIAL-BLOCK HOLD-OUT")
print("=" * 70)

n_blocks = 4
df['lat_bin'] = pd.cut(df['Latitude'], bins=n_blocks, labels=False)
df['lon_bin'] = pd.cut(df['Longitude'], bins=n_blocks, labels=False)
df['block_id'] = df['lat_bin'] * n_blocks + df['lon_bin']

unique_blocks = df['block_id'].unique()
np.random.seed(RANDOM_STATE)
test_blocks = np.random.choice(unique_blocks, size=int(len(unique_blocks) * 0.25), replace=False)

train_df = df[~df['block_id'].isin(test_blocks)]
test_df = df[df['block_id'].isin(test_blocks)]

X_train_sp, y_train_sp = train_df[FEATURES], train_df['Fertility_Level']
X_test_sp, y_test_sp = test_df[FEATURES], test_df['Fertility_Level']

class_counts_sp = y_train_sp.value_counts()
sample_weights_sp = y_train_sp.map(lambda c: len(y_train_sp) / (len(class_counts_sp) * class_counts_sp[c]))

gb_model_sp = GradientBoostingClassifier(
    n_estimators=200, max_depth=3, learning_rate=0.1, random_state=RANDOM_STATE
)
gb_model_sp.fit(X_train_sp, y_train_sp, sample_weight=sample_weights_sp)

y_pred_sp = gb_model_sp.predict(X_test_sp)
spatial_f1 = f1_score(y_test_sp, y_pred_sp, average="macro")

print(f"\nMacro-F1 (spatial-block): {spatial_f1:.4f}")
print(classification_report(y_test_sp, y_pred_sp, zero_division=0))

print("\n" + "=" * 70)
print("CONSOLIDATED MODEL COMPARISON (Macro-F1)")
print("=" * 70)
print(f"{'Model':<25} {'Random Split':<15} {'Spatial-Block':<15}")
print(f"{'Random Forest (final)':<25} {0.8787:<15.4f} {0.8721:<15.4f}")
print(f"{'Gradient Boosting':<25} {random_split_f1:<15.4f} {spatial_f1:<15.4f}")
print(f"{'Logistic Regression':<25} {0.7099:<15.4f} {'—':<15}")
print(f"{'K-Means (unsupervised)':<25} {0.2125:<15.4f} {'—':<15}")