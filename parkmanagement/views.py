from django.shortcuts import render
from rest_framework import viewsets, generics
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from .models import Parkplatz
from .serializers import ParkplatzSerializer, UserRegisterSerializer

class ParkplatzViewSet(viewsets.ModelViewSet):
    queryset = Parkplatz.objects.all()
    serializer_class = ParkplatzSerializer
    #permission_classes = [IsAuthenticated]

class UserRegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer