#!/usr/bin/env python3
"""
Script pour tester le géofencing en forçant les heures de travail
Usage: python test_geofencing_now.py
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

def force_test_geofencing():
    """Tester le géofencing en créant une situation de test"""
    print("🧪 TEST FORCÉ DU GÉOFENCING")
    print("=" * 50)
    
    # 1. Vérifier la configuration
    settings = GeofenceSettings.objects.first()
    if not settings:
        print("❌ Aucune configuration trouvée")
        return
    
    print(f"⚙️  Configuration actuelle:")
    print(f"   Distance d'alerte: {settings.distance_alerte_metres}m")
    print(f"   Durée minimale: {settings.duree_minimale_hors_bureau_minutes} minutes")
    
    # 2. Récupérer l'utilisateur test
    try:
        user = User.objects.get(email='test@test.com')
        print(f"✅ Utilisateur: {user.username}")
    except User.DoesNotExist:
        print("❌ Utilisateur test@test.com non trouvé")
        return
    
    # 3. Récupérer le bureau
    bureau = Bureau.objects.first()
    if not bureau:
        print("❌ Aucun bureau trouvé")
        return
    
    print(f"✅ Bureau: {bureau.nom}")
    print(f"   Coordonnées: {bureau.latitude_centre}, {bureau.longitude_centre}")
    
    # 4. Créer des positions de test simulant une sortie prolongée
    now = timezone.now()
    
    # Position 1: Dans la zone (il y a 10 minutes)
    pos1_time = now - timedelta(minutes=10)
    pos1 = AgentLocation.objects.create(
        agent=user,
        latitude=bureau.latitude_centre,
        longitude=bureau.longitude_centre,
        timestamp=pos1_time,
        dans_zone_autorisee=True
    )
    print(f"📍 Position 1: {pos1_time.strftime('%H:%M:%S')} - DANS LA ZONE")
    
    # Position 2: Hors zone (il y a 8 minutes) - 300m du bureau
    pos2_time = now - timedelta(minutes=8)
    lat_offset = 0.003  # ~300m
    lon_offset = 0.003
    pos2_lat = float(bureau.latitude_centre) + lat_offset
    pos2_lon = float(bureau.longitude_centre) + lon_offset
    
    pos2 = AgentLocation.objects.create(
        agent=user,
        latitude=pos2_lat,
        longitude=pos2_lon,
        timestamp=pos2_time,
        dans_zone_autorisee=False
    )
    print(f"📍 Position 2: {pos2_time.strftime('%H:%M:%S')} - HORS ZONE (~300m)")
    
    # Position 3: Toujours hors zone (il y a 6 minutes)
    pos3_time = now - timedelta(minutes=6)
    pos3 = AgentLocation.objects.create(
        agent=user,
        latitude=pos2_lat,
        longitude=pos2_lon,
        timestamp=pos3_time,
        dans_zone_autorisee=False
    )
    print(f"📍 Position 3: {pos3_time.strftime('%H:%M:%S')} - TOUJOURS HORS ZONE")
    
    # Position 4: Encore hors zone (maintenant)
    pos4 = AgentLocation.objects.create(
        agent=user,
        latitude=pos2_lat,
        longitude=pos2_lon,
        timestamp=now,
        dans_zone_autorisee=False
    )
    print(f"📍 Position 4: {now.strftime('%H:%M:%S')} - ENCORE HORS ZONE")
    
    # 5. Modifier temporairement les heures de travail pour inclure maintenant
    original_debut = settings.heure_debut_apres_midi
    original_fin = settings.heure_fin_apres_midi
    
    current_hour = now.hour
    settings.heure_debut_apres_midi = time(max(7, current_hour - 1), 0)
    settings.heure_fin_apres_midi = time(min(23, current_hour + 2), 0)
    settings.save()
    
    print(f"\n⏰ Heures de travail temporaires:")
    print(f"   Modifiées: {settings.heure_debut_apres_midi} - {settings.heure_fin_apres_midi}")
    print(f"   (pour inclure l'heure actuelle: {now.strftime('%H:%M')})")
    
    # 6. Tester la tâche
    print(f"\n🚀 Exécution de la tâche de géofencing...")
    
    try:
        violations_count = check_geofence_violations()
        print(f"✅ Tâche exécutée")
        print(f"📊 Résultat: {violations_count or 0} nouvelles alertes créées")
        
        if violations_count and violations_count > 0:
            # Afficher les alertes créées
            recent_alerts = GeofenceAlert.objects.filter(
                agent=user,
                timestamp_alerte__gte=now - timedelta(minutes=2)
            ).order_by('-timestamp_alerte')
            
            print(f"\n🚨 Alertes créées:")
            for alert in recent_alerts:
                print(f"   🚨 {alert.agent.username}: {alert.distance_metres}m du bureau")
                print(f"      Type: {alert.type_alerte}")
                print(f"      Statut: {alert.statut}")
                print(f"      Heure: {alert.timestamp_alerte.strftime('%H:%M:%S')}")
        else:
            print(f"ℹ️  Aucune alerte créée - Vérifiez la logique de détection")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    
    # 7. Restaurer les heures de travail originales
    settings.heure_debut_apres_midi = original_debut
    settings.heure_fin_apres_midi = original_fin
    settings.save()
    print(f"\n🔄 Heures de travail restaurées: {original_debut} - {original_fin}")
    
    # 8. Nettoyer les positions de test
    print(f"\n🧹 Nettoyage des positions de test...")
    test_positions = [pos1, pos2, pos3, pos4]
    for pos in test_positions:
        pos.delete()
    print(f"✅ {len(test_positions)} positions de test supprimées")

def show_recent_alerts():
    """Afficher les alertes récentes"""
    print("\n🚨 ALERTES RÉCENTES")
    print("=" * 30)
    
    recent_alerts = GeofenceAlert.objects.filter(
        timestamp_alerte__gte=timezone.now() - timedelta(hours=2)
    ).order_by('-timestamp_alerte')
    
    if recent_alerts.exists():
        for alert in recent_alerts:
            print(f"🚨 {alert.agent.username}: {alert.distance_metres}m")
            print(f"   Bureau: {alert.bureau.nom}")
            print(f"   Type: {alert.type_alerte}")
            print(f"   Statut: {alert.statut}")
            print(f"   Heure: {alert.timestamp_alerte.strftime('%d/%m/%Y %H:%M:%S')}")
            print()
    else:
        print("ℹ️  Aucune alerte récente")

def main():
    """Fonction principale"""
    print("🔧 TEST GÉOFENCING FORCÉ")
    print("=" * 40)
    
    while True:
        print(f"\nOptions:")
        print("1. Test forcé avec positions simulées")
        print("2. Voir les alertes récentes")
        print("3. Quitter")
        
        choice = input("\nChoisissez (1-3): ").strip()
        
        if choice == '1':
            force_test_geofencing()
        elif choice == '2':
            show_recent_alerts()
        elif choice == '3':
            print("👋 Au revoir!")
            break
        else:
            print("❌ Option invalide")

if __name__ == "__main__":
    main()
