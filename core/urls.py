from rest_framework import routers
from .views import (

    BureauViewSet,
    # PresenceFingerprintView removed
    UserProfileView,
    ChangePasswordView,
    AdminRegistrationView,
    AgentRegistrationView,
    LoginView,
    ListUsersView,
    RetrieveUserView,
    DeleteUserView
)
from .views_courrier_access import CourrierAccessViewSet
# Fingerprint views removed
from .views import UserViewSet
from .views_ import UserManagementViewSet, NotificationViewSet
from .views import (
    DirectionViewSet, ServiceViewSet, DiligenceViewSet, CourrierViewSet, 
    UserViewSet, BureauViewSet, PresenceViewSet, RolePermissionViewSet,
    DiligenceDownloadFichierView, ImputationFileViewSet, MaPresenceDuJourView,
    CustomTokenObtainPairView, ImputationAccessViewSet, UserDiligenceCommentViewSet,
    UserDiligenceInstructionViewSet, DemandeCongeViewSet, DemandeAbsenceViewSet,
    CourrierImputationViewSet, SimplePresenceView, UpdatePresenceStatusView
)
from .task_views import ProjetViewSet, TacheViewSet, CommentaireViewSet, FichierViewSet, ActiviteViewSet, DomaineViewSet
from .diligence_views import DiligenceDocumentViewSet, DiligenceNotificationViewSet, EnhancedDiligenceViewSet
from .geofencing_views import GeofenceAlertViewSet, GeofenceSettingsViewSet, AgentLocationViewSet, PushNotificationTokenViewSet
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from core.views_stats import PresenceStatsAPIView
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView
from .serializers import MyTokenObtainPairSerializer

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'directions', DirectionViewSet)
router.register(r'services', ServiceViewSet)
router.register(r'courriers', CourrierViewSet)
router.register(r'courrier-access', CourrierAccessViewSet)
router.register(r'courrier-imputation', CourrierImputationViewSet, basename='courrier-imputation')
router.register(r'diligences', DiligenceViewSet)
router.register(r'imputation-files', ImputationFileViewSet)
router.register(r'imputation-access', ImputationAccessViewSet)
router.register(r'user-diligence-comments', UserDiligenceCommentViewSet, basename='user-diligence-comments')
router.register(r'user-diligence-instructions', UserDiligenceInstructionViewSet, basename='user-diligence-instructions')
router.register(r'demandes-conge', DemandeCongeViewSet, basename='demandes-conge')
router.register(r'demandes-absence', DemandeAbsenceViewSet, basename='demandes-absence')
router.register(r'bureaux', BureauViewSet)


router.register(r'role-permissions', RolePermissionViewSet, basename='role-permissions')
router.register(r'presences', PresenceViewSet, basename='presences')

# --- ROUTES GESTION D'ACTIVITE ---
router.register(r'activites', ActiviteViewSet)
router.register(r'domaines', DomaineViewSet)

# --- ROUTES NOTIFICATIONS ---
router.register(r'notifications', NotificationViewSet, basename='notifications')

# --- ROUTES DILIGENCES AMÉLIORÉES ---
router.register(r'diligence-documents', DiligenceDocumentViewSet)
router.register(r'diligence-notifications', DiligenceNotificationViewSet, basename='diligence-notifications')
router.register(r'enhanced-diligences', EnhancedDiligenceViewSet, basename='enhanced-diligences')

# --- ROUTES SUIVI PROJETS & TACHES (compatibilité) ---
router.register(r'projets', ProjetViewSet)
router.register(r'taches', TacheViewSet)
router.register(r'commentaires', CommentaireViewSet)
router.register(r'fichiers', FichierViewSet)

# --- ROUTES GÉOFENCING ---
router.register(r'geofence-alerts', GeofenceAlertViewSet, basename='geofence-alerts')
router.register(r'geofence-settings', GeofenceSettingsViewSet, basename='geofence-settings')
router.register(r'agent-locations', AgentLocationViewSet, basename='agent-locations')
router.register(r'push-tokens', PushNotificationTokenViewSet, basename='push-tokens')

urlpatterns = [
    path('token/custom/', CustomTokenObtainPairView.as_view(), name='custom_token_obtain_pair'),
    path('token/', TokenObtainPairView.as_view(serializer_class=MyTokenObtainPairSerializer), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('presence/ma-presence-du-jour/', MaPresenceDuJourView.as_view(), name='ma-presence-du-jour'),
    # Fingerprint endpoints removed - using simple button presence now
    path('presence/simple/', SimplePresenceView.as_view(), name='simple-presence'),
    path('presence/<int:presence_id>/update-status/', UpdatePresenceStatusView.as_view(), name='update-presence-status'),
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


