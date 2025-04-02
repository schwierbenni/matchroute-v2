from django.shortcuts import render
from rest_framework import viewsets
from .models import Parkplatz
from .serializers import ParkplatzSerializer

class ParkplatzViewSet(viewsets.ModelViewSet):
    queryset = Parkplatz.objects.all()
    serializer_class = ParkplatzSerializer

