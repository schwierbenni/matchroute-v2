from django.contrib import admin
from .models import Parkplatz
from .models import BenutzerProfil
# Register your models here.

# Das Parkplatz-Modell wird im Admin-Bereich registriert.
admin.site.register(Parkplatz)

# Das Benutzerprofil-Modell wird im Admin-Bereich registriert.
# Dies ermöglicht es Administratoren, Benutzerprofile zu verwalten und zu bearbeiten.
@admin.register(BenutzerProfil)
class BenutzerProfilAdmin(admin.ModelAdmin):
    list_display = ('user', 'lieblingsverein')
    search_fields = ('user__username', 'lieblingsverein')
    list_filter = ('lieblingsverein',)
    ordering = ('user',)