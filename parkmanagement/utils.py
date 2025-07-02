import requests
from django.conf import settings
from openai import OpenAI
import math
from datetime import datetime, time
import logging

# Import der neuen Dortmund Parking API
try:
    from .dortmund_parking_api import (
        DortmundParkingData,
        enrich_parkplatz_with_live_data,
        get_dortmund_parking_overview
    )
    DORTMUND_INTEGRATION_AVAILABLE = True
except ImportError:
    DORTMUND_INTEGRATION_AVAILABLE = False
    logging.warning("Dortmund Parking API Integration nicht verfügbar")

GOOGLE_KEY = settings.GOOGLE_MAPS_API_KEY
OPENWEATHER_KEY = settings.OPENWEATHERMAP_KEY

client = OpenAI(api_key=settings.OPENAI_API_KEY)
logger = logging.getLogger(__name__)


def berechne_realistische_verkehrsbewertung(normal_dauer_sekunden, traffic_dauer_sekunden, tageszeit=None, wochentag=None):
    """
    Berechnet eine realistische Verkehrsbewertung basierend auf:
    - Verkehrsverzögerung in Prozent
    - Tageszeit (Rush Hour Faktoren)
    - Wochentag (Wochenende vs. Werktag)
    - Absolute Verzögerungszeit
    
    Skala: 1-5 (statt 1-10) für realistischere Bewertung
    5 = Excellent (freie Fahrt)
    4 = Good (leichte Verzögerung)
    3 = Fair (moderate Verzögerung) 
    2 = Poor (starke Verzögerung)
    1 = Critical (extreme Verzögerung)
    """
    
    if normal_dauer_sekunden == 0:
        return 3, "Keine Verkehrsdaten verfügbar"
    
    # Verzögerung in Prozent
    verzoegerung_prozent = ((traffic_dauer_sekunden - normal_dauer_sekunden) / normal_dauer_sekunden) * 100
    
    # Absolute Verzögerung in Minuten
    verzoegerung_minuten = (traffic_dauer_sekunden - normal_dauer_sekunden) / 60
    
    # Base Score basierend auf Verzögerung
    if verzoegerung_prozent <= 5:  # Bis 5% Verzögerung
        base_score = 5
    elif verzoegerung_prozent <= 15:  # 5-15% Verzögerung
        base_score = 4
    elif verzoegerung_prozent <= 35:  # 15-35% Verzögerung
        base_score = 3
    elif verzoegerung_prozent <= 60:  # 35-60% Verzögerung
        base_score = 2
    else:  # Über 60% Verzögerung
        base_score = 1
    
    # Tageszeit-Faktor (falls verfügbar)
    if tageszeit:
        hour = tageszeit.hour if isinstance(tageszeit, datetime) else tageszeit
        
        # Rush Hour Penalties
        if 7 <= hour <= 9 or 17 <= hour <= 19:  # Hauptverkehrszeiten
            if verzoegerung_prozent > 10:
                base_score = max(1, base_score - 1)  # Ein Punkt Abzug
        elif 22 <= hour or hour <= 6:  # Nachtzeit
            if verzoegerung_prozent < 20:  # Nachts sollte wenig Verkehr sein
                base_score = min(5, base_score + 1)  # Bonus für gute Nachtzeit-Performance
    
    # Wochentag-Faktor
    if wochentag is not None:
        if wochentag in [5, 6]:  # Samstag/Sonntag (0=Montag)
            if verzoegerung_prozent < 25:  # Wochenende sollte entspannter sein
                base_score = min(5, base_score + 1)
    
    # Absolute Verzögerung berücksichtigen
    if verzoegerung_minuten > 15:  # Mehr als 15 Minuten Verzögerung ist immer schlecht
        base_score = min(base_score, 2)
    elif verzoegerung_minuten > 30:  # Mehr als 30 Minuten ist kritisch
        base_score = 1
    
    # Kommentar generieren
    kommentar = generiere_realistischen_verkehrskommentar(
        base_score, verzoegerung_prozent, verzoegerung_minuten, tageszeit
    )
    
    return base_score, kommentar


