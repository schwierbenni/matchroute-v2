from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework import viewsets, generics
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User

from parkmanagement.utils import berechne_route
from .models import Parkplatz, Route, Stadion, Verein
from .serializers import ParkplatzSerializer, RouteSerializer, StadionSerializer, UserRegisterSerializer, VereinSerializer

# Dieses ViewSet wird verwendet, um die Parkplatz-API zu erstellen.
# Es ermöglicht das Erstellen, Bearbeiten, Löschen und Abrufen von Parkplätzen.
class ParkplatzViewSet(viewsets.ModelViewSet):
    # queryset definiert die Daten, die von der API zurückgegeben werden.
    queryset = Parkplatz.objects.all()
    # serializer_class definiert den Serializer, der verwendet wird, um die Daten zu serialisieren.
    serializer_class = ParkplatzSerializer
    #permission_classes = [IsAuthenticated]

# Diese View wird verwendet, um die Registrierung eines neuen Benutzers zu ermöglichen.
# API, die nur die Anlage eines neuen Benutzers ermöglicht.
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
        return self.queryset.filter(benutzer=user).order_by('-erstelldatum')

class RouteSuggestionView(APIView):

    def post(self, request):
        start_adresse = request.data.get('start_adresse')
        user = request.user
        stadion = user.profil.lieblingsverein.stadien.first()
        parkplaetze = stadion.parkplaetze.all()
        vorschlaege = []

        for parkplatz in parkplaetze:
            result = berechne_route(start_adresse, parkplatz.latitude, parkplatz.longitude)
            if result:
                vorschlaege.append({
                    "parkplatz": {
                        "id": parkplatz.id,
                        "name": parkplatz.name,
                        "latitude": float(parkplatz.latitude),
                        "longitude": float(parkplatz.longitude),
                    },
                    "dauer_min": result["dauer_min"],
                    "distanz_km": result["distanz_km"],
                    "polyline": result["polyline"]
                })

        if not vorschlaege:
            return Response({"detail": "Keine Route gefunden."}, status=400)

        bester = min(vorschlaege, key=lambda x: x["dauer_min"])

        return Response({
            "empfohlener_parkplatz": bester,
            "alle_parkplaetze": vorschlaege
        }, status=status.HTTP_200_OK)
    
# Diese View wird verwendet, um eine Route zu speichern. 
# Wenn der Benutzer im Frontend eine Navigation startet, sollen im Backend die Eckdaten zur Route abgespeichert werden.
class RouteSpeichernView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        data = request.data

        try:
            stadion = Stadion.objects.get(id=data.get("stadion_id"))
            parkplatz = Parkplatz.objects.get(id=data.get("parkplatz_id"))
        except (Stadion.DoesNotExist, Parkplatz.DoesNotExist):
            return Response({"detail": "Stadion oder Parkplatz nicht gefunden."}, status=400)

        route = Route.objects.create(
            benutzer=user,
            stadion=stadion,
            parkplatz=parkplatz,
            start_adresse=data.get("start_adresse"),
            start_latitude=data.get("start_lat"),
            start_longitude=data.get("start_lng"),
            strecke_km=data.get("distanz_km"),
            dauer_min=data.get("dauer_min"),
            transportmittel=data.get("transportmittel", "auto"),
            route_url=data.get("route_url")
        )

        return Response({"detail": "Route gespeichert.", "route_id": route.id}, status=201)