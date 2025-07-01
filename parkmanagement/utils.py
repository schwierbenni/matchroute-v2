import requests
from django.conf import settings
from openai import OpenAI

GRAPH_HOPPER_KEY = settings.GRAPH_HOPPER_API_KEY
GOOGLE_KEY = settings.GOOGLE_MAPS_API_KEY
OPENWEATHER_KEY = settings.OPENWEATHERMAP_KEY

client = OpenAI(api_key=settings.OPENAI_API_KEY)

def berechne_auto_route(start_adresse, ziel_lat, ziel_lng):
    """
    Nutzt GraphHopper, um Auto-Route von Adresse ➝ Koordinaten zu berechnen.
    Vorher wird die Startadresse geocodiert.
    """
    # 1. Adresse in Koordinaten umwandeln
    geo = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={"q": start_adresse, "format": "json"},
        headers={"User-Agent": "matchroute-app (info@matchroute.de)"},
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
        },
    )
    data = res.json()
    if "paths" not in data or not data["paths"]:
        return None

    pfad = data["paths"][0]
    return {
        "dauer_min": round(pfad["time"] / 60000),
        "distanz_km": round(pfad["distance"] / 1000, 1),
        "polyline": pfad["points"],
    }


def berechne_gesamtzeit_mit_transit_und_walk(start_adresse, parkplatz, stadion):
    ergebnisse = {}

    # 1. Distance Matrix für Auto-Daten (Google API)
    matrix_url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    matrix_params = {
        "origins": start_adresse,
        "destinations": f"{parkplatz.latitude},{parkplatz.longitude}",
        "mode": "driving",
        "departure_time": "now",
        "key": GOOGLE_KEY,
    }

    matrix_resp = requests.get(matrix_url, params=matrix_params).json()
    row = matrix_resp["rows"][0]["elements"][0]

    dauer_normal = row["duration"]["value"]
    dauer_traffic = row.get("duration_in_traffic", {}).get("value", dauer_normal)

    abweichung = (
        (dauer_traffic - dauer_normal) / dauer_normal if dauer_normal > 0 else 0
    )
    bewertung = max(1, 10 - int(abweichung * 10))

    def generiere_verkehrskommentar(score):
        if score >= 9:
            return "Die Straßen sind frei. Du kommst schnell ans Ziel."
        elif score >= 7:
            return "Leichtes Verkehrsaufkommen. Mit Puffer alles gut machbar."
        elif score >= 4:
            return "Es gibt spürbaren Verkehr. Plane genug Zeit ein."
        else:
            return (
                "Die Lage ist angespannt. Stell dich auf deutliche Verzögerungen ein."
            )

    ergebnisse["dauer_auto"] = dauer_normal // 60
    ergebnisse["dauer_traffic"] = dauer_traffic // 60
    ergebnisse["distanz_km"] = round(row["distance"]["value"] / 1000, 1)
    ergebnisse["verkehr_bewertung"] = bewertung
    ergebnisse["verkehr_kommentar"] = generiere_verkehrskommentar(bewertung)

    # 2. Polyline für Autoroute (optional, über Directions API)
    directions = requests.get(
        "https://maps.googleapis.com/maps/api/directions/json",
        params={
            "origin": start_adresse,
            "destination": f"{parkplatz.latitude},{parkplatz.longitude}",
            "mode": "driving",
            "departure_time": "now",
            "key": GOOGLE_KEY,
        },
    ).json()

    if directions["status"] == "OK":
        ergebnisse["polyline_auto"] = directions["routes"][0]["overview_polyline"][
            "points"
        ]

    # 3. Transit & Walking (wie gehabt)
    r_transit = requests.get(
        "https://maps.googleapis.com/maps/api/directions/json",
        params={
            "origin": f"{parkplatz.latitude},{parkplatz.longitude}",
            "destination": f"{stadion.latitude},{stadion.longitude}",
            "mode": "transit",
            "departure_time": "now",
            "key": GOOGLE_KEY,
        },
    )
    d_transit = r_transit.json()
    if d_transit["status"] == "OK":
        ergebnisse["dauer_transit"] = (
            d_transit["routes"][0]["legs"][0]["duration"]["value"] // 60
        )
        ergebnisse["polyline_transit"] = d_transit["routes"][0]["overview_polyline"][
            "points"
        ]
    else:
        ergebnisse["dauer_transit"] = None

    walk_result = berechne_zu_fuss_route(
        (float(parkplatz.latitude), float(parkplatz.longitude)),
        (float(stadion.latitude), float(stadion.longitude)),
    )
    if walk_result:
        ergebnisse["dauer_walking"] = walk_result["dauer_min"]
        ergebnisse["polyline_walking"] = walk_result["polyline"]
    else:
        ergebnisse["dauer_walking"] = None

    # 4. Beste Methode & Gesamtzeit
    if (
        ergebnisse["dauer_transit"] is not None
        and ergebnisse["dauer_walking"] is not None
    ):
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
        return None

    ergebnisse["beste_methode"] = beste
    ergebnisse["gesamt_min"] = ergebnisse["dauer_auto"] + weiterreise

    return ergebnisse


def berechne_zu_fuss_route(start_coords, ziel_coords):
    res = requests.get(
        "https://graphhopper.com/api/1/route",
        params={
            "point": [
                f"{start_coords[0]},{start_coords[1]}",
                f"{ziel_coords[0]},{ziel_coords[1]}",
            ],
            "vehicle": "foot",
            "locale": "de",
            "points_encoded": True,
            "key": GRAPH_HOPPER_KEY,
        },
    )
    data = res.json()
    if "paths" not in data or not data["paths"]:
        return None
    pfad = data["paths"][0]
    return {
        "dauer_min": round(pfad["time"] / 60000),
        "distanz_km": round(pfad["distance"] / 1000, 1),
        "polyline": pfad["points"],
    }


def hole_wetter(lat, lng):
    res = requests.get(
        "https://api.openweathermap.org/data/2.5/weather",
        params={
            "lat": lat,
            "lon": lng,
            "appid": OPENWEATHER_KEY,
            "units": "metric",
            "lang": "de",
        },
    ).json()

    temp = res["main"]["temp"]
    wetter = res["weather"][0]["description"]

    return f"{temp:.0f}°C und {wetter}"


def format_dauer(minuten):
    h = minuten // 60
    m = minuten % 60
    if h > 0:
        return f"{h}h {m}min"
    return f"{m}min"

def generiere_gpt_verkehrstext(dauer_min, dauer_normal_min, wetter, ort):
    abweichung = max(0, dauer_min - dauer_normal_min)
    prozent = (abweichung / dauer_normal_min) * 100 if dauer_normal_min > 0 else 0

    dauer_text = format_dauer(dauer_min)
    normal_text = format_dauer(dauer_normal_min)
    diff_text = format_dauer(abweichung)

    prompt = (
        f"Du bist ein freundlicher Reiseassistent für Stadionbesucher. "
        f"Die normale Fahrt zum Stadion dauert {normal_text}, aktuell jedoch {dauer_text}, "
        f"was etwa {prozent:.0f}% länger ist. "
        f"Das Wetter in {ort} ist derzeit {wetter}. "
        f"Formuliere auf Deutsch einen netten Hinweis in 2–3 Sätzen für den Fan. "
        f"Erkläre kurz die Verzögerung, erwähne das Wetter und gib eine Empfehlung, wie viel Puffer sinnvoll ist. "
        f"Sprich die Person direkt an. Kein Gendern."
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=180,
    )

    return response.choices[0].message.content.strip()