#!/usr/bin/env python3
"""
Script pour tester la correction de géofencing
Usage: python test_fix_geofencing.py
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
from core.geofencing_tasks import check_geofence_violations
from core.geofencing_utils import calculate_distance

def test_corrected_logic():
    """Tester la logique corrigée"""
    print("🧪 TEST DE LA LOGIQUE CORRIGÉE")
    print("=" * 50)
    
    # 1. Configuration
    settings = GeofenceSettings.objects.first()
    user = User.objects.get(email='test@test.com')
    bureau = Bureau.objects.first()
    
    print(f"✅ Configuration: {settings.distance_alerte_metres}m, {settings.duree_minimale_hors_bureau_minutes} min")
    print(f"✅ Utilisateur: {user.username}")
    print(f"✅ Bureau: {bureau.nom}")
    
    # 2. Modifier heures de travail temporairement
    now = timezone.now()
    original_debut = settings.heure_debut_apres_midi
    original_fin = settings.heure_fin_apres_midi
    
    current_hour = now.hour
    settings.heure_debut_apres_midi = time(max(7, current_hour - 1), 0)
    settings.heure_fin_apres_midi = time(min(23, current_hour + 2), 0)
    settings.save()
    
    print(f"⏰ Heures modifiées: {settings.heure_debut_apres_midi} - {settings.heure_fin_apres_midi}")
    
    # 3. Créer positions de test avec logique correcte
    
    # Position dans zone (il y a 8 minutes)
    pos1_time = now - timedelta(minutes=8)
    pos1 = AgentLocation.objects.create(
        agent=user,
        latitude=bureau.latitude_centre,
        longitude=bureau.longitude_centre,
        timestamp=pos1_time,
        dans_zone_autorisee=True
    )
    print(f"📍 Position 1: {pos1_time.strftime('%H:%M:%S')} - DANS ZONE")
    
    # Position hors zone (il y a 6 minutes) - début de sortie
    pos2_time = now - timedelta(minutes=6)
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
    
    # Position actuelle (maintenant) - toujours hors zone
    pos3 = AgentLocation.objects.create(
        agent=user,
        latitude=pos2_lat,
        longitude=pos2_lon,
        timestamp=now,
        dans_zone_autorisee=False
    )
    print(f"📍 Position 3: {now.strftime('%H:%M:%S')} - TOUJOURS HORS ZONE")
    
    # 4. Calculer la durée hors zone
    duree_hors_zone = now - pos1_time
    duree_minimale = timedelta(minutes=settings.duree_minimale_hors_bureau_minutes)
    
    print(f"\n📊 Analyse:")
    print(f"   Dernière position dans zone: {pos1_time.strftime('%H:%M:%S')}")
    print(f"   Durée hors zone: {duree_hors_zone}")
    print(f"   Durée minimale requise: {duree_minimale}")
    print(f"   Devrait créer alerte: {duree_hors_zone >= duree_minimale}")
    
    # 5. Tester la tâche
    print(f"\n🚀 Test de la tâche corrigée...")
    
    try:
        violations_count = check_geofence_violations()
        print(f"✅ Tâche exécutée")
        print(f"📊 Résultat: {violations_count or 0} nouvelles alertes créées")
        
        if violations_count and violations_count > 0:
            # Vérifier les alertes créées
            recent_alerts = GeofenceAlert.objects.filter(
                agent=user,
                timestamp_alerte__gte=now - timedelta(minutes=2)
            ).order_by('-timestamp_alerte')
            
            print(f"\n🚨 Alertes créées:")
            for alert in recent_alerts:
                print(f"   🚨 {alert.agent.username}: {alert.distance_metres}m")
                print(f"      Type: {alert.type_alerte}")
                print(f"      Statut: {alert.statut}")
                print(f"      Heure: {alert.timestamp_alerte.strftime('%H:%M:%S')}")
                
            print(f"\n✅ SUCCESS! La logique fonctionne maintenant!")
        else:
            print(f"\n❌ Toujours aucune alerte créée - Problème persistant")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    
    # 6. Nettoyer
    print(f"\n🧹 Nettoyage...")
    pos1.delete()
    pos2.delete()
    pos3.delete()
    
    # Supprimer les alertes de test
    test_alerts = GeofenceAlert.objects.filter(
        agent=user,
        timestamp_alerte__gte=now - timedelta(minutes=5)
    )
    alert_count = test_alerts.count()
    test_alerts.delete()
    
    # Restaurer heures
    settings.heure_debut_apres_midi = original_debut
    settings.heure_fin_apres_midi = original_fin
    settings.save()
    
    print(f"✅ {alert_count} alertes de test supprimées")
    print(f"✅ Heures restaurées")

if __name__ == "__main__":
    test_corrected_logic()
