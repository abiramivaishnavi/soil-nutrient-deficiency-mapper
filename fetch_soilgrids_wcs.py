import requests
from pyproj import Transformer

# Sakri bounding box (same as your Sentinel-2 imagery)
BBOX_WGS84 = [74.320, 20.870, 74.420, 20.970]  # [minlon, minlat, maxlon, maxlat]

# SoilGrids uses "Homolosine" projection - convert our lat/lon box to it
transformer = Transformer.from_crs("EPSG:4326", "+proj=igh +lat_0=0 +lon_0=0 +datum=WGS84 +units=m +no_defs", always_xy=True)

x_min, y_min = transformer.transform(BBOX_WGS84[0], BBOX_WGS84[1])
x_max, y_max = transformer.transform(BBOX_WGS84[2], BBOX_WGS84[3])

print(f"Homolosine bbox: X({x_min}, {x_max}), Y({y_min}, {y_max})")

def fetch_soilgrids_wcs(map_name, coverage_id, out_file):
    url = "https://maps.isric.org/mapserv"
    params = {
        "map": f"/map/{map_name}.map",
        "SERVICE": "WCS",
        "VERSION": "2.0.1",
        "REQUEST": "GetCoverage",
        "COVERAGEID": coverage_id,
        "FORMAT": "GEOTIFF_INT16",
        "SUBSET": [f"X({x_min},{x_max})", f"Y({y_min},{y_max})"],
        "SUBSETTINGCRS": "http://www.opengis.net/def/crs/EPSG/0/152160",
        "OUTPUTCRS": "http://www.opengis.net/def/crs/EPSG/0/152160",
    }
    r = requests.get(url, params=params)
    print(f"{coverage_id}: status {r.status_code}, size {len(r.content)} bytes")
    if r.status_code == 200 and len(r.content) > 500:
        with open(out_file, "wb") as f:
            f.write(r.content)
        print(f"Saved {out_file}")
    else:
        print("Response preview:", r.text[:300])

print("\nFetching Nitrogen...")
fetch_soilgrids_wcs("nitrogen", "nitrogen_0-5cm_mean", "sakri_soilgrids_nitrogen.tif")

print("\nFetching CEC (potassium-holding-capacity proxy)...")
fetch_soilgrids_wcs("cec", "cec_0-5cm_mean", "sakri_soilgrids_cec.tif")