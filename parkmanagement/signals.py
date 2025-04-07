from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import BenutzerProfil


# Jedes Mal, wenn ein neuer Benutzer erstellt wird, wird auch ein Benutzerprofil erstellt.
# Dies geschieht durch die Verwendung von Django Signals.
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        BenutzerProfil.objects.create(user=instance)
        
# Jedes Mal, wenn ein Benutzer gespeichert wird, wird auch das Benutzerprofil gespeichert.
@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profil.save()