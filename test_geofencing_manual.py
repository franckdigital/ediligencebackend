#!/usr/bin/env python3
"""
Script pour tester manuellement la détection de géofencing
Usage: python test_geofencing_manual.py
"""
import os
import sys
import django
from datetime import datetime, timedelta, time

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ediligencebackend.settings')
django.setup()

from django.utils import timezone
from django.contrib.auth.models import User
from core.models import (
    GeofenceSettings, AgentLocation, GeofenceAlert, 
    Bureau, UserProfile
)
from core.geofencing_tasks import check_geofence_violations

def create_test_scenario():
    """Créer un scénario de test pour simuler le problème"""
    print("🧪 CRÉATION D'UN SCÉNARIO DE TEST")
    print("=" * 50)
    
    # Récupérer l'utilisateur test
    try:
        user = User.objects.get(email='test@test.com')
        print(f"✅ Utilisateur: {user.username}")
    except User.DoesNotExist:
        print("❌ Utilisateur test@test.com non trouvé")
        return
    
    # Récupérer le bureau
    bureau = Bureau.objects.first()
    if not bureau:
        print("❌ Aucun bureau trouvé")
        return
    
    print(f"✅ Bureau: {bureau.nom}")
    print(f"   Coordonnées: {bureau.latitude_centre}, {bureau.longitude_centre}")
    
    # Créer des positions de test simulant le problème
    maintenant = timezone.now()
    
    # Position 1: Dans la zone (il y a 10 minutes)
    pos1_time = maintenant - timedelta(minutes=10)
    pos1 = AgentLocation.objects.create(
        agent=user,
        latitude=bureau.latitude_centre,  # Même position que le bureau
        longitude=bureau.longitude_centre,
        timestamp=pos1_time,
        dans_zone_autorisee=True
    )
    print(f"📍 Position 1 créée: {pos1_time.strftime('%H:%M:%S')} - DANS LA ZONE")
    
    # Position 2: Hors de la zone (il y a 8 minutes) - 300m du bureau
    pos2_time = maintenant - timedelta(minutes=8)
    # Décaler de ~300m (approximativement 0.003 degrés)
    pos2_lat = float(bureau.latitude_centre) + 0.003
    pos2_lon = float(bureau.longitude_centre) + 0.003
    
    pos2 = AgentLocation.objects.create(
        agent=user,
        latitude=pos2_lat,
        longitude=pos2_lon,
        timestamp=pos2_time,
        dans_zone_autorisee=False
    )
    print(f"📍 Position 2 créée: {pos2_time.strftime('%H:%M:%S')} - HORS ZONE (~300m)")
    
    # Position 3: Toujours hors de la zone (il y a 6 minutes)
    pos3_time = maintenant - timedelta(minutes=6)
    pos3 = AgentLocation.objects.create(
        agent=user,
        latitude=pos2_lat,
        longitude=pos2_lon,
        timestamp=pos3_time,
        dans_zone_autorisee=False
    )
    print(f"📍 Position 3 créée: {pos3_time.strftime('%H:%M:%S')} - TOUJOURS HORS ZONE")
    
    # Position 4: Toujours hors de la zone (maintenant)
    pos4 = AgentLocation.objects.create(
        agent=user,
        latitude=pos2_lat,
        longitude=pos2_lon,
        timestamp=maintenant,
        dans_zone_autorisee=False
    )
    print(f"📍 Position 4 créée: {maintenant.strftime('%H:%M:%S')} - TOUJOURS HORS ZONE")
    
    return user, bureau

def test_manual_detection():
    """Tester manuellement la détection"""
    print("\n🔍 TEST MANUEL DE LA DÉTECTION")
    print("=" * 50)
    
    # Vérifier la configuration
    settings = GeofenceSettings.objects.first()
    if not settings:
        print("❌ Aucune configuration de géofencing")
        return
    
    print(f"⚙️  Configuration:")
    print(f"   Distance d'alerte: {settings.distance_alerte_metres}m")
    print(f"   Durée minimale: {settings.duree_minimale_hors_bureau_minutes} minutes")
    
    # Exécuter la tâche de vérification
    print(f"\n🚀 Exécution de la tâche de vérification...")
    
    try:
        violations_count = check_geofence_violations()
        print(f"✅ Tâche exécutée: {violations_count} nouvelles alertes créées")
    except Exception as e:
        print(f"❌ Erreur lors de l'exécution: {e}")
        import traceback
        traceback.print_exc()
    
    # Vérifier les alertes créées
    print(f"\n📋 Vérification des alertes récentes:")
    recent_alerts = GeofenceAlert.objects.filter(
        timestamp_alerte__gte=timezone.now() - timedelta(minutes=5)
    ).order_by('-timestamp_alerte')
    
    if recent_alerts.exists():
        for alert in recent_alerts:
            print(f"🚨 Alerte: {alert.agent.username} - {alert.type_alerte}")
            print(f"   Distance: {alert.distance_metres}m")
            print(f"   Heure: {alert.timestamp_alerte.strftime('%H:%M:%S')}")
            print(f"   Statut: {alert.statut}")
    else:
        print("❌ Aucune alerte récente trouvée")

def cleanup_test_data():
    """Nettoyer les données de test"""
    print(f"\n🧹 NETTOYAGE DES DONNÉES DE TEST")
    print("=" * 50)
    
    try:
        user = User.objects.get(email='test@test.com')
        
        # Supprimer les positions de test récentes
        recent_positions = AgentLocation.objects.filter(
            agent=user,
            timestamp__gte=timezone.now() - timedelta(minutes=15)
        )
        count_pos = recent_positions.count()
        recent_positions.delete()
        print(f"🗑️  {count_pos} positions de test supprimées")
        
        # Supprimer les alertes de test récentes
        recent_alerts = GeofenceAlert.objects.filter(
            agent=user,
            timestamp_alerte__gte=timezone.now() - timedelta(minutes=15)
        )
        count_alerts = recent_alerts.count()
        recent_alerts.delete()
        print(f"🗑️  {count_alerts} alertes de test supprimées")
        
    except Exception as e:
        print(f"❌ Erreur lors du nettoyage: {e}")

def main():
    """Fonction principale"""
    print("🔧 OUTIL DE TEST GÉOFENCING MANUEL")
    print("=" * 60)
    
    while True:
        print(f"\nOptions disponibles:")
        print("1. Créer un scénario de test")
        print("2. Tester la détection manuelle")
        print("3. Nettoyer les données de test")
        print("4. Diagnostic complet")
        print("5. Quitter")
        
        choice = input("\nChoisissez une option (1-5): ").strip()
        
        if choice == '1':
            create_test_scenario()
        elif choice == '2':
            test_manual_detection()
        elif choice == '3':
            cleanup_test_data()
        elif choice == '4':
            # Exécuter le script de diagnostic
            from debug_test_user_geofencing import debug_test_user_geofencing
            debug_test_user_geofencing()
        elif choice == '5':
            print("👋 Au revoir!")
            break
        else:
            print("❌ Option invalide")

if __name__ == "__main__":
    main()
