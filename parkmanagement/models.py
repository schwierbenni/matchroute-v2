from django.db import models
from django.contrib.auth.models import User

# Model für Parkplatz
class Parkplatz(models.Model):
    name = models.CharField(max_length=100)
    adresse = models.CharField(max_length=255)
    
    kapazitaet = models.IntegerField(null=True, blank=True)
    frei = models.IntegerField(default=0, null=True, blank=True)
    preis_pro_stunde = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    verfuegbar = models.BooleanField(default=True)
    bewertung = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    oeffnungszeiten = models.CharField(max_length=100, null=True, blank=True)
    schliesszeiten = models.CharField(max_length=100, null=True, blank=True)

    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    
    letztes_update = models.DateTimeField(auto_now=True)
    stadion = models.ForeignKey('Stadion', on_delete=models.CASCADE, null=True, blank=True, related_name='parkplaetze')

    def __str__(self):
        return self.name

# Model für Benutzerprofil
# Das Benutzerprofil erweitert die Django User-Klasse um zusätzliche Informationen.
class BenutzerProfil(models.Model): 
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profil')
    lieblingsverein = models.ForeignKey('Verein', on_delete=models.SET_NULL, null=True, blank=True, related_name='fans')

    def __str__(self):
        return f"{self.user.username} - Lieblingsverein: {self.lieblingsverein}"
    
class Verein(models.Model):
    name = models.CharField(max_length=100, unique=True)
    stadt = models.CharField(max_length=100, blank=True, null=True)
    liga = models.CharField(max_length=50, blank=True, null=True)
    logo_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name

class Stadion(models.Model):
    name = models.CharField(max_length=100)
    verein = models.ForeignKey(Verein, on_delete=models.CASCADE, related_name='stadien')
    adresse = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    bild_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.verein})"
    
class Route(models.Model):
    benutzer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='routen')
    stadion = models.ForeignKey(Stadion, on_delete=models.CASCADE, related_name='routen')
    parkplatz = models.ForeignKey(Parkplatz, on_delete=models.SET_NULL, null=True, related_name='routen')
    start_adresse = models.CharField(max_length=255)
    start_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    start_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    strecke_km = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    dauer_minuten = models.IntegerField(null=True, blank=True)
    transportmittel = models.CharField(max_length=50, choices=[('auto', 'Auto'), ('bus', 'Bus'), ('bahn', 'Bahn'), ('zu_fuss', 'zu Fuß')], default='auto')
    erstelldatum = models.DateTimeField(auto_now_add=True)
    route_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"{self.benutzer.username} beantragt Route von {self.start_adresse} zu {self.stadion.name} am {self.erstelldatum.date()}"