def generiere_realistischen_verkehrskommentar(score, verzoegerung_prozent, verzoegerung_minuten, tageszeit=None):
    """Generiert realistische Kommentare basierend auf der Verkehrssituation."""
    
    hour = None
    if tageszeit:
        hour = tageszeit.hour if isinstance(tageszeit, datetime) else tageszeit
    
    # Zeitspezifische Präfixe
    zeit_kontext = ""
    if hour:
        if 7 <= hour <= 9:
            zeit_kontext = "Zur Hauptverkehrszeit "
        elif 17 <= hour <= 19:
            zeit_kontext = "Im Feierabendverkehr "
        elif 22 <= hour or hour <= 6:
            zeit_kontext = "Zur Nachtzeit "
        elif 10 <= hour <= 16:
            zeit_kontext = "Zur Mittagszeit "
    
    if score == 5:  # Excellent
        kommentare = [
            f"{zeit_kontext}läuft der Verkehr sehr flüssig. Optimale Bedingungen!",
            f"Freie Fahrt! {zeit_kontext}sind die Straßen entspannt.",
            f"{zeit_kontext}herrscht kaum Verkehr. Perfekte Reisebedingungen!"
        ]
    elif score == 4:  # Good
        kommentare = [
            f"{zeit_kontext}ist mit leichten Verzögerungen zu rechnen ({int(verzoegerung_minuten)}min extra).",
            f"Gute Verkehrslage {zeit_kontext}mit nur minimalen Staus.",
            f"{zeit_kontext}läuft es größtenteils flüssig, vereinzelt langsamerer Verkehr."
        ]
    elif score == 3:  # Fair
        kommentare = [
            f"{zeit_kontext}herrscht mäßiger Verkehr. Planen Sie {int(verzoegerung_minuten)} Minuten Puffer ein.",
            f"Durchschnittliche Verkehrslage {zeit_kontext}mit spürbaren Verzögerungen.",
            f"{zeit_kontext}ist mit Stop-and-Go-Verkehr zu rechnen."
        ]
    elif score == 2:  # Poor
        kommentare = [
            f"{zeit_kontext}herrscht dichter Verkehr! {int(verzoegerung_minuten)}min Mehrzeit einplanen.",
            f"Schwierige Verkehrslage {zeit_kontext}mit erheblichen Staus.",
            f"{zeit_kontext}stockt der Verkehr deutlich. Früher losfahren empfohlen!"
        ]
    else:  # Critical
        kommentare = [
            f"{zeit_kontext}herrscht extremer Stau! Mindestens {int(verzoegerung_minuten)}min Mehrzeit.",
            f"Kritische Verkehrslage {zeit_kontext}! Alternative Routen prüfen.",
            f"{zeit_kontext}ist mit massiven Verzögerungen zu rechnen. Viel Geduld nötig!"
        ]
    
    import random
    return random.choice(kommentare)


def generiere_google_maps_navigation_link(start_adresse, parkplatz_lat, parkplatz_lng, stadion_lat=None, stadion_lng=None):
    """
    Generiert einen Google Maps Link für die Navigation.
    """
    import urllib.parse
    
    # Basis-Parameter
    base_url = "https://www.google.com/maps/dir/"
    
    # Einfache Route: Start → Parkplatz
    simple_route = f"{base_url}{urllib.parse.quote(start_adresse)}/{parkplatz_lat},{parkplatz_lng}"
    
    # Multi-Stop Route: Start → Parkplatz → Stadion (falls Stadion-Koordinaten verfügbar)
    multi_stop_route = None
    if stadion_lat and stadion_lng:
        multi_stop_route = f"{base_url}{urllib.parse.quote(start_adresse)}/{parkplatz_lat},{parkplatz_lng}/{stadion_lat},{stadion_lng}"
    
    # Mobile App Links (deep links)
    mobile_link = f"https://maps.google.com/?daddr={parkplatz_lat},{parkplatz_lng}&saddr={urllib.parse.quote(start_adresse)}"
    
    return {
        "web_link": simple_route,
        "multi_stop_link": multi_stop_route,
        "mobile_link": mobile_link,
        "parkplatz_coords": f"{parkplatz_lat},{parkplatz_lng}"
    }


