from rest_framework import serializers
from .models import Parkplatz, Route, Stadion, Verein
from django.contrib.auth.models import User

# Dieser Serializer wird verwendet, um die Daten für den Parkplatz zu serialisieren.
# Er wird verwendet, um die Daten in JSON-Format zu konvertieren, damit sie über die API gesendet werden können.
class ParkplatzSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parkplatz
        fields = '__all__'

# Dieser Serializer wird verwendet, um die Daten für den Benutzer zu serialisieren.
class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)
    lieblingsverein = serializers.IntegerField(required=False, write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 'lieblingsverein']

    def validate(self, data):
            if data['password'] != data['password2']:
                raise serializers.ValidationError("Passwörter stimmen nicht überein.")
            return data
        
    def create(self, validated_data):
        password = validated_data.pop('password')
        validated_data.pop('password2', None)
        lieblingsverein_id = validated_data.pop('lieblingsverein', None)

        user = User(**validated_data)
        user.set_password(password)
        user.save()

        if lieblingsverein_id:
            try:
                verein = Verein.objects.get(id=lieblingsverein_id)
                user.profil.lieblingsverein = verein
                user.profil.save()
            except Verein.DoesNotExist:
                raise serializers.ValidationError("Verein nicht gefunden.")

        return user
    
class VereinSerializer(serializers.ModelSerializer):
    class Meta:
        model = Verein
        fields = '__all__'

class StadionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stadion
        fields = '__all__'

class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = '__all__'