
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
    # 🆕 Neue Dortmund Live-Daten Endpoints
    dortmund_parking_overview,
    live_parking_status,
    research_data_export,
    performance_analysis,
    monitoring_export
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
    
    # Google Maps basierte Endpoints
    path("route-details/", google_route_details, name="google_route_details"),
    path("geocode/", geocode_address, name="geocode_address"),
    
    # Dashboard API
    path("dashboard-stats/", dashboard_stats, name="dashboard_stats"),
    
    # 🆕 NEUE ENDPOINTS: Dortmund Live-Daten Integration
    path("dortmund/parking-overview/", dortmund_parking_overview, name="dortmund_parking_overview"),
    path("live-parking-status/", live_parking_status, name="live_parking_status"),
    
    # 🎓 FORSCHUNGS-ENDPOINTS für Masterarbeit
    path("research/data-export/", research_data_export, name="research_data_export"),
    
    path("performance/analysis/", performance_analysis, name="performance_analysis"),
    path("performance/export/", monitoring_export, name="monitoring_export"),
    
    # Router URLs
    path('', include(router.urls)),
]