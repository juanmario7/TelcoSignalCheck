import os
import requests
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
GOOGLE_URL = "https://maps.googleapis.com/maps/api/geocode/json"


def geocode(address: str) -> dict | None:
    """
    Convierte una dirección a coordenadas usando Google Maps Geocoding API.
    Retorna {"lat": float, "lng": float, "display_name": str} o None.
    """
    params = {
        "address": f"{address}, Colombia",
        "key": GOOGLE_API_KEY,
        "language": "es",
        "region": "co",
    }
    try:
        resp = requests.get(GOOGLE_URL, params=params, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        if data["status"] == "OK" and data["results"]:
            r = data["results"][0]
            location = r["geometry"]["location"]
            return {
                "lat": location["lat"],
                "lng": location["lng"],
                "display_name": r["formatted_address"],
            }
    except Exception:
        pass
    return None
