from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework import viewsets, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth.models import User
from django.conf import settings

import requests

from parkmanagement.utils import (
    berechne_gesamtzeit_mit_realistischer_bewertung, 
    berechne_optimierte_parkplatz_empfehlung,
    generiere_intelligenten_verkehrskommentar,
    hole_wetter_mit_verkehrseinfluss,
    berechne_google_route,
    geocode_adresse,
)
from .models import Parkplatz, Route, Stadion, Verein
from .serializers import (
    ParkplatzSerializer,
    RouteSerializer,
    StadionSerializer,
    UserRegisterSerializer,
    VereinSerializer,
)


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
    Optimierte Route-Suggestion mit vollständiger Google Maps Integration
    und realistischer Verkehrsbewertung.
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

        # Optimierte Batch-Berechnung verwenden
        vorschlaege = berechne_optimierte_parkplatz_empfehlung(
            start_adresse, parkplaetze, stadion
        )

        if not vorschlaege:
            return Response(
                {"detail": "Keine Route gefunden. Bitte überprüfen Sie Ihre Startadresse."}, 
                status=400
            )

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
            print(f"Wetter/GPT Fehler: {e}")
            # Fallback bleibt bestehen

        alle_ohne_bester = vorschlaege[1:]

        return Response(
            {
                "empfohlener_parkplatz": bester, 
                "alle_parkplaetze": alle_ohne_bester,
                "meta": {
                    "total_options": len(vorschlaege),
                    "calculation_time": "live",
                    "data_source": "Google Maps API"
                }
            },
            status=200,
        )


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


# Zusätzliche API für Dashboard-Statistiken
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """
    Liefert Dashboard-Statistiken für den angemeldeten Benutzer.
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
        
        return Response({
            "total_routes": total_routes,
            "avg_duration_minutes": round(avg_duration) if avg_duration else 0,
            "favorite_parking": favorite_parking.get('parkplatz__name') if favorite_parking else None,
            "recent_routes": recent_routes,
            "profile_completion": {
                "has_favorite_club": bool(user.profil.lieblingsverein),
                "has_stadium": bool(user.profil.lieblingsverein and user.profil.lieblingsverein.stadien.exists()),
                "completion_percentage": 100 if user.profil.lieblingsverein else 50
            }
        })
        
    except Exception as e:
        return Response(
            {"detail": f"Fehler beim Laden der Dashboard-Daten: {str(e)}"},
            status=500
        )
