import requests
import time


BASE_URL = "https://api.fortyguard.com"


def submit_heatmap(api_key, coordinates=None):

    url = f"{BASE_URL}/v1/heatmap"

    headers = {
        "api-key": api_key,
        "Content-Type": "application/json"
    }

    if coordinates is None:
        coordinates = [[
            [-74.0170, 40.7050],
            [-74.0030, 40.7050],
            [-74.0030, 40.7180],
            [-74.0170, 40.7180],
            [-74.0170, 40.7050]
        ]]

    payload = {
        "polygon_aoi": {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": coordinates
                    }
                }
            ]
        },

        "date_time": {
            "start_date": "2024-07-15",
            "start_time": "14:00",
            "filter_type": 1
        },

        "granularity": 100
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    activity_id = data["data"]["activity_id"]

    return activity_id


def check_heatmap_status(api_key, activity_id):

    status_url = f"{BASE_URL}/v1/status/{activity_id}"

    headers = {
        "api-key": api_key
    }

    response = requests.get(
        status_url,
        headers=headers,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    status = data["data"]["status"]

    return status, data


def wait_for_heatmap(api_key, activity_id):

    while True:

        try:

            status, status_data = check_heatmap_status(
                api_key,
                activity_id
            )

            print("Current heatmap status:", status)

            if status == "Completed":

                print("Heatmap generation completed!")

                result = status_data["data"]["result"]

                return result

            elif status == "Processing":

                print("Heatmap is still being generated...")

                time.sleep(5)

            else:

                print("Heatmap ended with status:", status)

                return None

        except requests.exceptions.RequestException as e:

            print("Status request failed:", e)
            print("Retrying in 5 seconds...")

            time.sleep(5)