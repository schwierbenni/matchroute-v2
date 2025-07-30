from datetime import datetime
from typing import Any, Dict, List
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework import viewsets, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth.models import User
from django.conf import settings
from django.db import models
import requests
import logging

from parkmanagement.utils import (
    berechne_gesamtzeit_mit_realistischer_bewertung, 
    berechne_optimierte_parkplatz_empfehlung_mit_live_daten, 
    generiere_intelligenten_verkehrskommentar,
    hole_wetter_mit_verkehrseinfluss,
    berechne_google_route,
    geocode_adresse,
)

from .performance_monitor import performance_monitor, get_research_export


# Import der Dortmund Live-Daten Integration
try:
    from parkmanagement.dortmund_parking_api import (
        get_dortmund_parking_overview,
        DortmundParkingData
    )
    DORTMUND_INTEGRATION_AVAILABLE = True
except ImportError:
    DORTMUND_INTEGRATION_AVAILABLE = False

from .models import Parkplatz, Route, Stadion, Verein
from .serializers import (
    ParkplatzSerializer,
    RouteSerializer,
    StadionSerializer,
    UserRegisterSerializer,
    VereinSerializer,
)

logger = logging.getLogger(__name__)


class ParkplatzViewSet(viewsets.ModelViewSet):
    queryset = Parkplatz.objects.all()
    serializer_class = ParkplatzSerializer
    # permission_classes = [IsAuthenticated]


class UserRegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer


class VereinViewSet(viewsets.ModelViewSet):
    queryset = Verein.objects.all()
    serializer_class = VereinSerializer


class StadionViewSet(viewsets.ModelViewSet):
    queryset = Stadion.objects.all()
    serializer_class = StadionSerializer


class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return self.queryset.filter(benutzer=user).order_by("-erstelldatum")


