from django.shortcuts import render
from rest_framework import viewsets, generics
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
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