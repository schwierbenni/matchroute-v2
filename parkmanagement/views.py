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
    berechne_gesamtzeit_mit_transit_und_walk,
    generiere_gpt_verkehrstext,
    hole_wetter,
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
    permission_classes = [IsAuthenticated]

    def post(self, request):
        start_adresse = request.data.get("start_adresse")
        user = request.user

        try:
            stadion = user.profil.lieblingsverein.stadien.first()
        except AttributeError:
            return Response(
                {"detail": "Kein Lieblingsverein oder Stadion gefunden."}, status=400
            )

        parkplaetze = stadion.parkplaetze.all()
        vorschlaege = []

        for parkplatz in parkplaetze:
            result = berechne_gesamtzeit_mit_transit_und_walk(
                start_adresse, parkplatz, stadion
            )

            if result:
                
                wetter = hole_wetter(stadion.latitude, stadion.longitude)
                
                gpt_kommentar = generiere_gpt_verkehrstext(
                    dauer_min=result.get("dauer_traffic"),
                    dauer_normal_min = result.get("dauer_auto"),
                    wetter=wetter,
                    ort = stadion.name
                )
                
                vorschlaege.append(
                    {
                        "parkplatz": {
                            "id": parkplatz.id,
                            "name": parkplatz.name,
                            "latitude": float(parkplatz.latitude),
                            "longitude": float(parkplatz.longitude),
                        },
                        "dauer_auto": result.get("dauer_auto"),
                        "dauer_traffic": result.get("dauer_traffic"),
                        "verkehr_bewertung": result.get("verkehr_bewertung"),
                        "verkehr_kommentar": gpt_kommentar,
                        "dauer_transit": result.get("dauer_transit"),
                        "dauer_walking": result.get("dauer_walking"),
                        "beste_methode": result.get("beste_methode"),
                        "gesamtzeit": result.get("gesamt_min"),
                        "distanz_km": result.get("distanz_km"),
                        "polyline_auto": result.get("polyline_auto"),
                        "polyline_transit": result.get("polyline_transit"),
                        "polyline_walking": result.get("polyline_walking"),
                    }
                )

        if not vorschlaege:
            return Response({"detail": "Keine Route gefunden."}, status=400)

        bester = min(vorschlaege, key=lambda x: x["gesamtzeit"])
        alle_ohne_bester = [v for v in vorschlaege if v != bester]

        return Response(
            {"empfohlener_parkplatz": bester, "alle_parkplaetze": alle_ohne_bester},
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
                {"detail": "Route gespeichert.", "route_id": route.id},
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
        profil = request.user.profil
        lieblingsverein = profil.lieblingsverein
        stadion = lieblingsverein.stadien.first() if lieblingsverein else None
        return Response(
            {
                "username": request.user.username,
                "email": request.user.email,
                "lieblingsverein": VereinSerializer(lieblingsverein).data if lieblingsverein else None,
                "stadion": StadionSerializer(stadion).data if stadion else None
            }
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def graphhopper_route(request):
    start = request.query_params.get("start")
    ziel = request.query_params.get("ziel")
    profile = request.query_params.get("profile", "foot")

    if not start or not ziel:
        return Response({"detail": "Start und Ziel müssen angegeben werden."}, status=400)

    url = "https://graphhopper.com/api/1/route"
    params = {
        "point": [start, ziel],
        "profile": profile,
        "instructions": "true",
        "locale": "de",
        "key": settings.GRAPH_HOPPER_API_KEY,
    }

    try:
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
        instructions = data.get("paths", [{}])[0].get("instructions", [])
        return Response({"instructions": instructions})
    except Exception as e:
        return Response({"detail": f"Fehler bei der Anfrage an GraphHopper: {str(e)}"}, status=500)
