"""
fetch_sakri_npk_region_imagery.py

Fetches Sentinel-2 imagery for an EXPANDED bounding box covering the full
extent of the SLUSI-verified Soil Health Card NPK sample points across
Sakri Taluka (171 observations, 50 unique coordinates, 41 villages).

This bbox is DIFFERENT from (and much larger than) the original Phase 1
bbox (74.320-74.420E, 20.870-20.970N) used for the Soil Sight V2 fertility
classification pipeline -- that pipeline and dashboard are left UNCHANGED.
This is a separate, additive Phase 2 pipeline for genuine N/P/K regression.

Bbox computed from actual NPK point extent (lat 20.795-21.228, lon 73.923-
74.423) with a small buffer added on each side.
"""

from sentinelhub import SentinelHubRequest, DataCollection, MimeType, CRS, BBox
from sentinel_config import get_config

config = get_config()

cdse_s2l2a = DataCollection.SENTINEL2_L2A.define_from(
    "cdse_s2l2a", service_url=config.sh_base_url
)

# Expanded bbox covering all 171 NPK points + small buffer
bbox = BBox(bbox=[73.91, 20.78, 74.44, 21.24], crs=CRS.WGS84)

request = SentinelHubRequest(
    data_folder="sakri_npk_region_imagery",
    evalscript="""//VERSION=3
    function setup() {
        return { input: ["B02","B03","B04","B05","B08"], output: { bands: 5, sampleType: "FLOAT32" } };
    }
    function evaluatePixel(s) {
        return [s.B02, s.B03, s.B04, s.B05, s.B08];
    }""",
    input_data=[SentinelHubRequest.input_data(
        data_collection=cdse_s2l2a,
        time_interval=("2024-08-01", "2024-09-30"),  # same date range as Phase 1 for consistency
        mosaicking_order="leastCC"
    )],
    responses=[SentinelHubRequest.output_response('default', MimeType.TIFF)],
    bbox=bbox,
    size=(1024, 1024),  # ~50m/pixel over this larger extent
    config=config
)

data = request.get_data(save_data=True)
print("Downloaded Sentinel-2 imagery for the EXPANDED Sakri Taluka NPK region.")
print("Saved to sakri_npk_region_imagery/")
print("Bbox: 73.91-74.44 E, 20.78-21.24 N (~50km x 51km)")