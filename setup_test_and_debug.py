#!/usr/bin/env python3
"""
Script pour créer des positions de test et déboguer
Usage: python setup_test_and_debug.py
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

def setup_test_scenario():
    """Créer un scénario de test complet"""
    print("🧪 CRÉATION DU SCÉNARIO DE TEST")
    print("=" * 50)
    
    # 1. Configuration
    settings = GeofenceSettings.objects.first()
    user = User.objects.get(email='test@test.com')
    bureau = Bureau.objects.first()
    
    # 2. Modifier heures de travail
    now = timezone.now()
    original_debut = settings.heure_debut_apres_midi
    original_fin = settings.heure_fin_apres_midi
    
    current_hour = now.hour
    settings.heure_debut_apres_midi = time(max(7, current_hour - 1), 0)
    settings.heure_fin_apres_midi = time(min(23, current_hour + 2), 0)
    settings.save()
    
    print(f"⏰ Heures modifiées: {settings.heure_debut_apres_midi} - {settings.heure_fin_apres_midi}")
    
    # 3. Nettoyer les anciennes positions
    old_positions = AgentLocation.objects.filter(
        agent=user,
        timestamp__gte=now - timedelta(hours=1)
    )
    old_count = old_positions.count()
    old_positions.delete()
    print(f"🧹 {old_count} anciennes positions supprimées")
    
    # 4. Créer positions de test
    
    # Position dans zone (il y a 10 minutes)
    pos1_time = now - timedelta(minutes=10)
    pos1 = AgentLocation.objects.create(
        agent=user,
        latitude=bureau.latitude_centre,
        longitude=bureau.longitude_centre,
        timestamp=pos1_time,
        dans_zone_autorisee=True
    )
    print(f"📍 Position 1: {pos1_time.strftime('%H:%M:%S')} - DANS ZONE (0m)")
    
    # Position hors zone (il y a 8 minutes)
    pos2_time = now - timedelta(minutes=8)
    lat_offset = 0.003  # ~300m
    lon_offset = 0.003
    pos2_lat = float(bureau.latitude_centre) + lat_offset
    pos2_lon = float(bureau.longitude_centre) + lon_offset
    
    distance2 = calculate_distance(
        pos2_lat, pos2_lon,
        float(bureau.latitude_centre), float(bureau.longitude_centre)
    )
    
    pos2 = AgentLocation.objects.create(
        agent=user,
        latitude=pos2_lat,
        longitude=pos2_lon,
        timestamp=pos2_time,
        dans_zone_autorisee=False
    )
    print(f"📍 Position 2: {pos2_time.strftime('%H:%M:%S')} - HORS ZONE ({distance2:.1f}m)")
    
    # Position actuelle (maintenant)
    pos3 = AgentLocation.objects.create(
        agent=user,
        latitude=pos2_lat,
        longitude=pos2_lon,
        timestamp=now,
        dans_zone_autorisee=False
    )
    print(f"📍 Position 3: {now.strftime('%H:%M:%S')} - TOUJOURS HORS ZONE ({distance2:.1f}m)")
    
    # 5. Vérifier la logique
    duree_hors_zone = now - pos1_time
    duree_minimale = timedelta(minutes=settings.duree_minimale_hors_bureau_minutes)
    
    print(f"\n📊 Vérification:")
    print(f"   Durée hors zone: {duree_hors_zone}")
    print(f"   Durée minimale: {duree_minimale}")
    print(f"   Devrait créer alerte: {duree_hors_zone >= duree_minimale}")
    
    return settings, original_debut, original_fin, [pos1, pos2, pos3]

def cleanup_test(settings, original_debut, original_fin, positions):
    """Nettoyer le test"""
    print(f"\n🧹 Nettoyage...")
    
    # Supprimer positions
    for pos in positions:
        pos.delete()
    print(f"✅ {len(positions)} positions supprimées")
    
    # Restaurer heures
    settings.heure_debut_apres_midi = original_debut
    settings.heure_fin_apres_midi = original_fin
    settings.save()
    print(f"✅ Heures restaurées")
    
    # Supprimer alertes de test
    user = User.objects.get(email='test@test.com')
    test_alerts = GeofenceAlert.objects.filter(
        agent=user,
        timestamp_alerte__gte=timezone.now() - timedelta(minutes=15)
    )
    alert_count = test_alerts.count()
    test_alerts.delete()
    print(f"✅ {alert_count} alertes de test supprimées")

def main():
    """Fonction principale"""
    print("🔧 SETUP TEST ET DEBUG GÉOFENCING")
    print("=" * 60)
    
    try:
        # 1. Créer le scénario de test
        settings, original_debut, original_fin, positions = setup_test_scenario()
        
        # 2. Exécuter le debug détaillé
        print(f"\n" + "="*70)
        from debug_step_by_step import debug_step_by_step
        debug_step_by_step()
        
        # 3. Nettoyer
        cleanup_test(settings, original_debut, original_fin, positions)
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
