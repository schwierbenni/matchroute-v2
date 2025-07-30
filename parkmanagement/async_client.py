# parkmanagement/async_client.py

import asyncio
import aiohttp
import logging
from typing import List, Dict, Any, Optional, Tuple
from django.conf import settings
from concurrent.futures import ThreadPoolExecutor
import time

logger = logging.getLogger(__name__)

class AsyncGoogleMapsClient:
    """
    Hochperformanter asynchroner Google Maps API Client
    Für Parallelisierung von API-Calls zur drastischen Performance-Verbesserung
    """
    
    def __init__(self):
        self.api_key = settings.GOOGLE_MAPS_API_KEY
        self.base_url = "https://maps.googleapis.com/maps/api"
        self.session = None
        
    async def __aenter__(self):
        """Async Context Manager - Session öffnen"""
        connector = aiohttp.TCPConnector(
            limit=30,  # Max 30 gleichzeitige Verbindungen
            limit_per_host=15,  # Max 15 pro Host
            ttl_dns_cache=300,  # DNS Cache 5 Minuten
            use_dns_cache=True,
        )
        
        timeout = aiohttp.ClientTimeout(
            total=30,  # Gesamt-Timeout
            connect=10,  # Verbindungs-Timeout
            sock_read=15  # Read-Timeout
        )
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': 'MatchRoute-Thesis-Performance-Optimization/1.0'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Session schließen"""
        if self.session:
            await self.session.close()
    
    async def calculate_directions_batch(self, requests: List[Dict[str, Any]]) -> List[Optional[Dict[str, Any]]]:
        """
        🚀 KERN-OPTIMIERUNG: Parallel API-Requests für alle Routen
        
        Args:
            requests: Liste von Route-Requests
        Returns:
            Liste von Route-Ergebnissen in gleicher Reihenfolge
        """
        if not requests:
            return []
        
        logger.info(f"🔄 Starte {len(requests)} parallele Google Directions Requests")
        start_time = time.time()
        
        # Alle Requests parallel ausführen
        tasks = []
        for i, request in enumerate(requests):
            task = asyncio.create_task(
                self._single_directions_request(request, request_id=i)
            )
            tasks.append(task)
        
        # Auf alle Ergebnisse warten
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Exceptions handhaben
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"❌ Request {i} fehlgeschlagen: {result}")
                processed_results.append(None)
            else:
                processed_results.append(result)
        
        duration = time.time() - start_time
        success_count = sum(1 for r in processed_results if r is not None)
        
        logger.info(f"✅ Parallel Requests abgeschlossen: {success_count}/{len(requests)} erfolgreich in {duration:.2f}s")
        
        return processed_results
    
    async def _single_directions_request(self, request_data: Dict[str, Any], request_id: int = 0) -> Optional[Dict[str, Any]]:
        """
        Einzelner Google Directions API Request
        """
        url = f"{self.base_url}/directions/json"
        
        params = {
            "origin": request_data["origin"],
            "destination": request_data["destination"], 
            "mode": request_data.get("mode", "driving"),
            "key": self.api_key,
            "language": "de",
            "region": "DE"
        }
        
        # Mode-spezifische Parameter
        if params["mode"] == "driving":
            params.update({
                "departure_time": request_data.get("departure_time", "now"),
                "traffic_model": "best_guess",
                "avoid": "tolls"
            })
        elif params["mode"] == "transit":
            params.update({
                "departure_time": request_data.get("departure_time", "now"),
                "transit_mode": "bus|subway|train|tram",
                "transit_routing_preference": "fewer_transfers"
            })
        
        try:
            async with self.session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()
                
                if data["status"] == "OK" and data["routes"]:
                    route = data["routes"][0]
                    leg = route["legs"][0]
                    
                    result = {
                        "request_id": request_id,
                        "dauer_sekunden": leg["duration"]["value"],
                        "dauer_minuten": leg["duration"]["value"] // 60,
                        "distanz_meter": leg["distance"]["value"],
                        "distanz_km": round(leg["distance"]["value"] / 1000, 1),
                        "polyline": route["overview_polyline"]["points"],
                        "start_adresse": leg["start_address"],
                        "end_adresse": leg["end_address"],
                        "status": "success",
                        "mode": params["mode"]
                    }
                    
                    # Verkehrsdaten für Driving Mode
                    if params["mode"] == "driving" and "duration_in_traffic" in leg:
                        result["dauer_traffic_sekunden"] = leg["duration_in_traffic"]["value"]
                        result["dauer_traffic_minuten"] = leg["duration_in_traffic"]["value"] // 60
                    
                    logger.debug(f"✅ Request {request_id} ({params['mode']}): {result['dauer_minuten']}min")
                    return result
                    
                else:
                    logger.warning(f"⚠️ Request {request_id}: Google API Status: {data.get('status', 'UNKNOWN')}")
                    return None
                    
        except asyncio.TimeoutError:
            logger.error(f"⏰ Request {request_id}: Timeout bei Google Directions API")
            return None
        except aiohttp.ClientError as e:
            logger.error(f"🌐 Request {request_id}: HTTP Fehler: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Request {request_id}: Unerwarteter Fehler: {e}")
            return None


