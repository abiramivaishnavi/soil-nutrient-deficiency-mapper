from sentinelhub import SHConfig, SentinelHubRequest, DataCollection, MimeType, CRS, BBox

config = SHConfig()
config.sh_client_id = "sh-ef6cf07e-c451-4e70-a437-c04f0616e761"
config.sh_client_secret = "JkwoJf6moUxQ5N1B4esN8m8AMCX0tiSs"
config.sh_base_url = "https://sh.dataspace.copernicus.eu"
config.sh_token_url = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"

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