#!/usr/bin/env python3
"""
Script pour déboguer les assignations de diligences
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ediligence.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from core.models import Diligence, UserProfile, Service
from django.contrib.auth.models import User

def debug_superieur_diligences():
    print("=== DEBUG SUPERIEUR DILIGENCES ===")
    
    # Trouver le service "Service Developpement d'Application"
    try:
        service = Service.objects.get(nom__icontains="Developpement")
        print(f"\nService trouvé: {service.nom} (ID: {service.id})")
        
        # Trouver tous les utilisateurs de ce service
        profiles = UserProfile.objects.filter(service=service).select_related('user')
        print(f"\nUtilisateurs du service:")
        
        superieur = None
        agents = []
        
        for profile in profiles:
            user = profile.user
            print(f"  - {user.username} ({user.first_name} {user.last_name}) - Rôle: {profile.role}")
            
            if profile.role == 'SUPERIEUR':
                superieur = user
            agents.append(user)
        
        if superieur:
            print(f"\nSupérieur identifié: {superieur.username}")
            
            # Vérifier les diligences des agents du service
            print(f"\nAgents du service: {[u.username for u in agents]}")
            
            # Diligences assignées aux agents du service
            diligences_agents = Diligence.objects.filter(agents__in=agents).distinct()
            print(f"\nDiligences assignées aux agents du service: {diligences_agents.count()}")
            
            for d in diligences_agents:
                agents_names = [a.username for a in d.agents.all()]
                ref = getattr(d, 'reference', None) or getattr(d, 'reference_courrier', 'N/A')
                print(f"  - Diligence {d.id}: {ref} -> Agents: {agents_names}")
            
            # Diligences du service via services_concernes
            diligences_service = Diligence.objects.filter(services_concernes=service).distinct()
            print(f"\nDiligences liées au service via services_concernes: {diligences_service.count()}")
            
            for d in diligences_service:
                ref = getattr(d, 'reference', None) or getattr(d, 'reference_courrier', 'N/A')
                print(f"  - Diligence {d.id}: {ref}")
            
            # Diligences du service via courrier
            diligences_courrier = Diligence.objects.filter(courrier__service=service).distinct()
            print(f"\nDiligences liées au service via courrier: {diligences_courrier.count()}")
            
            for d in diligences_courrier:
                ref = getattr(d, 'reference', None) or getattr(d, 'reference_courrier', 'N/A')
                print(f"  - Diligence {d.id}: {ref}")
                
        else:
            print("\nAucun supérieur trouvé dans ce service")
            
    except Service.DoesNotExist:
        print("Service 'Developpement' non trouvé")
        # Lister tous les services
        print("\nServices disponibles:")
        for s in Service.objects.all():
            print(f"  - {s.nom}")
    except Exception as e:
        print(f"Erreur: {e}")

if __name__ == "__main__":
    debug_superieur_diligences()
