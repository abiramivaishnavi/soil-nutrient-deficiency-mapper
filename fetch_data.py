from sentinelhub import SHConfig, SentinelHubRequest, DataCollection, MimeType, CRS, BBox

config = SHConfig()
config.sh_client_id = "sh-ef6cf07e-c451-4e70-a437-c04f0616e761"
config.sh_client_secret = "JkwoJf6moUxQ5N1B4esN8m8AMCX0tiSs"
config.sh_base_url = "https://sh.dataspace.copernicus.eu"
config.sh_token_url = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"

# Re-point the Sentinel-2 L2A collection at the CDSE service URL
cdse_s2l2a = DataCollection.SENTINEL2_L2A.define_from(
    "cdse_s2l2a", service_url=config.sh_base_url
)

bbox = BBox(bbox=[76.64, 12.65, 76.67, 12.68], crs=CRS.WGS84)

dates = ["2026-01-05", "2026-02-24", "2026-03-06"]

for date in dates:
    request = SentinelHubRequest(
        data_folder=f"data/{date}",
        evalscript="""//VERSION=3
        function setup() {
            return { input: ["B04","B05","B08"], output: { bands: 3, sampleType: "FLOAT32" } };
        }
        function evaluatePixel(s) {
            return [s.B04, s.B05, s.B08];
        }""",
        input_data=[SentinelHubRequest.input_data(
            data_collection=cdse_s2l2a,        # ← use the redefined collection here
            time_interval=(date, date))],
        responses=[SentinelHubRequest.output_response('default', MimeType.TIFF)],
        bbox=bbox,
        size=(512, 512),
        config=config
    )
    data = request.get_data(save_data=True)
    print(f"Downloaded data for {date}")