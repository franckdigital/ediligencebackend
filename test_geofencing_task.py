#!/usr/bin/env python3
"""
Script pour tester manuellement la tâche de géofencing
Usage: python test_geofencing_task.py
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

def test_geofence_task():
    """Tester la tâche de géofencing"""
    print("🧪 TEST DE LA TÂCHE DE GÉOFENCING")
    print("=" * 50)
    
    # Vérifier la configuration
    settings = GeofenceSettings.objects.first()
    if not settings:
        print("❌ Aucune configuration de géofencing trouvée")
        return
    
    print(f"⚙️  Configuration:")
    print(f"   Distance d'alerte: {settings.distance_alerte_metres}m")
    print(f"   Durée minimale: {settings.duree_minimale_hors_bureau_minutes} minutes")
    
    # Vérifier les bureaux
    bureaux = Bureau.objects.all()
    if not bureaux.exists():
        print("❌ Aucun bureau configuré")
        return
    
    print(f"\n🏢 Bureaux configurés:")
    for bureau in bureaux:
        print(f"   ✅ {bureau.nom}: {bureau.latitude_centre}, {bureau.longitude_centre} (rayon: {bureau.rayon_metres}m)")
    
    # Vérifier les agents
    agents = User.objects.filter(
        profile__role='AGENT',
        is_active=True
    ).select_related('profile')
    
    print(f"\n👥 Agents actifs: {agents.count()}")
    for agent in agents[:5]:  # Afficher seulement les 5 premiers
        print(f"   👤 {agent.username} ({agent.email})")
    
    # Vérifier les positions récentes
    now = timezone.now()
    recent_locations = AgentLocation.objects.filter(
        timestamp__gte=now - timedelta(minutes=15)
    ).order_by('-timestamp')
    
    print(f"\n📍 Positions récentes (15 dernières minutes): {recent_locations.count()}")
    for loc in recent_locations[:3]:  # Afficher seulement les 3 premières
        print(f"   📍 {loc.agent.username}: {loc.latitude}, {loc.longitude} à {loc.timestamp.strftime('%H:%M:%S')}")
    
    # Tester si on est dans les heures de travail
    if settings.is_heure_travail(now):
        print(f"\n✅ Heure actuelle ({now.strftime('%H:%M')}) est dans les heures de travail")
    else:
        print(f"\n⏰ Heure actuelle ({now.strftime('%H:%M')}) n'est PAS dans les heures de travail")
        print("   La tâche de géofencing ne s'exécutera pas")
    
    # Exécuter la tâche
    print(f"\n🚀 Exécution de la tâche check_geofence_violations...")
    
    try:
        violations_count = check_geofence_violations()
        print(f"✅ Tâche exécutée avec succès")
        print(f"📊 Résultat: {violations_count} nouvelles alertes créées")
        
        if violations_count > 0:
            # Afficher les alertes récentes
            recent_alerts = GeofenceAlert.objects.filter(
                timestamp_alerte__gte=now - timedelta(minutes=5)
            ).order_by('-timestamp_alerte')
            
            print(f"\n🚨 Alertes créées:")
            for alert in recent_alerts:
                print(f"   🚨 {alert.agent.username}: {alert.distance_metres}m du bureau {alert.bureau.nom}")
                print(f"      Type: {alert.type_alerte}, Statut: {alert.statut}")
                print(f"      Heure: {alert.timestamp_alerte.strftime('%H:%M:%S')}")
        else:
            print(f"ℹ️  Aucune violation détectée")
            
    except Exception as e:
        print(f"❌ Erreur lors de l'exécution: {e}")
        import traceback
        traceback.print_exc()

def create_test_violation():
    """Créer une violation de test pour l'utilisateur test@test.com"""
    print(f"\n🧪 CRÉATION D'UNE VIOLATION DE TEST")
    print("=" * 50)
    
    try:
        # Récupérer l'utilisateur test
        user = User.objects.get(email='test@test.com')
        print(f"✅ Utilisateur trouvé: {user.username}")
    except User.DoesNotExist:
        print("❌ Utilisateur test@test.com non trouvé")
        return
    
    # Récupérer le bureau
    bureau = Bureau.objects.first()
    if not bureau:
        print("❌ Aucun bureau trouvé")
        return
    
    print(f"✅ Bureau: {bureau.nom}")
    
    # Créer une position hors zone (300m du bureau)
    now = timezone.now()
    
    # Calculer une position à ~300m du bureau
    lat_offset = 0.003  # Approximativement 300m
    lon_offset = 0.003
    
    test_lat = float(bureau.latitude_centre) + lat_offset
    test_lon = float(bureau.longitude_centre) + lon_offset
    
    # Créer la position
    location = AgentLocation.objects.create(
        agent=user,
        latitude=test_lat,
        longitude=test_lon,
        timestamp=now,
        dans_zone_autorisee=False
    )
    
    print(f"📍 Position de test créée:")
    print(f"   Coordonnées: {test_lat}, {test_lon}")
    print(f"   Heure: {now.strftime('%H:%M:%S')}")
    print(f"   Distance estimée: ~300m du bureau")
    
    return location

def main():
    """Fonction principale"""
    print("🔧 OUTIL DE TEST GÉOFENCING")
    print("=" * 60)
    
    while True:
        print(f"\nOptions disponibles:")
        print("1. Tester la tâche de géofencing")
        print("2. Créer une violation de test")
        print("3. Voir les alertes récentes")
        print("4. Quitter")
        
        choice = input("\nChoisissez une option (1-4): ").strip()
        
        if choice == '1':
            test_geofence_task()
        elif choice == '2':
            create_test_violation()
        elif choice == '3':
            # Afficher les alertes récentes
            recent_alerts = GeofenceAlert.objects.filter(
                timestamp_alerte__gte=timezone.now() - timedelta(hours=1)
            ).order_by('-timestamp_alerte')
            
            print(f"\n🚨 Alertes de la dernière heure: {recent_alerts.count()}")
            for alert in recent_alerts:
                print(f"   🚨 {alert.agent.username}: {alert.distance_metres}m")
                print(f"      Bureau: {alert.bureau.nom}")
                print(f"      Heure: {alert.timestamp_alerte.strftime('%H:%M:%S')}")
                print(f"      Statut: {alert.statut}")
        elif choice == '4':
            print("👋 Au revoir!")
            break
        else:
            print("❌ Option invalide")

if __name__ == "__main__":
    main()
