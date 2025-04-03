from django.apps import AppConfig


class ParkmanagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'parkmanagement'

    def ready(self):
        import parkmanagement.signals
