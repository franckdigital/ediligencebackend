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
    # Test avec franck (ADMIN)
    franck = User.objects.get(username='franck')
    print(f"Test pour utilisateur: {franck.username} (ID: {franck.id})")
    print(f"Rôle: {franck.profile.role}")
    
    # Créer une requête mock
    factory = RequestFactory()
    django_request = factory.get('/api/diligences/')
    django_request.user = franck
    
    # Convertir en Request DRF
    request = Request(django_request)
    
    # Créer l'instance du viewset
    viewset = DiligenceViewSet()
    viewset.request = request
    viewset.format_kwarg = None
    
    print(f"\nTest de DiligenceViewSet.get_queryset() pour ADMIN...")
    
    # Appeler get_queryset
    queryset = viewset.get_queryset()
    print(f"Queryset retourné avec succès: {queryset.count()} diligences")
    
    # Test avec directeur
    print(f"\n" + "="*50)
    directeur = User.objects.get(username='alainfranck')
    print(f"Test pour directeur: {directeur.username} (ID: {directeur.id})")
    print(f"Rôle: {directeur.profile.role}")
    
    django_request.user = directeur
    request = Request(django_request)
    viewset.request = request
    
    queryset = viewset.get_queryset()
    print(f"Queryset directeur retourné: {queryset.count()} diligences")
    
    # Évaluer le queryset
    diligences = list(queryset)
    print(f"Évaluation réussie: {len(diligences)} diligences")
        
except Exception as e:
    print(f"Erreur: {e}")
    traceback.print_exc()
