from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .geofencing_views import (
    GeofenceAlertViewSet,
    GeofenceSettingsViewSet,
    AgentLocationViewSet,
    PushNotificationTokenViewSet
)

# Router pour les APIs de géofencing
geofencing_router = DefaultRouter()
geofencing_router.register(r'geofence-alerts', GeofenceAlertViewSet, basename='geofence-alerts')
geofencing_router.register(r'geofence-settings', GeofenceSettingsViewSet, basename='geofence-settings')
geofencing_router.register(r'agent-locations', AgentLocationViewSet, basename='agent-locations')
geofencing_router.register(r'push-tokens', PushNotificationTokenViewSet, basename='push-tokens')

urlpatterns = [
    path('', include(geofencing_router.urls)),
]
