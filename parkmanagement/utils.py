import requests
from django.conf import settings

GRAPH_HOPPER_KEY = settings.GRAPH_HOPPER_API_KEY
GOOGLE_KEY = settings.GOOGLE_MAPS_API_KEY


def berechne_auto_route(start_adresse, ziel_lat, ziel_lng):
    """
    Nutzt GraphHopper, um Auto-Route von Adresse ➝ Koordinaten zu berechnen.
    Vorher wird die Startadresse geocodiert.
    """
    # 1. Adresse in Koordinaten umwandeln
    geo = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={"q": start_adresse, "format": "json"},
        headers={"User-Agent": "matchroute-app (info@matchroute.de)"}
    )
    print(geo)
    geo = geo.json()
    if not geo:
        return None

    start_lat = geo[0]["lat"]
    start_lng = geo[0]["lon"]

    # 2. GraphHopper Routing
    res = requests.get(
        "https://graphhopper.com/api/1/route",
        params={
            "point": [f"{start_lat},{start_lng}", f"{ziel_lat},{ziel_lng}"],
            "vehicle": "car",
            "locale": "de",
            "points_encoded": True,
            "key": GRAPH_HOPPER_KEY,
        }
    )
    data = res.json()
    if "paths" not in data or not data["paths"]:
        return None

    pfad = data["paths"][0]
    return {
        "dauer_min": round(pfad["time"] / 60000),
        "distanz_km": round(pfad["distance"] / 1000, 1),
        "polyline": pfad["points"]
    }


def berechne_gesamtzeit_mit_transit_und_walk(start_adresse, parkplatz, stadion):
    api_key = GOOGLE_KEY
    ergebnisse = {}

    # 1. Auto: Startadresse ➝ Parkplatz (via GraphHopper)
    auto_result = berechne_auto_route(
        start_adresse, float(parkplatz.latitude), float(parkplatz.longitude)
    )
    if not auto_result:
        return None

    ergebnisse["dauer_auto"] = auto_result["dauer_min"]
    ergebnisse["distanz_km"] = auto_result["distanz_km"]
    ergebnisse["polyline_auto"] = auto_result["polyline"]

    # 2. ÖPNV: Parkplatz ➝ Stadion
    r_transit = requests.get(
        "https://maps.googleapis.com/maps/api/directions/json",
        params={
            "origin": f"{parkplatz.latitude},{parkplatz.longitude}",
            "destination": f"{stadion.latitude},{stadion.longitude}",
            "mode": "transit",
            "departure_time": "now",
            "key": api_key
        }
    )
    d_transit = r_transit.json()
    if d_transit["status"] == "OK":
        ergebnisse["dauer_transit"] = d_transit["routes"][0]["legs"][0]["duration"]["value"] // 60
        ergebnisse["polyline_transit"] = d_transit["routes"][0]["overview_polyline"]["points"]
    else:
        ergebnisse["dauer_transit"] = None

    # 3. Zu Fuß: Parkplatz ➝ Stadion
    walk_result = berechne_zu_fuss_route(
        (float(parkplatz.latitude), float(parkplatz.longitude)),
        (float(stadion.latitude), float(stadion.longitude))
    )
    if walk_result:
        ergebnisse["dauer_walking"] = walk_result["dauer_min"]
        ergebnisse["polyline_walking"] = walk_result["polyline"]
    else:
        ergebnisse["dauer_walking"] = None

    # 4. Vergleich Transit vs. Walking
    if ergebnisse["dauer_transit"] is not None and ergebnisse["dauer_walking"] is not None:
        if ergebnisse["dauer_transit"] < ergebnisse["dauer_walking"]:
            beste = "transit"
            weiterreise = ergebnisse["dauer_transit"]
        else:
            beste = "walking"
            weiterreise = ergebnisse["dauer_walking"]
    elif ergebnisse["dauer_transit"] is not None:
        beste = "transit"
        weiterreise = ergebnisse["dauer_transit"]
    elif ergebnisse["dauer_walking"] is not None:
        beste = "walking"
        weiterreise = ergebnisse["dauer_walking"]
    else:
        return None  # beides gescheitert

    ergebnisse["beste_methode"] = beste
    ergebnisse["gesamt_min"] = ergebnisse["dauer_auto"] + weiterreise

    return ergebnisse

def berechne_zu_fuss_route(start_coords, ziel_coords):
    res = requests.get(
        "https://graphhopper.com/api/1/route",
        params={
            "point": [f"{start_coords[0]},{start_coords[1]}", f"{ziel_coords[0]},{ziel_coords[1]}"],
            "vehicle": "foot",
            "locale": "de",
            "points_encoded": True,
            "key": GRAPH_HOPPER_KEY,
        }
    )
    data = res.json()
    if "paths" not in data or not data["paths"]:
        return None
    pfad = data["paths"][0]
    return {
        "dauer_min": round(pfad["time"] / 60000),
        "distanz_km": round(pfad["distance"] / 1000, 1),
        "polyline": pfad["points"]
    }