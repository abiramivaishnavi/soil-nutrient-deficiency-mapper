import rasterio
import numpy as np
import matplotlib.pyplot as plt
from pyproj import Transformer
import os

TARGET_SHAPE = (1024, 1024)
TARGET_BOUNDS = (74.320, 20.870, 74.420, 20.970)  # west, south, east, north

fwd = Transformer.from_crs(
    "EPSG:4326",
    "+proj=igh +lat_0=0 +lon_0=0 +datum=WGS84 +units=m +no_defs",
    always_xy=True
)


def manual_remap(src_path, scale_factor):
    src = rasterio.open(src_path)
    data = src.read(1)

    lons = np.linspace(
        TARGET_BOUNDS[0],
        TARGET_BOUNDS[2],
        TARGET_SHAPE[1]
    )

    lats = np.linspace(
        TARGET_BOUNDS[3],
        TARGET_BOUNDS[1],
        TARGET_SHAPE[0]
    )

    lon_grid, lat_grid = np.meshgrid(lons, lats)

    x_flat, y_flat = fwd.transform(
        lon_grid.flatten(),
        lat_grid.flatten()
    )

    cols, rows = ~src.transform * (
        np.array(x_flat),
        np.array(y_flat)
    )

    cols = np.round(cols).astype(int)
    rows = np.round(rows).astype(int)

    valid = (
        (rows >= 0) &
        (rows < data.shape[0]) &
        (cols >= 0) &
        (cols < data.shape[1])
    )

    output = np.full(
        TARGET_SHAPE,
        np.nan,
        dtype=np.float32
    ).flatten()

    output[valid] = data[
        rows[valid],
        cols[valid]
    ]

    output = output.reshape(TARGET_SHAPE) * scale_factor

    print(
        f"{src_path}: valid pixels = "
        f"{valid.sum()} / {len(valid)}"
    )

    return output


def save_overlay(data, output_path, title):
    """
    Convert numerical raster into a proper RGBA PNG.
    Valid pixels receive colors.
    NaN pixels become transparent.
    """

    valid = np.isfinite(data)

    if not np.any(valid):
        print(f"ERROR: No valid pixels found for {title}")
        return

    vmin = np.nanmin(data)
    vmax = np.nanmax(data)

    print(f"{title}:")
    print(f"  Min = {vmin:.3f}")
    print(f"  Max = {vmax:.3f}")
    print(f"  Valid pixels = {valid.sum()}")

    # Normalize values between 0 and 1
    normalized = np.zeros_like(data, dtype=np.float32)

    if vmax > vmin:
        normalized[valid] = (
            (data[valid] - vmin) /
            (vmax - vmin)
        )
    else:
        normalized[valid] = 0.5

    # Apply green-yellow-red colour map
    cmap = plt.get_cmap("RdYlGn")

    rgba = cmap(normalized)

    # Make missing pixels transparent
    rgba[..., 3] = 0
    rgba[valid, 3] = 1

    # Convert to 8-bit RGBA PNG
    rgba_uint8 = (rgba * 255).astype(np.uint8)

    plt.imsave(
        output_path,
        rgba_uint8,
        format="png"
    )

    print(f"Saved: {output_path}")


# ---------------------------------------------------------
# STEP 1: Generate SoilGrids numerical layers
# ---------------------------------------------------------

nitrogen_gkg = manual_remap(
    "sakri_soilgrids_nitrogen.tif",
    scale_factor=1 / 100.0
)

cec_mmolkg = manual_remap(
    "sakri_soilgrids_cec.tif",
    scale_factor=1 / 10.0
)


# ---------------------------------------------------------
# STEP 2: Remove invalid zero values
# ---------------------------------------------------------

nitrogen_gkg[nitrogen_gkg == 0] = np.nan
cec_mmolkg[cec_mmolkg == 0] = np.nan


# ---------------------------------------------------------
# STEP 3: Create dashboard folder
# ---------------------------------------------------------

os.makedirs(
    "dashboard/public",
    exist_ok=True
)


# ---------------------------------------------------------
# STEP 4: Generate proper transparent overlays
# ---------------------------------------------------------

save_overlay(
    nitrogen_gkg,
    "dashboard/public/nitrogen_overlay.png",
    "Nitrogen (g/kg)"
)

save_overlay(
    cec_mmolkg,
    "dashboard/public/cec_overlay.png",
    "CEC (mmol(c)/kg)"
)


# ---------------------------------------------------------
# STEP 5: Save numerical arrays
# ---------------------------------------------------------

os.makedirs(
    "sakri_predictions",
    exist_ok=True
)

np.save(
    "sakri_predictions/nitrogen_gkg.npy",
    nitrogen_gkg
)

np.save(
    "sakri_predictions/cec_mmolkg.npy",
    cec_mmolkg
)


# ---------------------------------------------------------
# STEP 6: Print statistics
# ---------------------------------------------------------

print("\nFINAL STATISTICS")

print(
    f"Nitrogen (g/kg): "
    f"mean={np.nanmean(nitrogen_gkg):.2f}, "
    f"range={np.nanmin(nitrogen_gkg):.2f}-"
    f"{np.nanmax(nitrogen_gkg):.2f}"
)

print(
    f"CEC (mmol(c)/kg): "
    f"mean={np.nanmean(cec_mmolkg):.2f}, "
    f"range={np.nanmin(cec_mmolkg):.2f}-"
    f"{np.nanmax(cec_mmolkg):.2f}"
)