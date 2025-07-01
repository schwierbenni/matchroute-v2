from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ParkplatzViewSet,
    RouteSpeichernView,
    RouteSuggestionView,
    RouteViewSet,
    StadionViewSet,
    UserRegisterView,
    VereinViewSet,
    google_route_details, 
    geocode_address,
    dashboard_stats,
    ProfilView,
)

router = DefaultRouter()
router.register(r'parkplatz', ParkplatzViewSet, basename='parkplatz')
router.register(r'verein', VereinViewSet)
router.register(r'stadion', StadionViewSet)
router.register(r'routen', RouteViewSet)

urlpatterns = [
    # Hauptfunktionen
    path('routen/speichern/', RouteSpeichernView.as_view(), name='routing-speichern'),
    path('routen-vorschlag/', RouteSuggestionView.as_view(), name='routen-vorschlag'),
    path('register/', UserRegisterView.as_view(), name='register'),
    path('profil/', ProfilView.as_view(), name='profil'),
    
    # Neue Google Maps basierte Endpoints
    path("route-details/", google_route_details, name="google_route_details"),
    path("geocode/", geocode_address, name="geocode_address"),
    
    # Dashboard API
    path("dashboard-stats/", dashboard_stats, name="dashboard_stats"),
    
    # Router URLs
    path('', include(router.urls)),
]