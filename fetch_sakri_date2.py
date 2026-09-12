"""
fetch_sakri_date2.py

Fetches a SECOND Sentinel-2 date for Sakri, at a different phenological stage
than the existing imagery (Aug-Sep 2024 = mid-monsoon/peak vegetative for cotton).

This fetch targets Dec 2024 - Jan 2025 = post-harvest/dry season, so the
comparison between date1 and date2 should show a real, explainable shift in
vegetation indices (harvested/bare fields = lower NDVI/EVI/SAVI), not just noise.

Same bbox, same 1024x1024 grid, same 5 bands as the original fetch --
so outputs are pixel-aligned with the existing date1 data automatically.
"""

from sentinelhub import SentinelHubRequest, DataCollection, MimeType, CRS, BBox
from sentinel_config import get_config

config = get_config()

cdse_s2l2a = DataCollection.SENTINEL2_L2A.define_from(
    "cdse_s2l2a", service_url=config.sh_base_url
)

# SAME bbox as date1 -- critical for pixel alignment when comparing later
bbox = BBox(bbox=[74.320, 20.870, 74.420, 20.970], crs=CRS.WGS84)

request = SentinelHubRequest(
    data_folder="sakri_imagery_date2",
    evalscript="""//VERSION=3
    function setup() {
        return { input: ["B02","B03","B04","B05","B08"], output: { bands: 5, sampleType: "FLOAT32" } };
    }
    function evaluatePixel(s) {
        return [s.B02, s.B03, s.B04, s.B05, s.B08];
    }""",
    input_data=[SentinelHubRequest.input_data(
        data_collection=cdse_s2l2a,
        time_interval=("2024-12-01", "2025-01-31"),   # post-harvest / dry season
        mosaicking_order="leastCC"
    )],
    responses=[SentinelHubRequest.output_response('default', MimeType.TIFF)],
    bbox=bbox,
    size=(1024, 1024),   # SAME size as date1 -- pixel alignment
    config=config
)

data = request.get_data(save_data=True)
print("Downloaded Sentinel-2 imagery for Sakri — DATE 2 (Dec 2024-Jan 2025, post-harvest).")
print("Saved to sakri_imagery_date2/")