from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework import viewsets, generics
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User

from parkmanagement.utils import berechne_route
from .models import Parkplatz, Stadion, Verein
from .serializers import ParkplatzSerializer, StadionSerializer, UserRegisterSerializer, VereinSerializer

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