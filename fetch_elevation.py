from sentinelhub import SHConfig, SentinelHubRequest, DataCollection, MimeType, CRS, BBox

config = SHConfig()
config.sh_client_id = "sh-ef6cf07e-c451-4e70-a437-c04f0616e761"
config.sh_client_secret = "JkwoJf6moUxQ5N1B4esN8m8AMCX0tiSs"
config.sh_base_url = "https://sh.dataspace.copernicus.eu"
config.sh_token_url = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"

cdse_dem = DataCollection.DEM_COPERNICUS_30.define_from(
    "cdse_dem", service_url=config.sh_base_url
)

# Same bounding box as your Sentinel-2 imagery, for pixel alignment
bbox = BBox(bbox=[74.320, 20.870, 74.420, 20.970], crs=CRS.WGS84)

request = SentinelHubRequest(
    data_folder="sakri_elevation",
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
    size=(1024, 1024),   # same size as your Sentinel-2 fetch, for alignment
    config=config
)

data = request.get_data(save_data=True)
print("Downloaded Copernicus 30m DEM elevation data for Sakri region.")