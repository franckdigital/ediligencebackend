#!/usr/bin/env python3
"""
Diagnostic des assignations de bureau pour tous les agents
"""
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ediligencebackend.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import Agent, Bureau, Presence
from datetime import date

def diagnostic_bureaux():
    """Diagnostic des bureaux et assignations"""
    
    print("=" * 60)
    print("DIAGNOSTIC BUREAUX ET AGENTS")
    print("=" * 60)
    
    # 1. Lister tous les bureaux
    print("\n1. BUREAUX DISPONIBLES")
    print("-" * 30)
    
    bureaux = Bureau.objects.all()
    print(f"Nombre total de bureaux: {bureaux.count()}")
    
    for bureau in bureaux:
        print(f"   ID: {bureau.id} - {bureau.nom}")
        print(f"      Coordonnées: {bureau.latitude_centre}, {bureau.longitude_centre}")
        print(f"      Rayon: {bureau.rayon_metres}m")
        print(f"      Actif: {getattr(bureau, 'actif', 'N/A')}")
    
    # 2. Lister tous les agents et leurs bureaux
    print(f"\n2. AGENTS ET LEURS BUREAUX")
    print("-" * 30)
    
    agents = Agent.objects.all()
    print(f"Nombre total d'agents: {agents.count()}")
    
    agents_sans_bureau = []
    agents_avec_bureau = []
    
    for agent in agents:
        if agent.bureau:
            agents_avec_bureau.append(agent)
            print(f"✅ {agent.user.username} -> Bureau: {agent.bureau.nom}")
        else:
            agents_sans_bureau.append(agent)
            print(f"❌ {agent.user.username} -> AUCUN BUREAU")
    
    print(f"\nRésumé:")
    print(f"   Agents avec bureau: {len(agents_avec_bureau)}")
    print(f"   Agents sans bureau: {len(agents_sans_bureau)}")
    
    # 3. Vérifier les présences d'aujourd'hui
    print(f"\n3. PRESENCES AUJOURD'HUI")
    print("-" * 30)
    
    today = date.today()
    presences = Presence.objects.filter(date_presence=today)
    print(f"Présences aujourd'hui: {presences.count()}")
    
    for presence in presences:
        agent = presence.agent
        bureau_info = f"Bureau: {agent.bureau.nom}" if agent.bureau else "AUCUN BUREAU"
        print(f"   {agent.user.username} - {presence.statut} - {bureau_info}")
    
    return agents_sans_bureau, bureaux

def corriger_assignations_bureau():
    """Corriger les assignations de bureau manquantes"""
    
    print(f"\n4. CORRECTION DES ASSIGNATIONS")
    print("-" * 30)
    
    # Récupérer le bureau principal ou le premier bureau
    bureau_principal = Bureau.objects.filter(nom__icontains='Principal').first()
    if not bureau_principal:
        bureau_principal = Bureau.objects.first()
    
    if not bureau_principal:
        print("❌ ERREUR: Aucun bureau disponible pour l'assignation")
        return False
    
    print(f"Bureau à assigner: {bureau_principal.nom}")
    
    # Assigner le bureau à tous les agents sans bureau
    agents_sans_bureau = Agent.objects.filter(bureau__isnull=True)
    
    if agents_sans_bureau.exists():
        print(f"Assignation du bureau '{bureau_principal.nom}' à {agents_sans_bureau.count()} agents...")
        
        for agent in agents_sans_bureau:
            agent.bureau = bureau_principal
            agent.save()
            print(f"   ✅ {agent.user.username} -> {bureau_principal.nom}")
        
        print(f"✅ Assignation terminée pour {agents_sans_bureau.count()} agents")
        return True
    else:
        print("✅ Tous les agents ont déjà un bureau assigné")
        return True

def main():
    agents_sans_bureau, bureaux = diagnostic_bureaux()
    
    if agents_sans_bureau:
        print(f"\n🔧 CORRECTION NÉCESSAIRE")
        print(f"   {len(agents_sans_bureau)} agents sans bureau détectés")
        
        # Proposer la correction
        if bureaux.exists():
            corriger_assignations_bureau()
            
            # Vérifier après correction
            print(f"\n5. VERIFICATION APRES CORRECTION")
            print("-" * 30)
            agents_sans_bureau_apres = Agent.objects.filter(bureau__isnull=True)
            if agents_sans_bureau_apres.exists():
                print(f"❌ {agents_sans_bureau_apres.count()} agents encore sans bureau")
            else:
                print("✅ Tous les agents ont maintenant un bureau assigné")
        else:
            print("❌ Aucun bureau disponible pour l'assignation")
    else:
        print(f"\n✅ TOUS LES AGENTS ONT UN BUREAU ASSIGNÉ")

if __name__ == "__main__":
    main()
