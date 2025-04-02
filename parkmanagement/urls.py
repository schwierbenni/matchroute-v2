from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ParkplatzViewSet

router = DefaultRouter()
router.register(r'parkplatz', ParkplatzViewSet, basename='parkplatz')

urlpatterns = [
    path('', include(router.urls)),
]