def berechne_google_route(origin, destination, mode="driving", departure_time="now"):
    """
    Universelle Google Directions API Funktion für alle Verkehrsmittel.
    """
    url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": origin,
        "destination": destination,
        "mode": mode,
        "key": GOOGLE_KEY,
        "language": "de",
        "region": "DE"
    }
    
    # Verkehrsdaten nur für Auto-Modus
    if mode == "driving":
        params["departure_time"] = departure_time
        params["traffic_model"] = "best_guess"
        params["avoid"] = "tolls"  # Mautstraßen vermeiden für Deutschland
    
    # Transit-spezifische Parameter
    if mode == "transit":
        params["departure_time"] = departure_time
        params["transit_mode"] = "bus|subway|train|tram"
        params["transit_routing_preference"] = "fewer_transfers"
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data["status"] == "OK" and data["routes"]:
            route = data["routes"][0]
            leg = route["legs"][0]
            
            result = {
                "dauer_sekunden": leg["duration"]["value"],
                "dauer_minuten": leg["duration"]["value"] // 60,
                "distanz_meter": leg["distance"]["value"],
                "distanz_km": round(leg["distance"]["value"] / 1000, 1),
                "polyline": route["overview_polyline"]["points"],
                "start_adresse": leg["start_address"],
                "end_adresse": leg["end_address"],
                "status": "success"
            }
            
            # Verkehrsdaten für Auto-Modus
            if mode == "driving" and "duration_in_traffic" in leg:
                result["dauer_traffic_sekunden"] = leg["duration_in_traffic"]["value"]
                result["dauer_traffic_minuten"] = leg["duration_in_traffic"]["value"] // 60
            
            return result
            
        else:
            print(f"Google Directions API Fehler: {data.get('status', 'UNKNOWN')}")
            return None
            
    except Exception as e:
        print(f"Fehler bei Google Directions API: {e}")
        return None


def berechne_gesamtzeit_mit_realistischer_bewertung(start_adresse, parkplatz, stadion):
    """
    Erweiterte Routenberechnung mit realistischer Verkehrsbewertung.
    """
    ergebnisse = {}
    parkplatz_coords = f"{parkplatz.latitude},{parkplatz.longitude}"
    stadion_coords = f"{stadion.latitude},{stadion.longitude}"
    
    # Aktuelle Zeit für Verkehrsbewertung
    jetzt = datetime.now()
    
    # 1. Auto-Route mit Verkehrsdaten
    auto_route = berechne_google_route(
        origin=start_adresse,
        destination=parkplatz_coords,
        mode="driving"
    )
    
    if not auto_route:
        return None
    
    # Realistische Verkehrsbewertung
    normal_sekunden = auto_route["dauer_sekunden"]
    traffic_sekunden = auto_route.get("dauer_traffic_sekunden", normal_sekunden)
    
    bewertung, kommentar = berechne_realistische_verkehrsbewertung(
        normal_sekunden, 
        traffic_sekunden, 
        tageszeit=jetzt,
        wochentag=jetzt.weekday()
    )
    
    # Navigation Links generieren
    nav_links = generiere_google_maps_navigation_link(
        start_adresse, 
        parkplatz.latitude, 
        parkplatz.longitude,
        stadion.latitude,
        stadion.longitude
    )
    
    ergebnisse.update({
        "dauer_auto": auto_route["dauer_minuten"],
        "dauer_traffic": auto_route.get("dauer_traffic_minuten", auto_route["dauer_minuten"]),
        "distanz_km": auto_route["distanz_km"],
        "polyline_auto": auto_route["polyline"],
        "verkehr_bewertung": bewertung,
        "verkehr_kommentar": kommentar,
        "navigation_links": nav_links
    })
    
    # 2. Transit-Route (Parkplatz → Stadion)
    transit_route = berechne_google_route(
        origin=parkplatz_coords,
        destination=stadion_coords,
        mode="transit"
    )
    
    if transit_route:
        ergebnisse["dauer_transit"] = transit_route["dauer_minuten"]
        ergebnisse["polyline_transit"] = transit_route["polyline"]
    else:
        ergebnisse["dauer_transit"] = None
        ergebnisse["polyline_transit"] = None
    
    # 3. Fußweg (Parkplatz → Stadion)
    walking_route = berechne_google_route(
        origin=parkplatz_coords,
        destination=stadion_coords,
        mode="walking"
    )
    
    if walking_route:
        ergebnisse["dauer_walking"] = walking_route["dauer_minuten"]
        ergebnisse["polyline_walking"] = walking_route["polyline"]
        
        # Zusätzliche Navigation Links für Fußweg
        walking_nav = generiere_google_maps_navigation_link(
            f"{parkplatz.latitude},{parkplatz.longitude}",
            stadion.latitude,
            stadion.longitude
        )
        ergebnisse["walking_navigation"] = walking_nav
    else:
        ergebnisse["dauer_walking"] = None
        ergebnisse["polyline_walking"] = None
    
    # 4. Beste Methode ermitteln
    weiterreise_optionen = []
    if ergebnisse["dauer_transit"]:
        weiterreise_optionen.append(("transit", ergebnisse["dauer_transit"]))
    if ergebnisse["dauer_walking"]:
        weiterreise_optionen.append(("walking", ergebnisse["dauer_walking"]))
    
    if not weiterreise_optionen:
        return None
    
    beste_methode, beste_zeit = min(weiterreise_optionen, key=lambda x: x[1])
    
    ergebnisse["beste_methode"] = beste_methode
    ergebnisse["gesamt_min"] = ergebnisse["dauer_traffic"] + beste_zeit
    
    return ergebnisse