class RouteSuggestionView(APIView):
    """
    Diese View wurde für wissenschaftliche Anwendungsfälle erweitert und 
    integriert Echtzeit-Parkplatzdaten von Dortmund Open Data.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        start_adresse = request.data.get("start_adresse")
        user = request.user

        try:
            stadion = user.profil.lieblingsverein.stadien.first()
        except AttributeError:
            return Response(
                {"detail": "Kein Lieblingsverein oder Stadion gefunden."}, 
                status=400
            )

        parkplaetze = stadion.parkplaetze.all()
        
        if not parkplaetze.exists():
            return Response(
                {"detail": "Keine Parkplätze für das Stadion gefunden."}, 
                status=400
            )

        logger.info(f"Starte Routenberechnung für {user.username} - {len(parkplaetze)} Parkplätze")

        vorschlaege = berechne_optimierte_parkplatz_empfehlung_mit_live_daten(
            start_adresse, parkplaetze, stadion
        )

        if not vorschlaege:
            return Response(
                {"detail": "Keine Route gefunden. Bitte überprüfen Sie Ihre Startadresse."}, 
                status=400
            )

        # Erweiterte Metadaten für wissenschaftliche Auswertung
        live_data_count = sum(1 for v in vorschlaege if v.get("has_live_data"))
        
        # Wetter für GPT-Kommentar beim besten Vorschlag
        bester = vorschlaege[0]
        
        try:
            wetter_data = hole_wetter_mit_verkehrseinfluss(
                stadion.latitude, stadion.longitude
            )
            
            # Intelligenten Kommentar generieren
            enhanced_kommentar = generiere_intelligenten_verkehrskommentar(
                verkehr_score=bester.get("verkehr_bewertung", 3),
                verzoegerung_min=bester.get("dauer_traffic", 0) - bester.get("dauer_auto", 0),
                wetter_data=wetter_data,
                tageszeit=request.META.get('HTTP_DATE')  # Optional: Zeit aus Request
            )
            
            bester["verkehr_kommentar"] = enhanced_kommentar
            bester["wetter_info"] = wetter_data.get("formatted", "")
            
        except Exception as e:
            logger.error(f"Wetter/GPT Fehler: {e}")
            # Fallback bleibt bestehen

        alle_ohne_bester = vorschlaege[1:]

        # Erweiterte Response mit Live-Daten Metadaten
        response_data = {
            "empfohlener_parkplatz": bester, 
            "alle_parkplaetze": alle_ohne_bester,
            "meta": {
                "total_options": len(vorschlaege),
                "live_data_available": live_data_count,
                "live_data_percentage": round((live_data_count / len(vorschlaege)) * 100, 1) if vorschlaege else 0,
                "calculation_time": "live",
                "data_sources": {
                    "routing": "Google Maps API",
                    "traffic": "Google Maps Traffic API",
                    "parking_live_data": "Dortmund Open Data" if DORTMUND_INTEGRATION_AVAILABLE else "Not Available",
                    "weather": "OpenWeatherMap API"
                },
                "research_context": {
                    "integration_active": DORTMUND_INTEGRATION_AVAILABLE,
                    "city": "Dortmund",
                    "user_club": stadion.verein.name if stadion and stadion.verein else None
                }
            }
        }

        logger.info(f" Routenberechnung abgeschlossen: {len(vorschlaege)} Optionen, {live_data_count} mit Live-Daten")

        return Response(response_data, status=200)


class RouteSpeichernView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        data = request.data

        try:
            stadion = Stadion.objects.get(id=data.get("stadion_id"))
            parkplatz = Parkplatz.objects.get(id=data.get("parkplatz_id"))
        except (Stadion.DoesNotExist, Parkplatz.DoesNotExist):
            return Response(
                {"detail": "Stadion oder Parkplatz nicht gefunden."},
                status=400
            )

        try:
            route = Route.objects.create(
                benutzer=user,
                stadion=stadion,
                parkplatz=parkplatz,
                start_adresse=data.get("start_adresse"),
                start_latitude=data.get("start_lat"),
                start_longitude=data.get("start_lng"),
                strecke_km=data.get("distanz_km"),
                dauer_minuten=data.get("dauer_min"),  
                transportmittel=data.get("transportmittel", "auto"),
                route_url=data.get("route_url"),
            )

            return Response(
                {
                    "detail": "Route erfolgreich gespeichert.", 
                    "route_id": route.id,
                    "saved_at": route.erstelldatum.isoformat()
                },
                status=201
            )

        except Exception as e:
            return Response(
                {"detail": f"Fehler beim Speichern der Route: {str(e)}"},
                status=500
            )


class ProfilView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            profil = request.user.profil
            lieblingsverein = profil.lieblingsverein
            stadion = lieblingsverein.stadien.first() if lieblingsverein else None
            
            return Response(
                {
                    "username": request.user.username,
                    "email": request.user.email,
                    "lieblingsverein": VereinSerializer(lieblingsverein).data if lieblingsverein else None,
                    "stadion": StadionSerializer(stadion).data if stadion else None,
                    "member_since": request.user.date_joined.isoformat(),
                    "profile_complete": bool(lieblingsverein and stadion)
                }
            )
        except Exception as e:
            return Response(
                {"detail": f"Fehler beim Laden des Profils: {str(e)}"},
                status=500
            )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def google_route_details(request):
    """
    Ersatz für GraphHopper - detaillierte Routeninformationen über Google Directions API.
    Bietet erweiterte Funktionalität wie turn-by-turn Navigation.
    """
    start = request.query_params.get("start")
    ziel = request.query_params.get("ziel")
    mode = request.query_params.get("mode", "walking")  # walking, driving, transit, bicycling

    if not start or not ziel:
        return Response(
            {"detail": "Start und Ziel müssen angegeben werden."}, 
            status=400
        )

    # Google Directions API für detaillierte Wegbeschreibungen
    url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": start,
        "destination": ziel,
        "mode": mode,
        "language": "de",
        "region": "DE",
        "key": settings.GOOGLE_MAPS_API_KEY,
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data["status"] != "OK":
            return Response(
                {"detail": f"Google Directions Fehler: {data.get('status', 'Unbekannt')}"}, 
                status=400
            )

        route = data["routes"][0]
        leg = route["legs"][0]
        
        # Detaillierte Schritte extrahieren
        steps = []
        for step in leg["steps"]:
            steps.append({
                "instruction": step["html_instructions"],
                "distance": step["distance"]["text"],
                "duration": step["duration"]["text"],
                "travel_mode": step.get("travel_mode", mode.upper())
            })

        result = {
            "status": "OK",
            "route_summary": {
                "total_distance": leg["distance"]["text"],
                "total_duration": leg["duration"]["text"],
                "start_address": leg["start_address"],
                "end_address": leg["end_address"]
            },
            "steps": steps,
            "polyline": route["overview_polyline"]["points"],
            "navigation_url": f"https://www.google.com/maps/dir/{start}/{ziel}"
        }

        return Response(result)

    except requests.exceptions.Timeout:
        return Response(
            {"detail": "Zeitüberschreitung bei Google Directions API"}, 
            status=504
        )
    except requests.RequestException as e:
        return Response(
            {"detail": f"Fehler bei der Anfrage an Google Directions: {str(e)}"}, 
            status=500
        )
    except Exception as e:
        return Response(
            {"detail": f"Unerwarteter Fehler: {str(e)}"}, 
            status=500
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def geocode_address(request):
    """
    Neue Funktion für Frontend: Adressvalidierung und Geocoding.
    """
    adresse = request.data.get("adresse")
    if not adresse:
        return Response(
            {"detail": "Adresse erforderlich."}, 
            status=400
        )
    
    result = geocode_adresse(adresse)
    if result:
        return Response({
            "status": "success",
            "data": result,
            "message": "Adresse erfolgreich gefunden"
        })
    else:
        return Response(
            {"detail": "Adresse konnte nicht gefunden werden. Bitte überprüfen Sie Ihre Eingabe."}, 
            status=404
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dortmund_parking_overview(request):
    """
    Dortmund Parkplatz-Übersicht für Dashboard und Debugging
    
    Zeigt alle verfügbaren Live-Parkplatzdaten von Dortmund Open Data an.
    Nützlich für wissenschaftliche Auswertungen und Systemmonitoring.
    """
    if not DORTMUND_INTEGRATION_AVAILABLE:
        return Response({
            "status": "error",
            "message": "Dortmund Integration nicht verfügbar",
            "suggestion": "Bitte dortmund_parking_api.py hinzufügen"
        }, status=503)
    
    try:
        overview = get_dortmund_parking_overview()
        return Response(overview)
    except Exception as e:
        logger.error(f"Fehler bei Dortmund Parking Overview: {e}")
        return Response({
            "status": "error", 
            "message": f"Fehler beim Laden der Dortmund Parkdaten: {str(e)}"
        }, status=500)


@api_view(["GET"]) 
@permission_classes([IsAuthenticated])
def live_parking_status(request):
    """
    Live-Status einzelner Parkplätze
    
    Ermöglicht gezielten Abruf von Live-Daten für spezifische Parkplätze.
    """
    if not DORTMUND_INTEGRATION_AVAILABLE:
        return Response({
            "status": "error",
            "message": "Live-Daten Integration nicht verfügbar"
        }, status=503)
    
    try:
        parkplatz_id = request.query_params.get("parkplatz_id")
        
        if parkplatz_id:
            # Spezifischer Parkplatz
            try:
                parkplatz = Parkplatz.objects.get(id=parkplatz_id)
                live_data_list = DortmundParkingData.fetch_live_parking_data()
                
                if live_data_list:
                    matching_data = DortmundParkingData.find_matching_live_data(parkplatz, live_data_list)
                    
                    return Response({
                        "status": "success",
                        "parkplatz": {
                            "id": parkplatz.id,
                            "name": parkplatz.name,
                            "has_live_data": bool(matching_data),
                            "live_data": matching_data
                        }
                    })
                else:
                    return Response({
                        "status": "no_data",
                        "message": "Keine Live-Daten verfügbar"
                    })
                    
            except Parkplatz.DoesNotExist:
                return Response({
                    "status": "error",
                    "message": "Parkplatz nicht gefunden"
                }, status=404)
        else:
            # Alle Parkplätze
            live_data_list = DortmundParkingData.fetch_live_parking_data()
            
            return Response({
                "status": "success",
                "total_live_locations": len(live_data_list) if live_data_list else 0,
                "data_available": bool(live_data_list),
                "locations": live_data_list or []
            })
            
    except Exception as e:
        logger.error(f"Fehler bei Live Parking Status: {e}")
        return Response({
            "status": "error",
            "message": f"Fehler beim Abrufen der Live-Daten: {str(e)}"
        }, status=500)


# Zusätzliche API für Dashboard-Statistiken (erweitert)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """
    Liefert Dashboard-Statistiken für den angemeldeten Benutzer.
    Erweitert um Live-Daten Informationen.
    """
    try:
        user = request.user
        routen = Route.objects.filter(benutzer=user)
        
        # Grundlegende Statistiken
        total_routes = routen.count()
        
        if total_routes > 0:
            avg_duration = routen.aggregate(
                avg_dur=models.Avg('dauer_minuten')
            )['avg_dur'] or 0
            
            # Lieblings-Parkplatz (häufigster)
            favorite_parking = routen.values('parkplatz__name').annotate(
                count=models.Count('parkplatz')
            ).order_by('-count').first()
            
            # Letzte Routen
            recent_routes = RouteSerializer(
                routen.order_by('-erstelldatum')[:5], 
                many=True
            ).data
        else:
            avg_duration = 0
            favorite_parking = None
            recent_routes = []
        
        # Live-Daten Status für Dashboard
        live_data_status = {
            "integration_available": DORTMUND_INTEGRATION_AVAILABLE,
            "city": "Dortmund",
            "last_check": None,
            "available_locations": 0
        }
        
        if DORTMUND_INTEGRATION_AVAILABLE:
            try:
                live_data_list = DortmundParkingData.fetch_live_parking_data()
                if live_data_list:
                    live_data_status.update({
                        "last_check": "erfolgreiche Verbindung",
                        "available_locations": len(live_data_list),
                        "status": "operational"
                    })
                else:
                    live_data_status.update({
                        "last_check": "keine Daten verfügbar",
                        "status": "no_data"
                    })
            except Exception as e:
                live_data_status.update({
                    "last_check": f"Fehler: {str(e)}",
                    "status": "error"
                })
        
        return Response({
            "total_routes": total_routes,
            "avg_duration_minutes": round(avg_duration) if avg_duration else 0,
            "favorite_parking": favorite_parking.get('parkplatz__name') if favorite_parking else None,
            "recent_routes": recent_routes,
            "profile_completion": {
                "has_favorite_club": bool(user.profil.lieblingsverein),
                "has_stadium": bool(user.profil.lieblingsverein and user.profil.lieblingsverein.stadien.exists()),
                "completion_percentage": 100 if user.profil.lieblingsverein else 50
            },
            "live_data_status": live_data_status  # Neue Sektion
        })
        
    except Exception as e:
        return Response(
            {"detail": f"Fehler beim Laden der Dashboard-Daten: {str(e)}"},
            status=500
        )


from .performance_monitor import performance_monitor, get_research_export

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def performance_analysis(request):
    """
    Live Performance-Analyse für aktuelle Session
    
    Liefert detaillierte Metriken der letzten Routenberechnung für 
    Echtzeit-Debugging und wissenschaftliche Auswertung.
    """
    try:
        summary = performance_monitor.get_session_summary()
        
        if "error" in summary:
            return Response({
                "status": "no_data",
                "message": "Keine Performance-Daten verfügbar. Führen Sie zuerst eine Routenberechnung durch."
            })
        
        # Erweiterte Analyse für Masterarbeit
        analysis = {
            "session_overview": summary["session_info"],
            "detailed_breakdown": summary["operation_breakdown"],
            "identified_bottlenecks": summary["bottlenecks"],
            "optimization_recommendations": summary["recommendations"],
            
            # Wissenschaftliche Metriken
            "scientific_metrics": {
                "operations_per_second": len(summary["session_info"]) / summary["session_info"]["total_duration"] if summary["session_info"]["total_duration"] > 0 else 0,
                "api_call_efficiency": calculate_api_efficiency(summary["operation_breakdown"]),
                "parallelization_potential": calculate_parallelization_potential(summary["operation_breakdown"]),
                "scalability_projection": project_scalability(summary["session_info"])
            },
            
            # Verbesserungsvorschläge mit Zeitschätzungen
            "optimization_potential": {
                "current_performance": f"{summary['session_info']['total_duration']:.2f}s",
                "with_parallelization": f"{calculate_parallel_time(summary['operation_breakdown']):.2f}s",
                "with_caching": f"{calculate_cached_time(summary['operation_breakdown']):.2f}s",
                "with_batch_apis": f"{calculate_batch_time(summary['operation_breakdown']):.2f}s",
                "optimal_target": "2-4 seconds"
            }
        }
        
        return Response(analysis)
        
    except Exception as e:
        logger.error(f"Fehler bei Performance-Analyse: {e}")
        return Response({
            "error": f"Fehler bei der Performance-Analyse: {str(e)}"
        }, status=500)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def monitoring_export(request):
    """
    Vollständiger Export aller Performance-Daten für Masterarbeit
    
    Liefert alle gesammelten Monitoring-Daten im wissenschaftlichen Format
    für statistische Auswertung und Dokumentation.
    """
    try:
        # Vollständiger Export für Forschung
        research_data = get_research_export()
        
        # Zusätzliche Metadaten für Masterarbeit
        enhanced_research_data = {
            **research_data,
            "masterarbeit_metadata": {
                "title": "Optimierung der Fan-Anreise durch datengetriebene Technologien",
                "export_purpose": "Performance-Analyse und Optimierungsnachweis",
                "data_collection_period": {
                    "start": research_data["monitoring_metadata"]["export_timestamp"],
                    "sessions_analyzed": research_data["monitoring_metadata"]["total_sessions"]
                },
                "research_questions": [
                    "Welche API-Calls sind die größten Performance-Bottlenecks?",
                    "Wie wirkt sich die Anzahl der Parkplätze auf die Antwortzeit aus?",
                    "Welche Optimierungsmethoden bieten das größte Verbesserungspotenzial?"
                ]
            },
            
            # Statistische Auswertung
            "statistical_analysis": generate_statistical_analysis(research_data),
            
            # Performance-Trends
            "performance_trends": analyze_performance_trends(research_data),
            
            # Empfehlungen für Produktivsystem
            "production_recommendations": generate_production_recommendations(research_data)
        }
        
        return Response(enhanced_research_data)
        
    except Exception as e:
        logger.error(f"Fehler bei Monitoring-Export: {e}")
        return Response({
            "error": f"Fehler beim Export der Monitoring-Daten: {str(e)}"
        }, status=500)


# Hilfsfunktionen für wissenschaftliche Analyse

def calculate_api_efficiency(operation_breakdown: Dict[str, Dict]) -> Dict[str, Any]:
    """Berechnet API-Effizienz-Metriken"""
    api_operations = {k: v for k, v in operation_breakdown.items() 
                     if any(term in k.lower() for term in ['google', 'api', 'dortmund', 'gpt'])}
    
    total_api_time = sum(op["total_time"] for op in api_operations.values())
    total_api_calls = sum(op["count"] for op in api_operations.values())
    
    return {
        "total_api_time_seconds": round(total_api_time, 2),
        "total_api_calls": total_api_calls,
        "average_api_latency": round(total_api_time / total_api_calls, 2) if total_api_calls > 0 else 0,
        "api_time_percentage": round((total_api_time / sum(op["total_time"] for op in operation_breakdown.values())) * 100, 1),
        "efficiency_rating": "poor" if total_api_time > 20 else "fair" if total_api_time > 10 else "good"
    }


def calculate_parallelization_potential(operation_breakdown: Dict[str, Dict]) -> Dict[str, Any]:
    """Berechnet das Potenzial für Parallelisierung"""
    parallelizable_ops = {k: v for k, v in operation_breakdown.items() 
                         if 'google_directions' in k or 'live_data' in k}
    
    sequential_time = sum(op["total_time"] for op in parallelizable_ops.values())
    parallel_time = max(op["max_time"] for op in parallelizable_ops.values()) if parallelizable_ops else 0
    
    time_savings = sequential_time - parallel_time
    improvement_percentage = (time_savings / sequential_time * 100) if sequential_time > 0 else 0
    
    return {
        "current_sequential_time": round(sequential_time, 2),
        "estimated_parallel_time": round(parallel_time, 2),
        "potential_time_savings": round(time_savings, 2),
        "improvement_percentage": round(improvement_percentage, 1),
        "parallelizable_operations": len(parallelizable_ops),
        "recommendation": "High Priority" if improvement_percentage > 50 else "Medium Priority" if improvement_percentage > 25 else "Low Priority"
    }


def project_scalability(session_info: Dict[str, Any]) -> Dict[str, Any]:
    """Projiziert Skalierbarkeit für verschiedene Parkplatz-Anzahlen"""
    current_count = session_info.get("context", {}).get("parking_count", 1)
    current_time = session_info["total_duration"]
    
    # Lineare Skalierung (worst case)
    time_per_parking = current_time / current_count if current_count > 0 else current_time
    
    projections = {}
    for count in [5, 10, 15, 20, 50]:
        linear_time = time_per_parking * count
        projections[f"{count}_parkplaetze"] = {
            "linear_scaling": round(linear_time, 1),
            "with_parallelization": round(linear_time * 0.2, 1),  # 80% Verbesserung
            "with_full_optimization": round(linear_time * 0.1, 1),  # 90% Verbesserung
            "usability": "good" if linear_time * 0.1 < 5 else "acceptable" if linear_time * 0.1 < 10 else "poor"
        }
    
    return projections


def calculate_parallel_time(operation_breakdown: Dict[str, Dict]) -> float:
    """Schätzt Zeit mit Parallelisierung"""
    google_ops = [op for name, op in operation_breakdown.items() if 'google_directions' in name]
    if not google_ops:
        return sum(op["total_time"] for op in operation_breakdown.values())
    
    # Max Zeit der parallelisierbaren Operationen + serielle Operationen
    max_parallel_time = max(op["max_time"] for op in google_ops)
    serial_time = sum(op["total_time"] for name, op in operation_breakdown.items() 
                     if 'google_directions' not in name)
    
    return max_parallel_time + serial_time


def calculate_cached_time(operation_breakdown: Dict[str, Dict]) -> float:
    """Schätzt Zeit mit Caching (wiederholte Operationen)"""
    total_time = sum(op["total_time"] for op in operation_breakdown.values())
    
    # Annahme: 70% der wiederholten API-Calls können gecacht werden
    cached_savings = 0
    for op in operation_breakdown.values():
        if op["count"] > 1:
            cached_savings += op["total_time"] * 0.7
    
    return max(total_time - cached_savings, total_time * 0.3)


def calculate_batch_time(operation_breakdown: Dict[str, Dict]) -> float:
    """Schätzt Zeit mit Batch-API-Requests"""
    # Google Distance Matrix API kann multiple Ziele in einem Request
    google_ops = [op for name, op in operation_breakdown.items() if 'google_directions' in name]
    
    if not google_ops:
        return sum(op["total_time"] for op in operation_breakdown.values())
    
    # Batch-Request: 3-5 einzelne Requests → 1 Batch-Request
    google_time = sum(op["total_time"] for op in google_ops)
    batch_time = google_time * 0.3  # 70% Zeitersparnis durch Batching
    
    other_time = sum(op["total_time"] for name, op in operation_breakdown.items() 
                    if 'google_directions' not in name)
    
    return batch_time + other_time


def generate_statistical_analysis(research_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generiert statistische Auswertung für Masterarbeit"""
    sessions = research_data.get("all_sessions", [])
    
    if not sessions:
        return {"error": "Keine Sessions für Analyse verfügbar"}
    
    durations = [s["total_duration"] for s in sessions]
    
    return {
        "session_count": len(sessions),
        "duration_statistics": {
            "mean": round(sum(durations) / len(durations), 2),
            "min": round(min(durations), 2),
            "max": round(max(durations), 2),
            "median": round(sorted(durations)[len(durations)//2], 2)
        },
        "performance_classification": {
            "excellent": sum(1 for d in durations if d < 5),
            "good": sum(1 for d in durations if 5 <= d < 10),
            "acceptable": sum(1 for d in durations if 10 <= d < 20),
            "poor": sum(1 for d in durations if d >= 20)
        }
    }


def analyze_performance_trends(research_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analysiert Performance-Trends über Zeit"""
    sessions = research_data.get("all_sessions", [])
    
    if len(sessions) < 2:
        return {"note": "Mindestens 2 Sessions für Trend-Analyse erforderlich"}
    
    # Chronologische Sortierung
    sorted_sessions = sorted(sessions, key=lambda x: x.get("start_datetime", ""))
    
    recent_avg = sum(s["total_duration"] for s in sorted_sessions[-3:]) / min(3, len(sorted_sessions))
    early_avg = sum(s["total_duration"] for s in sorted_sessions[:3]) / min(3, len(sorted_sessions))
    
    trend = "improving" if recent_avg < early_avg else "stable" if abs(recent_avg - early_avg) < 1 else "degrading"
    
    return {
        "trend_direction": trend,
        "early_average": round(early_avg, 2),
        "recent_average": round(recent_avg, 2),
        "performance_change": round(((recent_avg - early_avg) / early_avg) * 100, 1) if early_avg > 0 else 0
    }


def generate_production_recommendations(research_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generiert Empfehlungen für Produktivsystem"""
    avg_duration = research_data.get("aggregated_statistics", {}).get("avg_session_duration", 0)
    
    recommendations = []
    
    if avg_duration > 15:
        recommendations.append({
            "priority": "CRITICAL",
            "area": "Architecture",
            "recommendation": "Implementierung von asynchroner Verarbeitung und Parallelisierung",
            "expected_improvement": "70-80% Zeitreduktion",
            "implementation_effort": "High"
        })
    
    if avg_duration > 10:
        recommendations.append({
            "priority": "HIGH", 
            "area": "API Optimization",
            "recommendation": "Google Distance Matrix API für Batch-Requests nutzen",
            "expected_improvement": "40-60% weniger API-Calls",
            "implementation_effort": "Medium"
        })
    
    recommendations.append({
        "priority": "MEDIUM",
        "area": "Caching",
        "recommendation": "Redis-basiertes Caching für Routenberechnungen (5-15min TTL)",
        "expected_improvement": "85-95% bei wiederholten Anfragen",
        "implementation_effort": "Low"
    })
    
    return recommendations

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def research_data_export(request):
    """
    FORSCHUNGS-API: Export von anonymisierten Daten für wissenschaftliche Auswertungen
    
    Dieser Endpoint liefert strukturierte Daten für Masterarbeit-Analysen,
    ohne persönliche Informationen preiszugeben.
    """
    try:
        # Allgemeine Nutzungsstatistiken (anonymisiert)
        total_users = User.objects.count()
        total_routes = Route.objects.count()
        
        # Stadion-bezogene Statistiken  
        stadion_stats = Route.objects.values('stadion__name').annotate(
            route_count=models.Count('id'),
            avg_duration=models.Avg('dauer_minuten'),
            unique_users=models.Count('benutzer', distinct=True)
        ).order_by('-route_count')
        
        # Parkplatz-Nutzung
        parkplatz_stats = Route.objects.values('parkplatz__name').annotate(
            usage_count=models.Count('id')
        ).order_by('-usage_count')[:10]
        
        # Live-Daten Verfügbarkeit
        live_data_info = {
            "integration_available": DORTMUND_INTEGRATION_AVAILABLE,
            "data_source": "Dortmund Open Data Portal",
            "api_endpoint": "https://open-data.dortmund.de/api/explore/v2.1/catalog/datasets/parkhauser/records"
        }
        
        if DORTMUND_INTEGRATION_AVAILABLE:
            try:
                live_locations = DortmundParkingData.fetch_live_parking_data()
                live_data_info.update({
                    "current_locations": len(live_locations) if live_locations else 0,
                    "status": "operational" if live_locations else "no_data"
                })
            except Exception:
                live_data_info["status"] = "error"
        
        return Response({
            "export_timestamp": datetime.now().isoformat(),
            "research_context": {
                "system": "MatchRoute - Fan-Anreise Optimierung",
                "purpose": "Masterarbeit - Optimierung der Fan-Anreise durch datengetriebene Technologien",
                "data_privacy": "Alle Daten anonymisiert, keine persönlichen Informationen"
            },
            "usage_statistics": {
                "total_users": total_users,
                "total_routes_calculated": total_routes,
                "stadion_preferences": list(stadion_stats),
                "popular_parking": list(parkplatz_stats)
            },
            "live_data_integration": live_data_info,
            "api_capabilities": {
                "routing_engine": "Google Maps Directions API",
                "traffic_data": "Google Maps Traffic Layer",
                "weather_data": "OpenWeatherMap API",
                "ai_comments": "OpenAI GPT-4",
                "live_parking": "Dortmund Open Data" if DORTMUND_INTEGRATION_AVAILABLE else "Not Available"
            }
        })
        
    except Exception as e:
        logger.error(f"Fehler bei Research Data Export: {e}")
        return Response({
            "error": f"Fehler beim Export der Forschungsdaten: {str(e)}"
        }, status=500)