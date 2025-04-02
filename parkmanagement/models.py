from django.db import models

# Create your models here.
class Parkplatz(models.Model):
    name = models.CharField(max_length=100)
    adresse = models.CharField(max_length=255)
    kapazitaet = models.IntegerField()
    frei = models.IntegerField(null=True, blank=True)
    preis_pro_stunde = models.DecimalField(max_digits=5, decimal_places=2)
    verfuegbar = models.BooleanField(default=True)
    bewertung = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    oeffnungszeiten = models.CharField(max_length=100, null=True, blank=True)
    schliesszeiten = models.CharField(max_length=100, null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    letztes_update = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
