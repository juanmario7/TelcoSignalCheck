import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
HEADERS = {"User-Agent": "TelcoSignalCheck/1.0"}


def geocode(address: str) -> dict | None:
    """
    Convierte una dirección a coordenadas.
    Prioriza Colombia. Retorna {"lat": float, "lng": float, "display_name": str} o None.
    """
    params = {
        "q": f"{address}, Colombia",
        "format": "json",
        "limit": 1,
        "countrycodes": "co",
        "addressdetails": 1,
    }
    try:
        resp = requests.get(NOMINATIM_URL, params=params, headers=HEADERS, timeout=5)
        resp.raise_for_status()
        results = resp.json()
        if results:
            r = results[0]
            return {
                "lat": float(r["lat"]),
                "lng": float(r["lon"]),
                "display_name": r["display_name"],
            }
    except Exception:
        pass
    return None