def berechne_optimierte_parkplatz_empfehlung_mit_live_daten(start_adresse, parkplaetze, stadion):
    """
    🎯 NEUE HAUPTFUNKTION: Erweiterte Parkplatz-Empfehlung mit Dortmund Live-Daten
    
    Diese Funktion integriert die Echtzeit-Parkplatzdaten von Dortmund Open Data
    in die bestehende Routenberechnung für wissenschaftliche Anwendungsfälle.
    """
    if not parkplaetze:
        return []
    
    logger.info(f"🚀 Berechne Routen für {len(parkplaetze)} Parkplätze mit Live-Daten Integration")
    
    # 1. Hole Live-Daten von Dortmund (falls verfügbar)
    live_data_list = []
    if DORTMUND_INTEGRATION_AVAILABLE:
        try:
            live_data_list = DortmundParkingData.fetch_live_parking_data() or []
            if live_data_list:
                logger.info(f"✅ {len(live_data_list)} Live-Parkplätze von Dortmund geladen")
            else:
                logger.info("ℹ️ Keine Live-Daten verfügbar - verwende nur Routenberechnung")
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Live-Daten: {e}")
            live_data_list = []
    
    # 2. Berechne Routen für alle Parkplätze
    vorschlaege = []
    
    for parkplatz in parkplaetze:
        logger.info(f"🔄 Berechne Route für: {parkplatz.name}")
        
        result = berechne_gesamtzeit_mit_realistischer_bewertung(
            start_adresse, parkplatz, stadion
        )
        
        if result:
            vorschlag = {
                "parkplatz": {
                    "id": parkplatz.id,
                    "name": parkplatz.name,
                    "latitude": float(parkplatz.latitude),
                    "longitude": float(parkplatz.longitude),
                },
                "dauer_auto": result.get("dauer_auto"),
                "dauer_traffic": result.get("dauer_traffic"),
                "verkehr_bewertung": result.get("verkehr_bewertung"),
                "verkehr_kommentar": result.get("verkehr_kommentar"),
                "dauer_transit": result.get("dauer_transit"),
                "dauer_walking": result.get("dauer_walking"),
                "beste_methode": result.get("beste_methode"),
                "gesamtzeit": result.get("gesamt_min"),
                "distanz_km": result.get("distanz_km"),
                "polyline_auto": result.get("polyline_auto"),
                "polyline_transit": result.get("polyline_transit"),
                "polyline_walking": result.get("polyline_walking"),
                "navigation_links": result.get("navigation_links"),
                "walking_navigation": result.get("walking_navigation"),
                # Placeholder für Live-Daten
                "has_live_data": False,
                "live_parking_data": None
            }
            
            # 3. Live-Daten Integration (falls verfügbar)
            if live_data_list and DORTMUND_INTEGRATION_AVAILABLE:
                try:
                    vorschlag = enrich_parkplatz_with_live_data(vorschlag, live_data_list)
                except Exception as e:
                    logger.error(f"⚠️ Fehler bei Live-Daten Integration für {parkplatz.name}: {e}")
            
            vorschlaege.append(vorschlag)
        else:
            logger.warning(f"⚠️ Keine Route gefunden für: {parkplatz.name}")
    
    # 4. Sortierung nach Gesamtzeit
    sorted_vorschlaege = sorted(vorschlaege, key=lambda x: x["gesamtzeit"] or float('inf'))
    
    logger.info(f"✅ {len(sorted_vorschlaege)} Parkplatz-Vorschläge erfolgreich berechnet")
    
    return sorted_vorschlaege


