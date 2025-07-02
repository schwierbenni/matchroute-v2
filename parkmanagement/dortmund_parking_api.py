import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
from django.conf import settings
from django.core.cache import cache
import math

logger = logging.getLogger(__name__)

# Cache-Konfiguration
CACHE_TIMEOUT = 300  # 5 Minuten Cache für Live-Daten
DORTMUND_API_URL = "https://open-data.dortmund.de/api/explore/v2.1/catalog/datasets/parkhauser/records"

class DortmundParkingData:
    """
    Handler für Dortmund Open Data Parkplatz-API
    Stellt Live-Verfügbarkeitsdaten für Parkplätze bereit
    """
    
    @staticmethod
    def fetch_live_parking_data() -> Optional[List[Dict[str, Any]]]:
        """
        Holt aktuelle Parkplatzdaten von der Dortmund Open Data API.
        
        Returns:
            List[Dict]: Live-Parkplatzdaten oder None bei Fehler
        """
        cache_key = "dortmund_parking_live_data"
        
        # Prüfe Cache zuerst
        cached_data = cache.get(cache_key)
        if cached_data:
            logger.info("📦 Dortmund Parkdaten aus Cache geladen")
            return cached_data
        
        try:
            logger.info("🔄 Lade Live-Parkdaten von Dortmund Open Data API...")
            
            response = requests.get(
                DORTMUND_API_URL,
                params={
                    "limit": 100,  # Alle verfügbaren Parkplätze
                    "timezone": "Europe/Berlin"
                },
                timeout=10,
                headers={
                    'User-Agent': 'MatchRoute-Research-App/1.0'
                }
            )
            
            response.raise_for_status()
            api_data = response.json()
            
            if "results" not in api_data:
                logger.error("❌ Unerwartete API-Struktur von Dortmund Open Data")
                return None
            
            # Daten verarbeiten und normalisieren
            parking_data = []
            for item in api_data["results"]:
                processed_item = DortmundParkingData._process_parking_item(item)
                if processed_item:
                    parking_data.append(processed_item)
            
            # In Cache speichern
            cache.set(cache_key, parking_data, CACHE_TIMEOUT)
            
            logger.info(f"✅ {len(parking_data)} Dortmund Parkplätze erfolgreich geladen")
            return parking_data
            
        except requests.exceptions.Timeout:
            logger.warning("⏰ Timeout bei Dortmund Parking API - verwende Fallback")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"🌐 Netzwerkfehler bei Dortmund API: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Unerwarteter Fehler bei Dortmund API: {e}")
            return None
    
    @staticmethod
    def _process_parking_item(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Verarbeitet ein einzelnes Parkplatz-Item von der API.
        
        Args:
            item: Rohdaten von der API
            
        Returns:
            Dict: Verarbeitete Parkplatz-Daten
        """
        try:
            # Koordinaten extrahieren
            geo_point = item.get("geo_point_2d", {})
            if not geo_point:
                return None
                
            lat = geo_point.get("lat")
            lng = geo_point.get("lon") 
            
            if not lat or not lng:
                return None
            
            # Zeitstempel verarbeiten
            zeitstempel_raw = item.get("zeitstempel")
            zeitstempel_status = item.get("zeitstempel_status", "Unbekannt")
            last_update = None
            
            if zeitstempel_raw:
                try:
                    last_update = datetime.fromisoformat(zeitstempel_raw.replace("Z", "+00:00"))
                except ValueError:
                    pass
            
            # Verfügbarkeitsdaten
            frei = item.get("frei", 0)
            capacity = item.get("capacity", 0)
            
            # Belegungsrate berechnen
            occupancy_rate = 0
            if capacity > 0:
                occupancy_rate = round(((capacity - frei) / capacity) * 100, 1)
            
            # Verfügbarkeits-Score (1-5)
            availability_score = DortmundParkingData._calculate_availability_score(frei, capacity, occupancy_rate)
            
            # Status-Text generieren
            occupancy_text = DortmundParkingData._generate_occupancy_text(availability_score, frei, occupancy_rate)
            
            # CSS-Klassen für Frontend
            css_class = DortmundParkingData._get_occupancy_css_class(availability_score)
            
            # Datenqualität bewerten
            freshness = DortmundParkingData._assess_data_freshness(last_update, zeitstempel_status)
            
            return {
                "api_id": item.get("id"),
                "name": item.get("name", "Unbekannt"),
                "type": item.get("type", "Parkhaus"),
                "latitude": float(lat),
                "longitude": float(lng),
                "frei": frei,
                "capacity": capacity,
                "occupancy": {
                    "occupancy_rate": occupancy_rate,
                    "availability_score": availability_score,
                    "occupancy_text": occupancy_text,
                    "css_class": css_class
                },
                "last_update": last_update.isoformat() if last_update else None,
                "freshness": freshness,
                "parkeinrichtung": item.get("parkeinrichtung", "unbekannt"),
                "opening_hours": DortmundParkingData._extract_opening_hours(item),
                "raw_stand": item.get("stand", "")
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Fehler beim Verarbeiten von Parkplatz-Item: {e}")
            return None
    
    @staticmethod
    def _calculate_availability_score(frei: int, capacity: int, occupancy_rate: float) -> int:
        """
        Berechnet einen Verfügbarkeits-Score von 1-5.
        
        Args:
            frei: Freie Plätze
            capacity: Gesamtkapazität
            occupancy_rate: Belegungsrate in Prozent
            
        Returns:
            int: Score von 1 (schlecht) bis 5 (excellent)
        """
        if capacity == 0:
            return 1
            
        if occupancy_rate <= 30:  # <= 30% belegt
            return 5  # Excellent
        elif occupancy_rate <= 60:  # 30-60% belegt
            return 4  # Good
        elif occupancy_rate <= 85:  # 60-85% belegt
            return 3  # Fair
        elif occupancy_rate <= 95:  # 85-95% belegt
            return 2  # Poor
        else:  # > 95% belegt
            return 1  # Critical
    
    @staticmethod
    def _generate_occupancy_text(score: int, frei: int, occupancy_rate: float) -> str:
        """Generiert benutzerfreundlichen Status-Text."""
        if score == 5:
            return f"Viele Plätze frei ({frei} verfügbar)"
        elif score == 4:
            return f"Gute Verfügbarkeit ({frei} frei)"
        elif score == 3:
            return f"Moderate Belegung ({frei} frei)"
        elif score == 2:
            return f"Wenige Plätze frei ({frei} verfügbar)"
        else:
            return f"Nahezu voll ({frei} Plätze)"
    
    @staticmethod
    def _get_occupancy_css_class(score: int) -> str:
        """Gibt CSS-Klassen für Frontend-Styling zurück."""
        css_classes = {
            5: "bg-green-100 text-green-800 border-green-300",
            4: "bg-blue-100 text-blue-800 border-blue-300", 
            3: "bg-yellow-100 text-yellow-800 border-yellow-300",
            2: "bg-orange-100 text-orange-800 border-orange-300",
            1: "bg-red-100 text-red-800 border-red-300"
        }
        return css_classes.get(score, "bg-gray-100 text-gray-800 border-gray-300")
    
    @staticmethod
    def _assess_data_freshness(last_update: Optional[datetime], status_text: str) -> Dict[str, Any]:
        """
        Bewertet die Aktualität der Daten.
        
        Returns:
            Dict mit freshness-Informationen
        """
        if not last_update:
            return {
                "status": "Unbekannte Aktualität",
                "css_class": "bg-gray-100 text-gray-600",
                "age_minutes": None
            }
        
        now = datetime.now(last_update.tzinfo) if last_update.tzinfo else datetime.now()
        age = now - last_update
        age_minutes = int(age.total_seconds() / 60)
        
        if age_minutes <= 5:
            return {
                "status": "Live-Daten",
                "css_class": "bg-green-100 text-green-700",
                "age_minutes": age_minutes
            }
        elif age_minutes <= 10:
            return {
                "status": "Aktuelle Daten",
                "css_class": "bg-blue-100 text-blue-700", 
                "age_minutes": age_minutes
            }
        elif age_minutes <= 30:
            return {
                "status": "Mäßig aktuell",
                "css_class": "bg-yellow-100 text-yellow-700",
                "age_minutes": age_minutes
            }
        else:
            return {
                "status": "Veraltete Daten",
                "css_class": "bg-red-100 text-red-700",
                "age_minutes": age_minutes
            }
    
    @staticmethod
    def _extract_opening_hours(item: Dict[str, Any]) -> Dict[str, str]:
        """Extrahiert Öffnungszeiten aus API-Daten."""
        days = ["montag", "dienstag", "mittwoch", "donnerstag", "freitag", "samstag", "sonntag"]
        opening_hours = {}
        
        for day in days:
            hours = item.get(day, "-")
            if hours and hours != "-":
                opening_hours[day] = hours
                
        return opening_hours
    
    @staticmethod
    def find_matching_live_data(db_parkplatz, live_data_list: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Findet passende Live-Daten für einen Datenbank-Parkplatz.
        
        Args:
            db_parkplatz: Parkplatz-Objekt aus der Datenbank
            live_data_list: Liste der Live-Daten von der API
            
        Returns:
            Dict: Passende Live-Daten oder None
        """
        if not live_data_list:
            return None
        
        db_lat = float(db_parkplatz.latitude)
        db_lng = float(db_parkplatz.longitude)
        
        best_match = None
        min_distance = float('inf')
        
        for live_item in live_data_list:
            # 1. Versuch: Name-Match (teilweise)
            live_name = live_item.get("name", "").lower()
            db_name = db_parkplatz.name.lower()
            
            # Einfache Namens-Ähnlichkeit
            if any(word in live_name for word in db_name.split() if len(word) > 3):
                logger.info(f"🎯 Name-Match gefunden: '{db_name}' ↔ '{live_name}'")
                return live_item
            
            # 2. Versuch: Distanz-basierter Match
            live_lat = live_item.get("latitude")
            live_lng = live_item.get("longitude")
            
            if live_lat and live_lng:
                distance = DortmundParkingData._calculate_distance(db_lat, db_lng, live_lat, live_lng)
                
                # Wenn sehr nah (< 200m), als Match betrachten
                if distance < 0.2 and distance < min_distance:
                    min_distance = distance
                    best_match = live_item
        
        if best_match:
            logger.info(f"📍 Distanz-Match gefunden: {min_distance:.0f}m für '{db_parkplatz.name}'")
            
        return best_match
    
    @staticmethod
    def _calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """
        Berechnet die Distanz zwischen zwei Koordinaten in Kilometern.
        
        Returns:
            float: Distanz in Kilometern
        """
        # Haversine-Formel für kurze Distanzen
        R = 6371  # Erdradius in km
        
        dlat = math.radians(lat2 - lat1)
        dlng = math.radians(lng2 - lng1)
        
        a = (math.sin(dlat/2) ** 2 + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
             math.sin(dlng/2) ** 2)
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c
        
        return distance


def enrich_parkplatz_with_live_data(parkplatz_vorschlag: Dict[str, Any], live_data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Reichert einen Parkplatz-Vorschlag mit Live-Daten an.
    
    Args:
        parkplatz_vorschlag: Bestehender Parkplatz-Vorschlag
        live_data_list: Liste der Live-Daten
        
    Returns:
        Dict: Angereicherter Parkplatz-Vorschlag
    """
    # Mock-Parkplatz-Objekt aus Vorschlag erstellen
    class MockParkplatz:
        def __init__(self, data):
            self.name = data["name"]
            self.latitude = data["latitude"]
            self.longitude = data["longitude"]
    
    mock_parkplatz = MockParkplatz(parkplatz_vorschlag["parkplatz"])
    
    # Live-Daten suchen
    live_data = DortmundParkingData.find_matching_live_data(mock_parkplatz, live_data_list)
    
    if live_data:
        logger.info(f"✅ Live-Daten für '{mock_parkplatz.name}' gefunden")
        parkplatz_vorschlag["has_live_data"] = True
        parkplatz_vorschlag["live_parking_data"] = live_data
    else:
        logger.info(f"ℹ️ Keine Live-Daten für '{mock_parkplatz.name}' verfügbar")
        parkplatz_vorschlag["has_live_data"] = False
        parkplatz_vorschlag["live_parking_data"] = None
    
    return parkplatz_vorschlag


def get_dortmund_parking_overview() -> Dict[str, Any]:
    """
    Liefert eine Übersicht aller Dortmund Parkplätze für Dashboard/Debugging.
    
    Returns:
        Dict: Übersicht der verfügbaren Parkplätze
    """
    live_data = DortmundParkingData.fetch_live_parking_data()
    
    if not live_data:
        return {
            "status": "error",
            "message": "Keine Live-Daten verfügbar",
            "parkplaetze": []
        }
    
    # Statistiken berechnen
    total_capacity = sum(item.get("capacity", 0) for item in live_data)
    total_free = sum(item.get("frei", 0) for item in live_data)
    avg_occupancy = round(((total_capacity - total_free) / total_capacity * 100), 1) if total_capacity > 0 else 0
    
    return {
        "status": "success",
        "last_updated": datetime.now().isoformat(),
        "statistics": {
            "total_locations": len(live_data),
            "total_capacity": total_capacity,
            "total_free": total_free,
            "avg_occupancy_rate": avg_occupancy
        },
        "parkplaetze": live_data
    }