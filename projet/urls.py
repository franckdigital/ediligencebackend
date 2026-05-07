from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

app_name = 'projet'

router = DefaultRouter()
router.register(r'projets', views.ProjetViewSet, basename='projet')
router.register(r'taches', views.TacheViewSet, basename='tache')
router.register(r'sous-taches', views.SousTacheViewSet, basename='sous-tache')
router.register(r'commentaires', views.CommentaireTacheViewSet, basename='commentaire')
router.register(r'pieces-jointes', views.PieceJointeViewSet, basename='piece-jointe')
router.register(r'livrables', views.LivrableViewSet, basename='livrable')
router.register(r'notifications', views.NotificationProjetViewSet, basename='notification')
router.register(r'validations', views.ValidationTacheViewSet, basename='validation')
router.register(r'historique', views.HistoriqueActionViewSet, basename='historique')

urlpatterns = [
    # ViewSets (CRUD automatique)
    path('', include(router.urls)),

    # Dashboard global
    path('dashboard/', views.dashboard_global, name='dashboard'),

    # Reporting
    path('rapports/projet/<int:projet_id>/', views.rapport_projet, name='rapport-projet'),
    path('rapports/agent/', views.rapport_agent, name='rapport-agent-self'),
    path('rapports/agent/<int:user_id>/', views.rapport_agent, name='rapport-agent'),

    # Détection des retards (cron / admin)
    path('detecter-retards/', views.detecter_retards, name='detecter-retards'),

    # Agenda / Calendrier
    path('agenda/', views.agenda_calendrier, name='agenda'),

    # Rapport global avancé
    path('rapports/global/', views.rapport_global, name='rapport-global'),
]