# Backwards compatibility - alte Funktion leitet an neue weiter
def berechne_optimierte_parkplatz_empfehlung(start_adresse, parkplaetze, stadion):
    """
    Legacy-Funktion für Rückwärtskompatibilität.
    Leitet an die neue Funktion mit Live-Daten weiter.
    """
    return berechne_optimierte_parkplatz_empfehlung_mit_live_daten(start_adresse, parkplaetze, stadion)


def hole_wetter_mit_verkehrseinfluss(lat, lng):
    """
    Erweiterte Wetterfunktion die auch Verkehrsauswirkungen berücksichtigt.
    """
    try:
        res = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={
                "lat": lat,
                "lon": lng,
                "appid": OPENWEATHER_KEY,
                "units": "metric",
                "lang": "de",
            },
            timeout=5
        ).json()

        temp = res["main"]["temp"]
        wetter_code = res["weather"][0]["id"]
        wetter_beschreibung = res["weather"][0]["description"]
        
        # Verkehrsauswirkungen basierend auf Wetterbedingungen
        verkehr_einfluss = berechne_wetter_verkehrs_einfluss(wetter_code, temp)
        
        return {
            "temperatur": round(temp),
            "beschreibung": wetter_beschreibung,
            "verkehr_einfluss": verkehr_einfluss,
            "formatted": f"{temp:.0f}°C, {wetter_beschreibung}"
        }
        
    except Exception as e:
        print(f"Wetter API Fehler: {e}")
        return {
            "temperatur": None,
            "beschreibung": "Wetter nicht verfügbar",
            "verkehr_einfluss": 0,
            "formatted": "Wetter nicht verfügbar"
        }


def berechne_wetter_verkehrs_einfluss(wetter_code, temperatur):
    """
    Berechnet den Einfluss des Wetters auf den Verkehr.
    """
    base_faktor = 1.0
    
    # Wettercodes: https://openweathermap.org/weather-conditions
    if 200 <= wetter_code <= 299:  # Gewitter
        base_faktor = 1.4
    elif 300 <= wetter_code <= 399:  # Nieselregen
        base_faktor = 1.2
    elif 500 <= wetter_code <= 599:  # Regen
        if wetter_code >= 520:  # Starkregen
            base_faktor = 1.5
        else:  # Leichter Regen
            base_faktor = 1.3
    elif 600 <= wetter_code <= 699:  # Schnee
        base_faktor = 1.6
    elif 700 <= wetter_code <= 799:  # Nebel/Dunst
        base_faktor = 1.3
    elif wetter_code == 800:  # Klarer Himmel
        base_faktor = 0.9
    elif 801 <= wetter_code <= 804:  # Bewölkt
        base_faktor = 1.0
    
    # Temperatur-Einfluss
    if temperatur < -5:  # Sehr kalt
        base_faktor *= 1.2
    elif temperatur > 30:  # Sehr heiß
        base_faktor *= 1.1
    
    return round(base_faktor, 2)


