from django.apps import AppConfig

# Die AppConfig-Klasse für die Parkmanagement-App.
# Diese Klasse wird verwendet, um die Konfiguration für die App Parkmanagement zu definieren.
class ParkmanagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'parkmanagement'

# Diese Methode wird aufgerufen, wenn die App bereit ist.
    # Hier importieren wir die Signale, damit sie registriert werden.
    def ready(self):
        import parkmanagement.signals
