"""
Routing & Facility Service — Phase 7
Uses Overpass API (free, no key) to find nearest:
- Hospitals
- Fire stations
- Cooling centers (libraries, malls, community centers)

Uses OSRM public API (free, no key) to generate real road route GeoJSON.
"""
import logging
import requests

logger = logging.getLogger("hres.routing")

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
OSRM_URL = "https://router.project-osrm.org/route/v1/driving"

FACILITY_RADIUS_M = 5000  # 5km search radius


def _overpass_query(lat: float, lon: float, amenity: str, radius: int = FACILITY_RADIUS_M) -> list[dict]:
    """Query Overpass API for nearest amenity."""
    query = f"""
    [out:json][timeout:10];
    (
      node["amenity"="{amenity}"](around:{radius},{lat},{lon});
      way["amenity"="{amenity}"](around:{radius},{lat},{lon});
    );
    out center 5;
    """
    try:
        resp = requests.post(OVERPASS_URL, data={"data": query}, timeout=12)
        resp.raise_for_status()
        elements = resp.json().get("elements", [])
        results = []
        for el in elements[:5]:
            tags = el.get("tags", {})
            # Get center coords
            if el.get("type") == "node":
                el_lat, el_lon = el["lat"], el["lon"]
            else:
                el_lat = el.get("center", {}).get("lat", lat)
                el_lon = el.get("center", {}).get("lon", lon)

            name = tags.get("name", f"Nearest {amenity.replace('_', ' ').title()}")
            results.append({
                "name": name,
                "lat": el_lat,
                "lon": el_lon,
                "amenity": amenity,
                "tags": {k: v for k, v in tags.items() if k in ("phone", "website", "opening_hours", "addr:street")},
            })
        return results
    except Exception as e:
        logger.warning(f"Overpass query failed for {amenity}: {e}")
        return []


def _overpass_cooling_centers(lat: float, lon: float) -> list[dict]:
    """Find cooling centers: libraries, community centres, malls."""
    results = []
    for amenity in ("library", "community_centre", "mall"):
        found = _overpass_query(lat, lon, amenity, radius=3000)
        for f in found:
            f["amenity"] = "cooling_center"
            f["subtype"] = amenity
            results.append(f)
        if results:
            break
    return results[:3]


def _osrm_route(
    from_lat: float, from_lon: float,
    to_lat: float, to_lon: float
) -> dict | None:
    """Get OSRM road route — returns GeoJSON LineString."""
    try:
        url = f"{OSRM_URL}/{from_lon},{from_lat};{to_lon},{to_lat}"
        params = {"overview": "full", "geometries": "geojson", "steps": "false"}
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        routes = data.get("routes", [])
        if not routes:
            return None
        route = routes[0]
        return {
            "geometry": route["geometry"],  # GeoJSON LineString
            "distance_m": route["distance"],
            "duration_s": route["duration"],
            "distance_km": round(route["distance"] / 1000, 2),
            "duration_min": round(route["duration"] / 60, 1),
        }
    except Exception as e:
        logger.warning(f"OSRM routing failed: {e}")
        return None


def get_nearest_facilities(lat: float, lon: float) -> dict:
    """
    Find nearest hospital, fire station, and cooling center.
    Returns structured dict with facility info + route GeoJSON.
    """
    logger.info(f"Looking up facilities near ({lat}, {lon})")

    hospitals = _overpass_query(lat, lon, "hospital")
    fire_stations = _overpass_query(lat, lon, "fire_station")
    cooling_centers = _overpass_cooling_centers(lat, lon)

    result = {
        "hospital": None,
        "fire_station": None,
        "cooling_center": None,
    }

    if hospitals:
        h = hospitals[0]
        route = _osrm_route(lat, lon, h["lat"], h["lon"])
        result["hospital"] = {**h, "route": route}
    else:
        # Fallback for demo if Overpass API fails or rate limits
        result["hospital"] = {
            "name": "City General Hospital (Demo Fallback)",
            "lat": lat + 0.015,
            "lon": lon + 0.015,
            "route": {"distance_km": 2.4, "duration_min": 6.5}
        }

    if fire_stations:
        fs = fire_stations[0]
        route = _osrm_route(lat, lon, fs["lat"], fs["lon"])
        result["fire_station"] = {**fs, "route": route}
    else:
        # Fallback for demo if Overpass API fails
        result["fire_station"] = {
            "name": "Central Fire Rescue (Demo Fallback)",
            "lat": lat - 0.012,
            "lon": lon + 0.008,
            "route": {"distance_km": 1.8, "duration_min": 4.0}
        }

    if cooling_centers:
        cc = cooling_centers[0]
        route = _osrm_route(lat, lon, cc["lat"], cc["lon"])
        result["cooling_center"] = {**cc, "route": route}
    else:
        result["cooling_center"] = {
            "name": "Community Library Center (Demo Fallback)",
            "lat": lat - 0.005,
            "lon": lon - 0.005,
            "route": {"distance_km": 0.8, "duration_min": 2.0}
        }

    logger.info(f"Facilities found: hospital={bool(result['hospital'])}, fire={bool(result['fire_station'])}, cooling={bool(result['cooling_center'])}")
    return result
