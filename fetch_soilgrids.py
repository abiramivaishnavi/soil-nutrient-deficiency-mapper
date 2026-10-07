import requests

BBOX = [74.320, 20.870, 74.420, 20.970]  # Sakri bounding box

def fetch_soilgrids_layer(property_name, depth="0-5cm", stat="mean"):
    url = "https://rest.isric.org/soilgrids/v2.0/properties/query"
    params = {
        "lon": (BBOX[0] + BBOX[2]) / 2,
        "lat": (BBOX[1] + BBOX[3]) / 2,
        "property": property_name,
        "depth": depth,
        "value": stat
    }
    r = requests.get(url, params=params)
    r.raise_for_status()
    return r.json()

print("Testing SoilGrids API for Sakri center point...")

nitrogen_result = fetch_soilgrids_layer("nitrogen")
print("\nNitrogen result:")
print(nitrogen_result)

cec_result = fetch_soilgrids_layer("cec")
print("\nCEC result (potassium-holding-capacity proxy):")
print(cec_result)