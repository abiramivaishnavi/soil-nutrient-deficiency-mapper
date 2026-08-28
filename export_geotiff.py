import numpy as np
import rasterio
import pickle
import os

# Load the profile (georeferencing info) saved earlier
with open("sakri_indices/raster_profile.pkl", "rb") as f:
    profile = pickle.load(f)

fertility_map = np.load("sakri_predictions/fertility_map_real.npy", allow_pickle=True)
confidence_map = np.load("sakri_predictions/confidence_map_real.npy")

# Convert class labels to numeric codes for GeoTIFF (rasters need numbers, not text)
class_codes = {"Low": 1, "Moderate": 2, "High": 3, "Very High": 4}
numeric_fertility = np.vectorize(class_codes.get)(fertility_map).astype(np.uint8)

# Update profile for single-band, byte-type output
out_profile = profile.copy()
out_profile.update(dtype=rasterio.uint8, count=1, nodata=0)

with rasterio.open("sakri_predictions/fertility_map.tif", "w", **out_profile) as dst:
    dst.write(numeric_fertility, 1)
    dst.write_colormap(1, {
        1: (178, 58, 46, 255),   # Low - red
        2: (217, 142, 43, 255),  # Moderate - amber
        3: (110, 159, 94, 255),  # High - green
        4: (31, 74, 44, 255),    # Very High - dark green
    })

# Confidence as a float GeoTIFF
conf_profile = profile.copy()
conf_profile.update(dtype=rasterio.float32, count=1)
with rasterio.open("sakri_predictions/confidence_map.tif", "w", **conf_profile) as dst:
    dst.write(confidence_map.astype(np.float32), 1)

print("Exported fertility_map.tif and confidence_map.tif to sakri_predictions/")
print("These are standard GeoTIFFs — openable in QGIS/ArcGIS with correct coordinates.")