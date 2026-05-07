#!/usr/bin/env python3
"""
Script pour déboguer étape par étape la tâche de géofencing
Usage: python debug_step_by_step.py
"""
import os
import sys
import django
from datetime import datetime, timedelta, time

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ediligence.settings')
django.setup()

from django.utils import timezone
from django.contrib.auth.models import User
from core.models import (
    GeofenceSettings, AgentLocation, GeofenceAlert, 
    Bureau, UserProfile
)
from core.geofencing_utils import calculate_distance

def debug_step_by_step():
    """Déboguer la tâche étape par étape avec tous les détails"""
    print("🔍 DEBUG ÉTAPE PAR ÉTAPE DE LA TÂCHE GÉOFENCING")
    print("=" * 70)
    
    # 1. Vérifier la configuration
    settings = GeofenceSettings.objects.first()
    if not settings:
        print("❌ Aucune configuration trouvée")
        return
    
    print(f"⚙️  Configuration GeofenceSettings:")
    print(f"   ID: {settings.id}")
    print(f"   Distance d'alerte: {settings.distance_alerte_metres}m")
    print(f"   Durée minimale: {settings.duree_minimale_hors_bureau_minutes} minutes")
    print(f"   Heures matin: {settings.heure_debut_matin} - {settings.heure_fin_matin}")
    print(f"   Heures après-midi: {settings.heure_debut_apres_midi} - {settings.heure_fin_apres_midi}")
    
    # 2. Vérifier l'heure actuelle
    now = timezone.now()
    print(f"\n⏰ Heure actuelle: {now.strftime('%H:%M:%S')}")
    print(f"   Dans heures de travail: {settings.is_heure_travail(now)}")
    
    if not settings.is_heure_travail(now):
        print("❌ Hors des heures de travail - La tâche ne s'exécutera pas")
        return
    
    # 3. Récupérer tous les agents actifs
    agents = User.objects.filter(
        profile__role='AGENT',
        is_active=True
    ).select_related('profile', 'agent_profile')
    
    print(f"\n👥 Agents actifs trouvés: {agents.count()}")
    for agent in agents:
        print(f"   👤 {agent.username} (ID: {agent.id}) - Rôle: {agent.profile.role}")
    
    # 4. Focus sur l'agent test
    try:
        test_agent = User.objects.get(email='test@test.com')
        print(f"\n🎯 Focus sur l'agent test: {test_agent.username}")
    except User.DoesNotExist:
        print("❌ Agent test@test.com non trouvé")
        return
    
    # 5. Vérifier les positions récentes
    recent_locations = AgentLocation.objects.filter(
        agent=test_agent,
        timestamp__gte=now - timedelta(minutes=10)
    ).order_by('-timestamp')
    
    print(f"\n📍 Positions récentes (10 dernières minutes): {recent_locations.count()}")
    for i, loc in enumerate(recent_locations):
        print(f"   {i+1}. {loc.timestamp.strftime('%H:%M:%S')} - Dans zone: {loc.dans_zone_autorisee}")
        print(f"      Coordonnées: {loc.latitude}, {loc.longitude}")
    
    if not recent_locations.exists():
        print("❌ Aucune position récente - L'agent ne sera pas traité")
        return
    
    recent_location = recent_locations.first()
    print(f"\n✅ Position la plus récente: {recent_location.timestamp.strftime('%H:%M:%S')}")
    
    # 6. Vérifier le bureau assigné
    bureau = None
    print(f"\n🏢 Recherche du bureau assigné...")
    
    # Vérifier agent_profile
    if hasattr(test_agent, 'agent_profile'):
        print(f"   Agent profile existe: {test_agent.agent_profile}")
        if test_agent.agent_profile and test_agent.agent_profile.bureau:
            bureau = test_agent.agent_profile.bureau
            print(f"   Bureau via agent_profile: {bureau.nom}")
    else:
        print(f"   Pas d'agent_profile")
    
    # Vérifier profile.service
    if not bureau and hasattr(test_agent, 'profile') and test_agent.profile.service:
        print(f"   Service via profile: {test_agent.profile.service}")
        bureau = Bureau.objects.first()
        print(f"   Bureau par défaut: {bureau.nom if bureau else 'Aucun'}")
    
    if not bureau:
        print("❌ Aucun bureau assigné - L'agent ne sera pas traité")
        return
    
    print(f"✅ Bureau assigné: {bureau.nom}")
    print(f"   Coordonnées: {bureau.latitude_centre}, {bureau.longitude_centre}")
    
    # 7. Calculer la distance
    distance = calculate_distance(
        recent_location.latitude,
        recent_location.longitude,
        bureau.latitude_centre,
        bureau.longitude_centre
    )
    
    print(f"\n📏 Calcul de distance:")
    print(f"   Position agent: {recent_location.latitude}, {recent_location.longitude}")
    print(f"   Position bureau: {bureau.latitude_centre}, {bureau.longitude_centre}")
    print(f"   Distance calculée: {distance:.1f}m")
    print(f"   Seuil d'alerte: {settings.distance_alerte_metres}m")
    print(f"   Hors zone: {distance > settings.distance_alerte_metres}")
    
    if distance <= settings.distance_alerte_metres:
        print("✅ Agent dans la zone - Pas d'alerte nécessaire")
        return
    
    # 8. Vérifier la durée hors zone
    print(f"\n⏱️  Vérification de la durée hors zone...")
    duree_minimale = timedelta(minutes=settings.duree_minimale_hors_bureau_minutes)
    print(f"   Durée minimale requise: {duree_minimale}")
    
    # Chercher la dernière position dans la zone
    last_inside_position = AgentLocation.objects.filter(
        agent=test_agent,
        dans_zone_autorisee=True
    ).order_by('-timestamp').first()
    
    if not last_inside_position:
        print("❌ Aucune position 'dans zone' trouvée - Pas d'alerte possible")
        return
    
    print(f"✅ Dernière position dans zone: {last_inside_position.timestamp.strftime('%H:%M:%S')}")
    
    duree_hors_zone = now - last_inside_position.timestamp
    print(f"   Durée hors zone: {duree_hors_zone}")
    print(f"   Condition remplie: {duree_hors_zone >= duree_minimale}")
    
    if duree_hors_zone < duree_minimale:
        print("❌ Durée insuffisante - Pas d'alerte")
        return
    
    # 9. Vérifier les alertes existantes
    print(f"\n🚨 Vérification des alertes existantes...")
    recent_alert = GeofenceAlert.objects.filter(
        agent=test_agent,
        bureau=bureau,
        type_alerte='sortie_zone',
        statut='active',
        timestamp_alerte__gte=now - timedelta(hours=2)
    )
    
    print(f"   Alertes récentes (2h): {recent_alert.count()}")
    for alert in recent_alert:
        print(f"   🚨 {alert.timestamp_alerte.strftime('%H:%M:%S')} - {alert.statut}")
    
    if recent_alert.exists():
        print("❌ Alerte récente déjà existante - Pas de nouvelle alerte")
        return
    
    # 10. Toutes les conditions sont remplies
    print(f"\n✅ TOUTES LES CONDITIONS SONT REMPLIES!")
    print(f"   ✅ Agent hors zone: {distance:.1f}m > {settings.distance_alerte_metres}m")
    print(f"   ✅ Durée suffisante: {duree_hors_zone} >= {duree_minimale}")
    print(f"   ✅ Pas d'alerte récente")
    print(f"   ✅ Dans les heures de travail")
    
    print(f"\n🚨 UNE ALERTE DEVRAIT ÊTRE CRÉÉE!")
    
    # 11. Simuler la création d'alerte
    print(f"\n🧪 Simulation de création d'alerte...")
    try:
        alert = GeofenceAlert.objects.create(
            agent=test_agent,
            bureau=bureau,
            type_alerte='sortie_zone',
            latitude_agent=recent_location.latitude,
            longitude_agent=recent_location.longitude,
            distance_metres=int(distance),
            en_heures_travail=True
        )
        print(f"✅ Alerte créée avec succès!")
        print(f"   ID: {alert.id}")
        print(f"   Agent: {alert.agent.username}")
        print(f"   Distance: {alert.distance_metres}m")
        print(f"   Heure: {alert.timestamp_alerte.strftime('%H:%M:%S')}")
        
        # Supprimer l'alerte de test
        alert.delete()
        print(f"🧹 Alerte de test supprimée")
        
    except Exception as e:
        print(f"❌ Erreur lors de la création d'alerte: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_step_by_step()
