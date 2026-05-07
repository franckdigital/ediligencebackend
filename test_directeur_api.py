import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ediligence.settings')
django.setup()

from django.contrib.auth.models import User
from core.views import DiligenceViewSet
from django.test import RequestFactory
from rest_framework.request import Request
import traceback

try:
    # Obtenir l'utilisateur directeur
    directeur = User.objects.get(username='alainfranck')
    print(f"Test pour directeur: {directeur.username}")
    print(f"Rôle: {directeur.profile.role}")
    print(f"Direction: {directeur.profile.service.direction}")
    
    # Créer une requête mock avec query_params
    factory = RequestFactory()
    django_request = factory.get('/api/diligences/')
    django_request.user = directeur
    
    # Convertir en Request DRF
    request = Request(django_request)
    
    # Créer l'instance du viewset
    viewset = DiligenceViewSet()
    viewset.request = request
    viewset.format_kwarg = None
    
    print(f"\nTest de DiligenceViewSet.get_queryset() pour DIRECTEUR...")
    
    # Appeler get_queryset
    queryset = viewset.get_queryset()
    print(f"Queryset retourné avec succès: {queryset.count()} diligences")
    
    # Évaluer le queryset
    diligences = list(queryset)
    print(f"Évaluation du queryset réussie: {len(diligences)} diligences")
    
    # Afficher les détails
    for diligence in diligences:
        print(f"- Diligence {diligence.id}: {diligence.objet[:50]}...")
        
except Exception as e:
    print(f"Erreur: {e}")
    traceback.print_exc()
