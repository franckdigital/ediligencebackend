from rest_framework import routers
from .views import (

    BureauViewSet,
    PresenceFingerprintView,
    UserProfileView,
    ChangePasswordView,
    AdminRegistrationView, 
    LoginView, 
)
from .views_ import UserManagementViewSet, AgentViewSet
from .views_fingerprint import SetFingerprintView, VerifyFingerprintView
from .views import UserViewSet
from .views import (

    BureauViewSet,
    PresenceFingerprintView,
    UserProfileView,
    ChangePasswordView,
    AdminRegistrationView,
    LoginView,
    DirectionViewSet,
    ServiceViewSet,
    CourrierViewSet,
    DiligenceViewSet,
    DiligenceDownloadFichierView,
    AgentRegistrationView,
    ImputationFileViewSet,
    RolePermissionViewSet,
    PresenceViewSet,
    ListUsersView,
    RetrieveUserView,
    DeleteUserView,
    MaPresenceDuJourView
)
from .task_views import ProjetViewSet, TacheViewSet, CommentaireViewSet, FichierViewSet
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from core.views_stats import PresenceStatsAPIView

router = DefaultRouter()
router.register(r'users', UserManagementViewSet)
router.register(r'directions', DirectionViewSet)
router.register(r'services', ServiceViewSet)
router.register(r'courriers', CourrierViewSet)
router.register(r'diligences', DiligenceViewSet)
router.register(r'imputation-files', ImputationFileViewSet)
router.register(r'bureaux', BureauViewSet)
from .views import RolePermissionViewSet, PresenceViewSet, MaPresenceDuJourView
from rest_framework_simplejwt.views import TokenRefreshView
from .serializers import MyTokenObtainPairSerializer
from .views import CustomTokenObtainPairView
from rest_framework_simplejwt.views import TokenObtainPairView


router.register(r'role-permissions', RolePermissionViewSet, basename='role-permissions')
router.register(r'presences', PresenceViewSet, basename='presences')

# --- ROUTES SUIVI PROJETS & TACHES ---
router.register(r'projets', ProjetViewSet)
router.register(r'taches', TacheViewSet)
router.register(r'commentaires', CommentaireViewSet)
router.register(r'fichiers', FichierViewSet)

urlpatterns = [
    path('users/', ListUsersView.as_view(), name='list_users'),
    path('users/<int:user_id>/', RetrieveUserView.as_view(), name='retrieve_user'),
    path('users/<int:user_id>/', DeleteUserView.as_view(), name='delete_user'),
    path('token/custom/', CustomTokenObtainPairView.as_view(), name='custom_token_obtain_pair'),
    path('token/', TokenObtainPairView.as_view(serializer_class=MyTokenObtainPairSerializer), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('presence/ma-presence-du-jour/', MaPresenceDuJourView.as_view(), name='ma-presence-du-jour'),
    path('api/set-fingerprint/', SetFingerprintView.as_view(), name='set_fingerprint'),
    path('api/verify-fingerprint/', VerifyFingerprintView.as_view(), name='verify_fingerprint'),
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


