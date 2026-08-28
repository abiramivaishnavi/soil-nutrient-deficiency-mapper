import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import f1_score, classification_report
from scipy.stats import mode
import numpy as np

df = pd.read_csv("Sakri_Soil_Fertility_Version_2.csv")
df = df[(df['NDVI'] >= -1) & (df['NDVI'] <= 1)]
df = df[(df['EVI'] >= -1) & (df['EVI'] <= 1)]

features = ["EVI", "SAVI", "Elevation"]  # same non-leaked set, for fair comparison
X = df[features]
y_true = df["Fertility_Level"]

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
cluster_labels = kmeans.fit_predict(X_scaled)

# Map each cluster to its most common true class (standard way to "score" unsupervised clustering)
label_map = {}
for cluster in np.unique(cluster_labels):
    mask = cluster_labels == cluster
    most_common = pd.Series(y_true[mask]).value_counts().idxmax()
    label_map[cluster] = most_common

y_pred_mapped = pd.Series(cluster_labels).map(label_map)

print("=== K-MEANS BASELINE (EVI+SAVI+Elevation) ===")
print("Macro-F1:", f1_score(y_true, y_pred_mapped, average='macro'))
print(classification_report(y_true, y_pred_mapped, zero_division=0))