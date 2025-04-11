import requests
from django.conf import settings

# Diese Funktion berechnet die Route von einer Startadresse zu einem Zielort (Latitude, Longitude).
# Sie verwendet die Google Maps Directions API, um die Route zu berechnen und gibt die Dauer, Distanz und Polyline zurück.
# Die Polyline ist eine kodierte Darstellung der Route, die auf einer Karte angezeigt werden kann.
def berechne_route(start_adresse, ziel_lat, ziel_lng):
    base_url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": start_adresse,
        "destination": f"{ziel_lat},{ziel_lng}",
        "key": settings.GOOGLE_MAPS_API_KEY,
        "mode": "driving",
        
    }

    response = requests.get(base_url, params=params)
    data = response.json()

    if data['status'] == 'OK':
        route = data['routes'][0]
        dauer = route['legs'][0]['duration']['value'] // 60  # in Minuten
        distanz = route['legs'][0]['distance']['value'] / 1000  # in km
        polyline = route['overview_polyline']['points']

        return {
            "dauer_min": dauer,
            "distanz_km": distanz,
            "polyline": polyline
        }
    else:
        return None
    
def berechne_gesamtzeit_mit_transit_und_walk(start_adresse, parkplatz, stadion):
    api_key = settings.GOOGLE_MAPS_API_KEY
    ergebnisse = {}

    # 1. Auto: Startadresse ➝ Parkplatz
    r_auto = requests.get(
        "https://maps.googleapis.com/maps/api/directions/json",
        params={
            "origin": start_adresse,
            "destination": f"{parkplatz.latitude},{parkplatz.longitude}",
            "mode": "driving",
            "departure_time": "now",
            "key": api_key
        }
    )
    d_auto = r_auto.json()
    if d_auto["status"] != "OK":
        return None

    ergebnisse["dauer_auto"] = d_auto["routes"][0]["legs"][0]["duration_in_traffic"]["value"] // 60
    ergebnisse["distanz_km"] = d_auto["routes"][0]["legs"][0]["distance"]["value"] / 1000
    ergebnisse["polyline_auto"] = d_auto["routes"][0]["overview_polyline"]["points"]

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
    r_walk = requests.get(
        "https://maps.googleapis.com/maps/api/directions/json",
        params={
            "origin": f"{parkplatz.latitude},{parkplatz.longitude}",
            "destination": f"{stadion.latitude},{stadion.longitude}",
            "mode": "walking",
            "departure_time": "now",
            "key": api_key
        }
    )
    d_walk = r_walk.json()
    if d_walk["status"] == "OK":
        ergebnisse["dauer_walking"] = d_walk["routes"][0]["legs"][0]["duration"]["value"] // 60
        ergebnisse["polyline_walking"] = d_walk["routes"][0]["overview_polyline"]["points"]
    else:
        ergebnisse["dauer_walking"] = None

    # 4. Vergleich
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