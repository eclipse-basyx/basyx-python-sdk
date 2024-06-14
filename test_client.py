import json
import requests
from basyx.aas.adapter.json import AASFromJsonDecoder
from basyx.aas.adapter import http as aas_http

BASE_URL = "http://127.0.0.1:8080/api/v3.0"

def get_aas_by_id(aas_id):
    response = requests.get(f"{BASE_URL}/shells/{aas_http.base64url_encode(aas_id)}")
    if response.ok:
        # Use the AASFromJsonDecoder to decode the JSON response
        aas = json.loads(response.text, cls=AASFromJsonDecoder)
        return aas
    else:
        return None

# Example usage
if __name__ == "__main__":
    # Assuming you have an AAS ID, retrieve a specific AAS by its ID
    aas_id = "https://acplt.org/Test_AssetAdministrationShell"  # Replace with an actual ID
    print(f"Retrieving AAS by ID: {aas_id}")
    aas = get_aas_by_id(aas_id)
    print(aas)