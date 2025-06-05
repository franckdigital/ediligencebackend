from rest_framework import routers
from .views import (
    SetFingerprintView,
    LieuxEntrepriseView,
    AdminRegistrationView, UserProfileView, LoginView, UserViewSet,
    DirectionViewSet, ServiceViewSet, CourrierViewSet, DiligenceViewSet,
    DiligenceDownloadFichierView, AgentRegistrationView, ImputationFileViewSet
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
from .views import ImputationAccessViewSet, RolePermissionViewSet, PresenceViewSet
router.register(r'imputation-access', ImputationAccessViewSet, basename='imputation-access')
router.register(r'role-permissions', RolePermissionViewSet, basename='role-permissions')
router.register(r'presences', PresenceViewSet, basename='presences')

# --- ROUTES SUIVI PROJETS & TACHES ---
router.register(r'projets', ProjetViewSet)
router.register(r'taches', TacheViewSet)
router.register(r'commentaires', CommentaireViewSet)
router.register(r'fichiers', FichierViewSet)

urlpatterns = [
    path('set-fingerprint/', SetFingerprintView.as_view(), name='set-fingerprint'),
    path('lieux-entreprise/', LieuxEntrepriseView.as_view(), name='lieux-entreprise'),
    path('stats/presence/', PresenceStatsAPIView.as_view(), name='presence-stats'),
    path('', include(router.urls)),
    path('auth/register/', AgentRegistrationView.as_view(), name='register'),
    path('auth/register/admin/', AdminRegistrationView.as_view(), name='register_admin'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/me/', UserProfileView.as_view(), name='user_profile'),
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


