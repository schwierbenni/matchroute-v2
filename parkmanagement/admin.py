from django.contrib import admin
from .models import Parkplatz, Route
from .models import BenutzerProfil
from .models import Verein
from .models import Stadion
# Register your models here.

@admin.register(Parkplatz)
class ParkplatzAdmin(admin.ModelAdmin):
    list_display = ('name', 'stadion', 'kapazitaet', 'verfuegbar')
    list_filter = ('stadion',)

# Das Benutzerprofil-Modell wird im Admin-Bereich registriert.
# Dies ermöglicht es Administratoren, Benutzerprofile zu verwalten und zu bearbeiten.
@admin.register(BenutzerProfil)
class BenutzerProfilAdmin(admin.ModelAdmin):
    list_display = ('user', 'lieblingsverein')
    search_fields = ('user__username', 'lieblingsverein')
    list_filter = ('lieblingsverein',)
    ordering = ('user',)

@admin.register(Verein)
class VereinAdmin(admin.ModelAdmin):
    list_display = ('name', 'stadt', 'liga')
    search_fields = ('name', 'stadt')

@admin.register(Stadion)
class StadionAdmin(admin.ModelAdmin):
    list_display = ('name', 'verein', 'adresse')
    search_fields = ('name', 'verein__name')

@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ('benutzer', 'stadion', 'parkplatz', 'start_adresse', 'strecke_km', 'dauer_minuten')
    search_fields = ('benutzer__username', 'stadion__name', 'parkplatz__name')
    list_filter = ('stadion', 'parkplatz')
    ordering = ('benutzer',)