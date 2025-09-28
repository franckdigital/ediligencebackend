#!/usr/bin/env python3
"""
Script pour déboguer en temps réel les diligences visibles par ange alain
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ediligence.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib.auth.models import User
from core.models import Diligence, ImputationAccess

def debug_ange_alain():
    print("=== DEBUG TEMPS RÉEL - ANGE ALAIN ===\n")
    
    # Récupérer ange alain
    try:
        ange_alain = User.objects.get(username='angealain')
        print(f"Utilisateur: {ange_alain.username} (ID:{ange_alain.id})")
        print(f"Role: {ange_alain.profile.role if hasattr(ange_alain, 'profile') else 'NO_PROFILE'}")
    except User.DoesNotExist:
        print("Utilisateur 'angealain' non trouvé")
        return
    
    print(f"\n=== SIMULATION DU FILTRAGE BACKEND ===")
    
    # Simuler le filtrage du backend
    base_qs = Diligence.objects.select_related(
        'courrier',
        'courrier__service',
        'courrier__service__direction',
        'direction'
    ).prefetch_related(
        'agents',
        'services_concernes',
        'services_concernes__direction'
    ).all().order_by('-created_at')
    
    print(f"Total diligences dans la base: {base_qs.count()}")
    
    # Diligences assignées
    assigned_qs = base_qs.filter(agents=ange_alain)
    print(f"Diligences assignées à ange alain: {assigned_qs.count()}")
    
    # Diligences avec ImputationAccess
    imputation_access_qs = base_qs.filter(imputation_access__user=ange_alain)
    print(f"Diligences avec ImputationAccess pour ange alain: {imputation_access_qs.count()}")
    
    # Résultat final selon la logique actuelle
    role = ange_alain.profile.role if hasattr(ange_alain, 'profile') else 'UNKNOWN'
    if role == 'ADMIN':
        final_qs = (base_qs | imputation_access_qs).distinct()
        print(f"ADMIN - Toutes les diligences: {final_qs.count()}")
    else:
        final_qs = assigned_qs
        print(f"{role} - Seulement assignées: {final_qs.count()}")
    
    print(f"\n=== DILIGENCES FINALES POUR ANGE ALAIN ===")
    for diligence in final_qs:
        agents_names = [agent.username for agent in diligence.agents.all()]
        print(f"Diligence #{diligence.id} - {diligence.reference_courrier}")
        print(f"  Agents: {', '.join(agents_names) if agents_names else 'Aucun'}")
    
    print(f"\n=== VÉRIFICATION IMPUTATION ACCESS ===")
    imputation_accesses = ImputationAccess.objects.filter(user=ange_alain)
    print(f"Nombre d'ImputationAccess pour ange alain: {imputation_accesses.count()}")
    for access in imputation_accesses:
        print(f"  - Diligence #{access.diligence.id} ({access.diligence.reference_courrier}) - Type: {access.access_type}")

if __name__ == "__main__":
    debug_ange_alain()