class ParallelRouteCalculator:
    """
    Hochperformante Routenberechnung mit Parallelisierung
    """
    
    @staticmethod
    async def calculate_all_parking_routes(start_adresse: str, parkplaetze: List, stadion) -> List[Dict[str, Any]]:
        """
        🎯 HAUPTFUNKTION: Alle Parkplatz-Routen parallel berechnen
        
        Reduziert 21 serielle API-Calls auf 3 parallele Batches:
        - Batch 1: Alle Auto-Routen (Start → Parkplätze)
        - Batch 2: Alle Transit-Routen (Parkplätze → Stadion)  
        - Batch 3: Alle Walking-Routen (Parkplätze → Stadion)
        """
        
        if not parkplaetze:
            return []
        
        logger.info(f"🚀 Starte parallele Berechnung für {len(parkplaetze)} Parkplätze")
        
        async with AsyncGoogleMapsClient() as client:
            
            # 1. BATCH 1: Alle Auto-Routen parallel (Start → Parkplätze)
            driving_requests = []
            for i, parkplatz in enumerate(parkplaetze):
                driving_requests.append({
                    "origin": start_adresse,
                    "destination": f"{parkplatz.latitude},{parkplatz.longitude}",
                    "mode": "driving",
                    "departure_time": "now",
                    "parking_index": i,
                    "parking_id": parkplatz.id,
                    "parking_name": parkplatz.name
                })
            
            logger.info(f"📡 Batch 1: {len(driving_requests)} Auto-Routen parallel")
            driving_results = await client.calculate_directions_batch(driving_requests)
            
            # 2. BATCH 2: Alle Transit-Routen parallel (Parkplätze → Stadion)
            transit_requests = []
            for i, parkplatz in enumerate(parkplaetze):
                transit_requests.append({
                    "origin": f"{parkplatz.latitude},{parkplatz.longitude}",
                    "destination": f"{stadion.latitude},{stadion.longitude}",
                    "mode": "transit",
                    "departure_time": "now",
                    "parking_index": i,
                    "parking_id": parkplatz.id,
                    "parking_name": parkplatz.name
                })
            
            logger.info(f"🚌 Batch 2: {len(transit_requests)} Transit-Routen parallel")
            transit_results = await client.calculate_directions_batch(transit_requests)
            
            # 3. BATCH 3: Alle Walking-Routen parallel (Parkplätze → Stadion)
            walking_requests = []
            for i, parkplatz in enumerate(parkplaetze):
                walking_requests.append({
                    "origin": f"{parkplatz.latitude},{parkplatz.longitude}",
                    "destination": f"{stadion.latitude},{stadion.longitude}",
                    "mode": "walking",
                    "parking_index": i,
                    "parking_id": parkplatz.id,
                    "parking_name": parkplatz.name
                })
            
            logger.info(f"🚶 Batch 3: {len(walking_requests)} Walking-Routen parallel")
            walking_results = await client.calculate_directions_batch(walking_requests)
        
        # 4. ERGEBNISSE KOMBINIEREN
        combined_results = []
        
        for i, parkplatz in enumerate(parkplaetze):
            driving_result = driving_results[i] if i < len(driving_results) else None
            transit_result = transit_results[i] if i < len(transit_results) else None
            walking_result = walking_results[i] if i < len(walking_results) else None
            
            if not driving_result:
                logger.warning(f"⚠️ Keine Auto-Route für {parkplatz.name} - überspringe")
                continue
            
            # Beste Weiterreise-Option ermitteln
            weiterreise_optionen = []
            if transit_result:
                weiterreise_optionen.append(("transit", transit_result["dauer_minuten"]))
            if walking_result:
                weiterreise_optionen.append(("walking", walking_result["dauer_minuten"]))
            
            if not weiterreise_optionen:
                logger.warning(f"⚠️ Keine Weiterreise-Option für {parkplatz.name}")
                continue
            
            beste_methode, beste_zeit = min(weiterreise_optionen, key=lambda x: x[1])
            
            # Verkehrsbewertung berechnen
            from .utils import berechne_realistische_verkehrsbewertung, generiere_google_maps_navigation_link
            from datetime import datetime
            
            normal_sekunden = driving_result["dauer_sekunden"]
            traffic_sekunden = driving_result.get("dauer_traffic_sekunden", normal_sekunden)
            
            bewertung, kommentar = berechne_realistische_verkehrsbewertung(
                normal_sekunden, traffic_sekunden, datetime.now()
            )
            
            # Navigation Links
            nav_links = generiere_google_maps_navigation_link(
                start_adresse,
                parkplatz.latitude,
                parkplatz.longitude,
                stadion.latitude,
                stadion.longitude
            )
            
            # Walking Navigation (falls Walking beste Option)
            walking_nav = None
            if beste_methode == "walking" and walking_result:
                walking_nav = generiere_google_maps_navigation_link(
                    f"{parkplatz.latitude},{parkplatz.longitude}",
                    stadion.latitude,
                    stadion.longitude
                )
            
            # Vollständiges Ergebnis
            route_result = {
                "parkplatz": {
                    "id": parkplatz.id,
                    "name": parkplatz.name,
                    "latitude": float(parkplatz.latitude),
                    "longitude": float(parkplatz.longitude),
                },
                "dauer_auto": driving_result["dauer_minuten"],
                "dauer_traffic": driving_result.get("dauer_traffic_minuten", driving_result["dauer_minuten"]),
                "distanz_km": driving_result["distanz_km"],
                "polyline_auto": driving_result["polyline"],
                "verkehr_bewertung": bewertung,
                "verkehr_kommentar": kommentar,
                "navigation_links": nav_links,
                
                # Transit/Walking Daten
                "dauer_transit": transit_result["dauer_minuten"] if transit_result else None,
                "polyline_transit": transit_result["polyline"] if transit_result else None,
                "dauer_walking": walking_result["dauer_minuten"] if walking_result else None,
                "polyline_walking": walking_result["polyline"] if walking_result else None,
                "walking_navigation": walking_nav,
                
                # Beste Option
                "beste_methode": beste_methode,
                "gesamtzeit": driving_result.get("dauer_traffic_minuten", driving_result["dauer_minuten"]) + beste_zeit,
                
                # Placeholder für Live-Daten (wird später ergänzt)
                "has_live_data": False,
                "live_parking_data": None
            }
            
            combined_results.append(route_result)
        
        logger.info(f"✅ Parallele Berechnung abgeschlossen: {len(combined_results)} Routen erfolgreich")
        return combined_results


# Wrapper-Funktion für Django (sync → async)
def run_parallel_route_calculation(start_adresse: str, parkplaetze: List, stadion) -> List[Dict[str, Any]]:
    """
    Synchroner Wrapper für die asynchrone Routenberechnung
    Kann direkt in Django Views verwendet werden
    """
    try:
        # Event Loop in Thread ausführen (Django-kompatibel)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                ParallelRouteCalculator.calculate_all_parking_routes(start_adresse, parkplaetze, stadion)
            )
            return result
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"❌ Fehler bei paralleler Routenberechnung: {e}")
        # Fallback zur sequenziellen Berechnung
        from .utils import berechne_optimierte_parkplatz_empfehlung
        logger.info("⚠️ Fallback zu sequenzieller Berechnung")
        return berechne_optimierte_parkplatz_empfehlung(start_adresse, parkplaetze, stadion)