#!/usr/bin/env python3
"""
Script de diagnostic pour analyser le problème de géofencing de test@test.com
Usage: python debug_test_user_geofencing.py
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
    Bureau, UserProfile, Presence
)
from core.geofencing_utils import calculate_distance

def debug_test_user_geofencing():
    """Diagnostiquer le problème de géofencing pour test@test.com"""
    print("🔍 DIAGNOSTIC GÉOFENCING - test@test.com")
    print("=" * 70)
    
    # 1. Vérifier l'utilisateur
    try:
        user = User.objects.get(email='test@test.com')
        print(f"✅ Utilisateur trouvé: {user.username} ({user.email})")
        print(f"   Nom complet: {user.first_name} {user.last_name}")
        print(f"   Actif: {user.is_active}")
    except User.DoesNotExist:
        print("❌ Utilisateur test@test.com non trouvé")
        return
    
    # 2. Vérifier le profil utilisateur
    try:
        profile = user.profile
        print(f"✅ Profil trouvé: Rôle {profile.role}")
        print(f"   Service: {profile.service}")
        print(f"   Matricule: {profile.matricule}")
    except UserProfile.DoesNotExist:
        print("❌ Profil utilisateur non trouvé")
        return
    
    # 3. Vérifier les paramètres de géofencing
    settings = GeofenceSettings.objects.first()
    if settings:
        print(f"✅ Configuration géofencing trouvée:")
        print(f"   Distance d'alerte: {settings.distance_alerte_metres}m")
        print(f"   Durée minimale hors bureau: {settings.duree_minimale_hors_bureau_minutes} minutes")
        print(f"   Fréquence de vérification: {settings.frequence_verification_minutes} minutes")
        print(f"   Heures de travail: {settings.heure_debut_matin}-{settings.heure_fin_matin}, {settings.heure_debut_apres_midi}-{settings.heure_fin_apres_midi}")
    else:
        print("❌ Aucune configuration de géofencing trouvée")
        return
    
    # 4. Vérifier le bureau assigné
    bureau = None
    if profile.service:
        # Chercher un bureau pour le service
        bureau = Bureau.objects.filter(service=profile.service).first()
        if not bureau:
            # Prendre le bureau par défaut
            bureau = Bureau.objects.first()
    
    if bureau:
        print(f"✅ Bureau assigné: {bureau.nom}")
        print(f"   Coordonnées: {bureau.latitude_centre}, {bureau.longitude_centre}")
        print(f"   Rayon autorisé: {bureau.rayon_autorise_metres}m")
    else:
        print("❌ Aucun bureau assigné trouvé")
        return
    
    # 5. Analyser les positions d'hier autour de 16h12
    hier = timezone.now().date() - timedelta(days=1)
    debut_periode = timezone.make_aware(datetime.combine(hier, time(16, 0)))  # 16h00
    fin_periode = timezone.make_aware(datetime.combine(hier, time(16, 30)))   # 16h30
    
    print(f"\n📍 ANALYSE DES POSITIONS HIER ({hier}) entre 16h00 et 16h30:")
    print("-" * 70)
    
    positions = AgentLocation.objects.filter(
        agent=user,
        timestamp__gte=debut_periode,
        timestamp__lte=fin_periode
    ).order_by('timestamp')
    
    if positions.exists():
        print(f"✅ {positions.count()} positions trouvées dans la période")
        
        for i, pos in enumerate(positions):
            # Calculer la distance du bureau
            distance = calculate_distance(
                float(pos.latitude), float(pos.longitude),
                float(bureau.latitude_centre), float(bureau.longitude_centre)
            )
            
            hors_zone = distance > settings.distance_alerte_metres
            status_icon = "🔴" if hors_zone else "🟢"
            
            print(f"   {status_icon} {pos.timestamp.strftime('%H:%M:%S')} - "
                  f"Distance: {distance:.1f}m {'(HORS ZONE)' if hors_zone else '(dans zone)'}")
            
            if i == 0:
                print(f"      Coordonnées: {pos.latitude}, {pos.longitude}")
    else:
        print("❌ Aucune position trouvée dans cette période")
    
    # 6. Vérifier les positions sur une période plus large (15h30-17h00)
    print(f"\n📍 ANALYSE ÉTENDUE - HIER ({hier}) entre 15h30 et 17h00:")
    print("-" * 70)
    
    debut_etendu = timezone.make_aware(datetime.combine(hier, time(15, 30)))
    fin_etendu = timezone.make_aware(datetime.combine(hier, time(17, 0)))
    
    positions_etendues = AgentLocation.objects.filter(
        agent=user,
        timestamp__gte=debut_etendu,
        timestamp__lte=fin_etendu
    ).order_by('timestamp')
    
    if positions_etendues.exists():
        print(f"✅ {positions_etendues.count()} positions trouvées dans la période étendue")
        
        hors_zone_continue = []
        derniere_pos_dans_zone = None
        
        for pos in positions_etendues:
            distance = calculate_distance(
                float(pos.latitude), float(pos.longitude),
                float(bureau.latitude_centre), float(bureau.longitude_centre)
            )
            
            hors_zone = distance > settings.distance_alerte_metres
            
            if hors_zone:
                hors_zone_continue.append(pos)
            else:
                if hors_zone_continue:
                    # Analyser la période hors zone
                    duree_hors_zone = hors_zone_continue[-1].timestamp - hors_zone_continue[0].timestamp
                    print(f"   📊 Période hors zone détectée:")
                    print(f"      Début: {hors_zone_continue[0].timestamp.strftime('%H:%M:%S')}")
                    print(f"      Fin: {hors_zone_continue[-1].timestamp.strftime('%H:%M:%S')}")
                    print(f"      Durée: {duree_hors_zone}")
                    print(f"      Distance max: {max([calculate_distance(float(p.latitude), float(p.longitude), float(bureau.latitude_centre), float(bureau.longitude_centre)) for p in hors_zone_continue]):.1f}m")
                    
                    if duree_hors_zone >= timedelta(minutes=settings.duree_minimale_hors_bureau_minutes):
                        print(f"      ⚠️  DEVRAIT DÉCLENCHER UNE ALERTE (durée > {settings.duree_minimale_hors_bureau_minutes} min)")
                    else:
                        print(f"      ℹ️  Durée insuffisante pour alerte (< {settings.duree_minimale_hors_bureau_minutes} min)")
                    
                    hors_zone_continue = []
                
                derniere_pos_dans_zone = pos
    else:
        print("❌ Aucune position trouvée dans la période étendue")
    
    # 7. Vérifier les alertes existantes pour hier
    print(f"\n🚨 ALERTES GÉOFENCING POUR HIER ({hier}):")
    print("-" * 70)
    
    alertes_hier = GeofenceAlert.objects.filter(
        agent=user,
        date_detection=hier
    ).order_by('timestamp_alerte')
    
    if alertes_hier.exists():
        print(f"✅ {alertes_hier.count()} alerte(s) trouvée(s)")
        for alerte in alertes_hier:
            print(f"   🚨 {alerte.timestamp_alerte.strftime('%H:%M:%S')} - "
                  f"Type: {alerte.type_alerte}, Statut: {alerte.statut}")
            print(f"      Distance: {alerte.distance_metres}m, Bureau: {alerte.bureau.nom}")
    else:
        print("❌ Aucune alerte trouvée pour hier")
    
    # 8. Vérifier si les heures de travail étaient actives
    test_time = timezone.make_aware(datetime.combine(hier, time(16, 12)))
    if settings.is_heure_travail(test_time):
        print(f"\n✅ 16h12 était bien dans les heures de travail")
    else:
        print(f"\n❌ 16h12 n'était PAS dans les heures de travail configurées")
    
    # 9. Recommandations
    print(f"\n💡 RECOMMANDATIONS:")
    print("-" * 70)
    print("1. Vérifiez que la tâche Celery de géofencing s'exécute bien toutes les 5 minutes")
    print("2. Vérifiez les logs de la tâche check_geofence_violations")
    print("3. Assurez-vous que l'utilisateur a bien le rôle 'AGENT' pour être surveillé")
    print("4. Vérifiez que les coordonnées du bureau sont correctes")
    print("5. Testez manuellement la tâche avec: python manage.py shell -c \"from core.geofencing_tasks import check_geofence_violations; check_geofence_violations()\"")

if __name__ == "__main__":
    debug_test_user_geofencing()