def generiere_intelligenten_verkehrskommentar(verkehr_score, verzoegerung_min, wetter_data, tageszeit):
    """
    Generiert intelligente Verkehrskommentare unter Berücksichtigung aller Faktoren.
    """
    try:
        if isinstance(tageszeit, str):
            # Falls tageszeit als String kommt, aktuelle Zeit verwenden
            tageszeit = datetime.now()
        elif tageszeit is None:
            tageszeit = datetime.now()
            
        hour = tageszeit.hour if isinstance(tageszeit, datetime) else tageszeit
        
        # Kontext aufbauen
        zeit_kontext = ""
        if 7 <= hour <= 9:
            zeit_kontext = "zur Hauptverkehrszeit am Morgen"
        elif 17 <= hour <= 19:
            zeit_kontext = "im Feierabendverkehr"
        elif 12 <= hour <= 14:
            zeit_kontext = "zur Mittagszeit"
        elif 22 <= hour or hour <= 6:
            zeit_kontext = "zur verkehrsarmen Nachtzeit"
        else:
            zeit_kontext = "zur aktuellen Zeit"
            
        wetter_einfluss = ""
        if wetter_data and wetter_data.get("verkehr_einfluss", 1) > 1.2:
            wetter_einfluss = f" Das {wetter_data.get('beschreibung', 'Wetter')} kann zusätzliche Verzögerungen verursachen."
        elif wetter_data and wetter_data.get("verkehr_einfluss", 1) < 0.95:
            wetter_einfluss = f" Bei dem schönen Wetter sind die Straßen entspannt."
        
        # GPT-Prompt für natürlichere Kommentare
        prompt = (
            f"Erstelle einen kurzen, freundlichen Verkehrskommentar (max. 2 Sätze) für eine Routenplanung. "
            f"Verkehrsbewertung: {verkehr_score}/5, Verzögerung: {verzoegerung_min} Minuten, "
            f"Zeit: {zeit_kontext}, Wetter: {wetter_data.get('beschreibung', 'unbekannt') if wetter_data else 'unbekannt'}. "
            f"Sei spezifisch und hilfreich. Auf Deutsch, kein Gendern."
        )

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=100,
        )

        kommentar = response.choices[0].message.content.strip()
        return kommentar + wetter_einfluss
        
    except Exception as e:
        print(f"GPT Kommentar Fehler: {e}")
        # Fallback zu statischen Kommentaren
        return generiere_realistischen_verkehrskommentar(verkehr_score, 0, verzoegerung_min or 0, tageszeit)


def geocode_adresse(adresse):
    """
    Konvertiert eine Adresse in Koordinaten mit Google Geocoding API.
    """
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": adresse,
        "key": GOOGLE_KEY,
        "language": "de",
        "region": "DE"
    }
    
    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        if data["status"] == "OK" and data["results"]:
            location = data["results"][0]["geometry"]["location"]
            return {
                "lat": location["lat"],
                "lng": location["lng"],
                "formatted_address": data["results"][0]["formatted_address"]
            }
        return None
    except Exception as e:
        print(f"Geocoding Fehler: {e}")
        return None


# Legacy-Funktionen für Rückwärtskompatibilität
def berechne_gesamtzeit_mit_transit_und_walk(start_adresse, parkplatz, stadion):
    """
    Legacy-Funktion für Rückwärtskompatibilität.
    Leitet an die neue Funktion weiter.
    """
    print("WARNUNG: berechne_gesamtzeit_mit_transit_und_walk ist veraltet. Verwenden Sie berechne_gesamtzeit_mit_realistischer_bewertung")
    return berechne_gesamtzeit_mit_realistischer_bewertung(start_adresse, parkplatz, stadion)


def format_dauer(minuten):
    """Zeitformatierung."""
    if not minuten:
        return "—"
    h = minuten // 60
    m = minuten % 60
    if h > 0:
        return f"{h}h {m}min"
    return f"{m}min"


def hole_wetter(lat, lng):
    """
    Legacy-Funktion für einfaches Wetter ohne Verkehrseinfluss.
    """
    wetter_data = hole_wetter_mit_verkehrseinfluss(lat, lng)
    return wetter_data.get("formatted", "Wetter nicht verfügbar")


def generiere_gpt_verkehrstext(dauer_min, dauer_normal_min, wetter, ort):
    """
    Legacy-Funktion für GPT-Verkehrskommentare.
    """
    try:
        abweichung = max(0, dauer_min - dauer_normal_min)
        
        # Konvertiere zu neuer Struktur
        wetter_data = {"beschreibung": wetter} if wetter else None
        
        return generiere_intelligenten_verkehrskommentar(
            verkehr_score=3,  # Default-Wert
            verzoegerung_min=abweichung,
            wetter_data=wetter_data,
            tageszeit=datetime.now()
        )
        
    except Exception as e:
        print(f"Legacy GPT Fehler: {e}")
        if dauer_min > dauer_normal_min:
            return f"Aktuell {format_dauer(dauer_min)} statt normal {format_dauer(dauer_normal_min)}. Plane etwas mehr Zeit ein!"
        return f"Gute Fahrt! Normale Reisezeit von {format_dauer(dauer_normal_min)} erwartet."