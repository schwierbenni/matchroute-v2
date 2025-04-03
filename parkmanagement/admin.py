from django.contrib import admin
from .models import Parkplatz
from .models import BenutzerProfil
# Register your models here.

# Registering the Parkplatz model with the Django admin interface
admin.site.register(Parkplatz)

# Registering the Benutzer model with the Django admin interface
@admin.register(BenutzerProfil)
class BenutzerProfilAdmin(admin.ModelAdmin):
    list_display = ('user', 'lieblingsverein')
    search_fields = ('user__username', 'lieblingsverein')
    list_filter = ('lieblingsverein',)
    ordering = ('user',)