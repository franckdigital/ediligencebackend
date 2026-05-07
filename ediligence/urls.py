"""
URL configuration for ediligence project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path
from django.urls import include
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.http import JsonResponse

def api_home(request):
    """Page d'accueil de l'API"""
    return JsonResponse({
        'message': 'Bienvenue sur l\'API Ediligence',
        'version': '1.0',
        'endpoints': {
            # Administration
            'admin': '/admin/',
            'api_root': '/api/',
            
            # Authentification
            'auth_login': '/api/auth/login/',
            'auth_register': '/api/auth/register/',
            'auth_me': '/api/auth/me/',
            'auth_change_password': '/api/auth/change-password/',
            'token': '/api/token/',
            'token_refresh': '/api/token/refresh/',
            
            # Gestion des utilisateurs
            'users': '/api/users/',
            'directions': '/api/directions/',
            'services': '/api/services/',
            
            # Courriers et diligences
            'courriers': '/api/courriers/',
            'courrier_access': '/api/courrier-access/',
            'courrier_imputation': '/api/courrier-imputation/',
            'diligences': '/api/diligences/',
            'enhanced_diligences': '/api/enhanced-diligences/',
            'diligence_documents': '/api/diligence-documents/',
            'diligence_notifications': '/api/diligence-notifications/',
            
            # Congés et absences
            'demandes_conge': '/api/demandes-conge/',
            'demandes_absence': '/api/demandes-absence/',
            
            # Projets et tâches
            'activites': '/api/activites/',
            'domaines': '/api/domaines/',
            'projets': '/api/projets/',
            'taches': '/api/taches/',
            'commentaires': '/api/commentaires/',
            'fichiers': '/api/fichiers/',
            
            # Présences et bureaux
            'presences': '/api/presences/',
            'bureaux': '/api/bureaux/',
            'presence_stats': '/api/stats/presence/',
            
            # Notifications et permissions
            'notifications': '/api/notifications/',
            'role_permissions': '/api/role-permissions/',
            
            # Imputation et accès
            'imputation_files': '/api/imputation-files/',
            'imputation_access': '/api/imputation-access/',
            'user_diligence_comments': '/api/user-diligence-comments/',
            'user_diligence_instructions': '/api/user-diligence-instructions/',
            
            # Module Gestion de Projets
            'module_projets': '/api/projet/projets/',
            'module_taches': '/api/projet/taches/',
            'module_sous_taches': '/api/projet/sous-taches/',
            'module_commentaires_tache': '/api/projet/commentaires/',
            'module_pieces_jointes': '/api/projet/pieces-jointes/',
            'module_livrables': '/api/projet/livrables/',
            'module_validations': '/api/projet/validations/',
            'module_notifications_projet': '/api/projet/notifications/',
            'module_historique': '/api/projet/historique/',
            'module_dashboard': '/api/projet/dashboard/',
            'module_kanban': '/api/projet/taches/kanban/',
            'module_gantt': '/api/projet/projets/{id}/gantt/',
            'module_rapport_projet': '/api/projet/rapports/projet/{id}/',
            'module_rapport_agent': '/api/projet/rapports/agent/{id}/',
            'module_detecter_retards': '/api/projet/detecter-retards/',
            
        }
    })

urlpatterns = [
    path('', api_home, name='api_home'),
    path('admin/', admin.site.urls),
    path('api/', include('core.urls')),
    path('api/projet/', include('projet.urls')),
]

# Servir les fichiers média (dev + production via Django)
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]
