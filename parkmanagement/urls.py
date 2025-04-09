from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ParkplatzViewSet, RouteSuggestionView, StadionViewSet, UserRegisterView, VereinViewSet

router = DefaultRouter()
router.register(r'parkplatz', ParkplatzViewSet, basename='parkplatz')
router.register(r'verein', VereinViewSet)
router.register(r'stadion', StadionViewSet)

# URL patterns für die Parkmanagement-App
# Hier werden die URL-Pfade für die API-Endpunkte definiert.
urlpatterns = [
    path('', include(router.urls)),
    path('register/', UserRegisterView.as_view(), name='register'),
    path('routen/vorschlag/', RouteSuggestionView.as_view(), name='routing-vorschlag'),
]