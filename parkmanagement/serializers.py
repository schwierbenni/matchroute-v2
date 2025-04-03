from rest_framework import serializers
from .models import Parkplatz
from django.contrib.auth.models import User

# This serializer is used to convert the Parkplatz model instances into JSON format and vice versa.
class ParkplatzSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parkplatz
        fields = '__all__'

class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)
    lieblingsverein = serializers.CharField(required=False, write_only=True)

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
            lieblingsverein = validated_data.pop('lieblingsverein', None)

            user = User(**validated_data)
            user.set_password(password)
            user.save()

            if lieblingsverein:
                 user.profil.lieblingsverein = lieblingsverein
                 user.profil.save()
                 
            return user