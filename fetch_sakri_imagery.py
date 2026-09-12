from sentinelhub import SentinelHubRequest, DataCollection, MimeType, CRS, BBox
# pyrefly: ignore [missing-import]
from sentinel_config import get_config

config = get_config()

cdse_s2l2a = DataCollection.SENTINEL2_L2A.define_from(
    "cdse_s2l2a", service_url=config.sh_base_url
)

bbox = BBox(bbox=[74.320, 20.870, 74.420, 20.970], crs=CRS.WGS84)

request = SentinelHubRequest(
    data_folder="sakri_imagery",
    evalscript="""//VERSION=3
    function setup() {
        return { input: ["B02","B03","B04","B05","B08"], output: { bands: 5, sampleType: "FLOAT32" } };
    }
    function evaluatePixel(s) {
        return [s.B02, s.B03, s.B04, s.B05, s.B08];
    }""",
    input_data=[SentinelHubRequest.input_data(
        data_collection=cdse_s2l2a,
        time_interval=("2024-08-01", "2024-09-30"),
        mosaicking_order="leastCC"
    )],
    responses=[SentinelHubRequest.output_response('default', MimeType.TIFF)],
    bbox=bbox,
    size=(1024, 1024),
    config=config
)

data = request.get_data(save_data=True)
print("Downloaded real Sentinel-2 imagery for Sakri region (5 bands: Blue, Green, Red, Red-Edge, NIR).")