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
    graphhopper_route,
    ProfilView,
)

router = DefaultRouter()
router.register(r'parkplatz', ParkplatzViewSet, basename='parkplatz')
router.register(r'verein', VereinViewSet)
router.register(r'stadion', StadionViewSet)
router.register(r'routen', RouteViewSet)

urlpatterns = [
    path('routen/speichern/', RouteSpeichernView.as_view(), name='routing-speichern'),
    path('routen-vorschlag/', RouteSuggestionView.as_view(), name='routen-vorschlag'),
    path('register/', UserRegisterView.as_view(), name='register'),
    path('profil/', ProfilView.as_view(), name='profil'),
    path("navigation/", graphhopper_route, name="graphhopper_route"),
    path('', include(router.urls)),
]
