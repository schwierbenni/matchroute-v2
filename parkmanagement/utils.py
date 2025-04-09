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