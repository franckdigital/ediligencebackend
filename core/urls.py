from rest_framework import routers
from .views import (
    SetFingerprintView,
    PresenceFingerprintView,
    UserProfileView,
    ChangePasswordView,
    AdminRegistrationView, LoginView, UserViewSet,
    DirectionViewSet, ServiceViewSet, CourrierViewSet, DiligenceViewSet,
    DiligenceDownloadFichierView, AgentRegistrationView, ImputationFileViewSet,
    ImputationAccessViewSet, RolePermissionViewSet, PresenceViewSet
)
from .task_views import ProjetViewSet, TacheViewSet, CommentaireViewSet, FichierViewSet
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from core.views_stats import PresenceStatsAPIView

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'directions', DirectionViewSet)
router.register(r'services', ServiceViewSet)
router.register(r'courriers', CourrierViewSet)
router.register(r'diligences', DiligenceViewSet)
router.register(r'imputation-files', ImputationFileViewSet)
from .views import ImputationAccessViewSet, RolePermissionViewSet, PresenceViewSet, MaPresenceDuJourView
from rest_framework_simplejwt.views import TokenRefreshView
from .serializers import MyTokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer
router.register(r'imputation-access', ImputationAccessViewSet, basename='imputation-access')
router.register(r'role-permissions', RolePermissionViewSet, basename='role-permissions')
router.register(r'presences', PresenceViewSet, basename='presences')

# --- ROUTES SUIVI PROJETS & TACHES ---
router.register(r'projets', ProjetViewSet)
router.register(r'taches', TacheViewSet)
router.register(r'commentaires', CommentaireViewSet)
router.register(r'fichiers', FichierViewSet)

urlpatterns = [
    path('token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('presence/ma-presence-du-jour/', MaPresenceDuJourView.as_view(), name='ma-presence-du-jour'),
    path('set-fingerprint/', SetFingerprintView.as_view(), name='set-fingerprint'),

    path('presence/fingerprint/', PresenceFingerprintView.as_view(), name='presence-fingerprint'),
    path('stats/presence/', PresenceStatsAPIView.as_view(), name='presence-stats'),
    path('', include(router.urls)),
    path('auth/register/', AgentRegistrationView.as_view(), name='register'),
    path('auth/register/admin/', AdminRegistrationView.as_view(), name='register_admin'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/me/', UserProfileView.as_view(), name='user_profile'),
    path('auth/change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('diligences/<int:pk>/download-fichier/', DiligenceDownloadFichierView.as_view(), name='diligence-download-fichier'),
    path('taches/<int:pk>/commentaires/',
         __import__('core.task_views').task_views.tache_commentaires,
         name='tache_commentaires'),
    path('taches/<int:pk>/commentaires/<int:comment_id>/',
         __import__('core.task_views').task_views.tache_commentaire_detail,
         name='tache_commentaire_detail'),
    path('taches/<int:pk>/historique/',
         __import__('core.task_views').task_views.tache_historique,
         name='tache_historique'),
    
]


