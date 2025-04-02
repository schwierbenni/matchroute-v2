from rest_framework import serializers
from .models import Parkplatz

class ParkplatzSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parkplatz
        fields = '__all__'