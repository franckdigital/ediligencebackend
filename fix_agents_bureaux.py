#!/usr/bin/env python3
"""
Script pour corriger l'assignation des bureaux aux agents
Usage: python manage.py shell < fix_agents_bureaux.py
"""
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ediligencebackend.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import Agent, Bureau

def fix_agents_bureaux():
    """Corriger l'assignation des bureaux pour tous les agents"""
    
    print("🔧 CORRECTION DES ASSIGNATIONS DE BUREAU")
    print("=" * 50)
    
    # 1. Vérifier les bureaux disponibles
    bureaux = Bureau.objects.all()
    if not bureaux.exists():
        print("❌ ERREUR: Aucun bureau disponible")
        return False
    
    # Choisir le bureau principal ou le premier
    bureau_principal = Bureau.objects.filter(nom__icontains='Principal').first()
    if not bureau_principal:
        bureau_principal = bureaux.first()
    
    print(f"📍 Bureau à assigner: {bureau_principal.nom}")
    print(f"   Coordonnées: {bureau_principal.latitude_centre}, {bureau_principal.longitude_centre}")
    print(f"   Rayon: {bureau_principal.rayon_metres}m")
    
    # 2. Trouver les agents sans bureau
    agents_sans_bureau = Agent.objects.filter(bureau__isnull=True)
    
    if not agents_sans_bureau.exists():
        print("✅ Tous les agents ont déjà un bureau assigné")
        return True
    
    print(f"\n📊 Agents à corriger: {agents_sans_bureau.count()}")
    
    # 3. Assigner le bureau à tous les agents sans bureau
    corriges = 0
    for agent in agents_sans_bureau:
        agent.bureau = bureau_principal
        agent.save()
        print(f"   ✅ {agent.user.username} -> {bureau_principal.nom}")
        corriges += 1
    
    print(f"\n🎉 CORRECTION TERMINÉE")
    print(f"   Agents corrigés: {corriges}")
    
    # 4. Vérification finale
    agents_sans_bureau_final = Agent.objects.filter(bureau__isnull=True)
    if agents_sans_bureau_final.exists():
        print(f"   ⚠️ {agents_sans_bureau_final.count()} agents encore sans bureau")
        return False
    else:
        print("   ✅ Tous les agents ont maintenant un bureau")
        return True

def verification_finale():
    """Vérification finale de tous les agents"""
    
    print(f"\n📋 VÉRIFICATION FINALE")
    print("-" * 30)
    
    agents = Agent.objects.all()
    for agent in agents:
        if agent.bureau:
            print(f"✅ {agent.user.username:15} -> {agent.bureau.nom}")
        else:
            print(f"❌ {agent.user.username:15} -> AUCUN BUREAU")
    
    # Statistiques
    total_agents = agents.count()
    agents_avec_bureau = agents.filter(bureau__isnull=False).count()
    
    print(f"\n📊 STATISTIQUES:")
    print(f"   Total agents: {total_agents}")
    print(f"   Avec bureau: {agents_avec_bureau}")
    print(f"   Sans bureau: {total_agents - agents_avec_bureau}")
    
    if agents_avec_bureau == total_agents:
        print("🎯 SUCCÈS: Tous les agents ont un bureau !")
    else:
        print("⚠️ ATTENTION: Certains agents n'ont pas de bureau")

def main():
    success = fix_agents_bureaux()
    verification_finale()
    
    if success:
        print(f"\n🚀 PROCHAINES ÉTAPES:")
        print("1. Redémarrer Celery pour prendre en compte les changements")
        print("2. Tester le pointage avec angealain")
        print("3. Vérifier la détection de sortie")
    else:
        print(f"\n❌ CORRECTION INCOMPLÈTE - Vérifier manuellement")

if __name__ == "__main__":
    main()
