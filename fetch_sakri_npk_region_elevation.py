"""
fetch_sakri_npk_region_elevation.py

Fetches Copernicus 30m DEM for the SAME expanded bbox as
fetch_sakri_npk_region_imagery.py, for pixel alignment.
"""

from sentinelhub import SentinelHubRequest, DataCollection, MimeType, CRS, BBox
from sentinel_config import get_config

config = get_config()

cdse_dem = DataCollection.DEM_COPERNICUS_30.define_from(
    "cdse_dem", service_url=config.sh_base_url
)

# SAME bbox as fetch_sakri_npk_region_imagery.py
bbox = BBox(bbox=[73.91, 20.78, 74.44, 21.24], crs=CRS.WGS84)

request = SentinelHubRequest(
    data_folder="sakri_npk_region_elevation",
    evalscript="""//VERSION=3
    function setup() {
        return { input: ["DEM"], output: { bands: 1, sampleType: "FLOAT32" } };
    }
    function evaluatePixel(sample) {
        return [sample.DEM];
    }""",
    input_data=[SentinelHubRequest.input_data(
        data_collection=cdse_dem,
    )],
    responses=[SentinelHubRequest.output_response('default', MimeType.TIFF)],
    bbox=bbox,
    size=(1024, 1024),  # SAME size as imagery fetch -- pixel alignment
    config=config
)

data = request.get_data(save_data=True)
print("Downloaded Copernicus 30m DEM for the EXPANDED Sakri Taluka NPK region.")
print("Saved to sakri_npk_region_elevation/")