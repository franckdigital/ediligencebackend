#!/usr/bin/env python3
"""
Script pour déboguer la logique de géofencing
Usage: python debug_geofencing_logic.py
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

def debug_geofencing_logic():
    """Déboguer étape par étape la logique de géofencing"""
    print("🔍 DEBUG DE LA LOGIQUE DE GÉOFENCING")
    print("=" * 60)
    
    # 1. Vérifier la configuration
    settings = GeofenceSettings.objects.first()
    if not settings:
        print("❌ Aucune configuration trouvée")
        return
    
    print(f"⚙️  Configuration:")
    print(f"   Distance d'alerte: {settings.distance_alerte_metres}m")
    print(f"   Durée minimale: {settings.duree_minimale_hors_bureau_minutes} minutes")
    
    # 2. Récupérer l'utilisateur test
    try:
        user = User.objects.get(email='test@test.com')
        print(f"\n✅ Utilisateur: {user.username}")
        print(f"   Rôle: {user.profile.role}")
        print(f"   Actif: {user.is_active}")
    except User.DoesNotExist:
        print("❌ Utilisateur test@test.com non trouvé")
        return
    
    # 3. Vérifier le bureau
    bureau = Bureau.objects.first()
    if not bureau:
        print("❌ Aucun bureau trouvé")
        return
    
    print(f"\n🏢 Bureau: {bureau.nom}")
    print(f"   Coordonnées: {bureau.latitude_centre}, {bureau.longitude_centre}")
    print(f"   Rayon: {bureau.rayon_metres}m")
    
    # 4. Créer des positions de test avec calcul correct de dans_zone_autorisee
    now = timezone.now()
    
    # Modifier temporairement les heures de travail
    original_debut = settings.heure_debut_apres_midi
    original_fin = settings.heure_fin_apres_midi
    
    current_hour = now.hour
    settings.heure_debut_apres_midi = time(max(7, current_hour - 1), 0)
    settings.heure_fin_apres_midi = time(min(23, current_hour + 2), 0)
    settings.save()
    
    print(f"\n⏰ Heures de travail modifiées: {settings.heure_debut_apres_midi} - {settings.heure_fin_apres_midi}")
    
    # Position 1: Dans la zone (il y a 10 minutes)
    pos1_time = now - timedelta(minutes=10)
    pos1_lat = bureau.latitude_centre
    pos1_lon = bureau.longitude_centre
    
    pos1 = AgentLocation.objects.create(
        agent=user,
        latitude=pos1_lat,
        longitude=pos1_lon,
        timestamp=pos1_time,
        dans_zone_autorisee=True  # Dans la zone
    )
    
    distance1 = calculate_distance(
        float(pos1_lat), float(pos1_lon),
        float(bureau.latitude_centre), float(bureau.longitude_centre)
    )
    
    print(f"\n📍 Position 1 créée:")
    print(f"   Heure: {pos1_time.strftime('%H:%M:%S')}")
    print(f"   Distance: {distance1:.1f}m")
    print(f"   Dans zone: {pos1.dans_zone_autorisee}")
    
    # Position 2: Hors zone (il y a 8 minutes) - 300m du bureau
    pos2_time = now - timedelta(minutes=8)
    lat_offset = 0.003  # ~300m
    lon_offset = 0.003
    pos2_lat = float(bureau.latitude_centre) + lat_offset
    pos2_lon = float(bureau.longitude_centre) + lon_offset
    
    distance2 = calculate_distance(
        pos2_lat, pos2_lon,
        float(bureau.latitude_centre), float(bureau.longitude_centre)
    )
    
    dans_zone_2 = distance2 <= settings.distance_alerte_metres
    
    pos2 = AgentLocation.objects.create(
        agent=user,
        latitude=pos2_lat,
        longitude=pos2_lon,
        timestamp=pos2_time,
        dans_zone_autorisee=dans_zone_2
    )
    
    print(f"\n📍 Position 2 créée:")
    print(f"   Heure: {pos2_time.strftime('%H:%M:%S')}")
    print(f"   Distance: {distance2:.1f}m")
    print(f"   Dans zone: {pos2.dans_zone_autorisee}")
    
    # Position 3: Toujours hors zone (il y a 6 minutes)
    pos3_time = now - timedelta(minutes=6)
    
    pos3 = AgentLocation.objects.create(
        agent=user,
        latitude=pos2_lat,
        longitude=pos2_lon,
        timestamp=pos3_time,
        dans_zone_autorisee=dans_zone_2
    )
    
    print(f"\n📍 Position 3 créée:")
    print(f"   Heure: {pos3_time.strftime('%H:%M:%S')}")
    print(f"   Distance: {distance2:.1f}m")
    print(f"   Dans zone: {pos3.dans_zone_autorisee}")
    
    # Position 4: Encore hors zone (maintenant)
    pos4 = AgentLocation.objects.create(
        agent=user,
        latitude=pos2_lat,
        longitude=pos2_lon,
        timestamp=now,
        dans_zone_autorisee=dans_zone_2
    )
    
    print(f"\n📍 Position 4 créée:")
    print(f"   Heure: {now.strftime('%H:%M:%S')}")
    print(f"   Distance: {distance2:.1f}m")
    print(f"   Dans zone: {pos4.dans_zone_autorisee}")
    
    # 5. Simuler la logique de la tâche étape par étape
    print(f"\n🔍 SIMULATION DE LA LOGIQUE DE DÉTECTION")
    print("=" * 60)
    
    # Récupérer la dernière position (dans les 10 dernières minutes)
    recent_location = AgentLocation.objects.filter(
        agent=user,
        timestamp__gte=now - timedelta(minutes=10)
    ).order_by('-timestamp').first()
    
    if recent_location:
        print(f"✅ Position récente trouvée:")
        print(f"   Heure: {recent_location.timestamp.strftime('%H:%M:%S')}")
        print(f"   Dans zone: {recent_location.dans_zone_autorisee}")
        
        # Calculer la distance
        distance = calculate_distance(
            recent_location.latitude,
            recent_location.longitude,
            bureau.latitude_centre,
            bureau.longitude_centre
        )
        
        print(f"   Distance calculée: {distance:.1f}m")
        print(f"   Seuil d'alerte: {settings.distance_alerte_metres}m")
        print(f"   Hors zone: {distance > settings.distance_alerte_metres}")
        
        if distance > settings.distance_alerte_metres:
            print(f"\n🚨 Agent hors zone détecté!")
            
            # Vérifier la durée
            duree_minimale = timedelta(minutes=settings.duree_minimale_hors_bureau_minutes)
            time_threshold = now - duree_minimale
            
            print(f"   Durée minimale requise: {settings.duree_minimale_hors_bureau_minutes} minutes")
            print(f"   Seuil de temps: {time_threshold.strftime('%H:%M:%S')}")
            
            # Chercher la dernière position dans la zone
            last_inside_position = AgentLocation.objects.filter(
                agent=user,
                dans_zone_autorisee=True,
                timestamp__gte=time_threshold
            ).order_by('-timestamp').first()
            
            if last_inside_position:
                print(f"   ✅ Dernière position dans zone: {last_inside_position.timestamp.strftime('%H:%M:%S')}")
                print(f"   ❌ Agent pas assez longtemps hors zone")
            else:
                print(f"   ❌ Aucune position dans zone depuis {time_threshold.strftime('%H:%M:%S')}")
                
                # Chercher sans limite de temps
                last_inside_ever = AgentLocation.objects.filter(
                    agent=user,
                    dans_zone_autorisee=True
                ).order_by('-timestamp').first()
                
                if last_inside_ever:
                    duree_hors_zone = now - last_inside_ever.timestamp
                    print(f"   📊 Dernière position dans zone: {last_inside_ever.timestamp.strftime('%H:%M:%S')}")
                    print(f"   📊 Durée hors zone: {duree_hors_zone}")
                    
                    if duree_hors_zone >= duree_minimale:
                        print(f"   🚨 DEVRAIT CRÉER UNE ALERTE!")
                        
                        # Vérifier s'il y a déjà une alerte récente
                        recent_alert = GeofenceAlert.objects.filter(
                            agent=user,
                            bureau=bureau,
                            type_alerte='sortie_zone',
                            statut='active',
                            timestamp_alerte__gte=now - timedelta(hours=2)
                        ).exists()
                        
                        if recent_alert:
                            print(f"   ⚠️  Alerte récente déjà existante")
                        else:
                            print(f"   ✅ Aucune alerte récente - CRÉATION JUSTIFIÉE")
                    else:
                        print(f"   ❌ Durée insuffisante: {duree_hors_zone} < {duree_minimale}")
        else:
            print(f"\n✅ Agent dans la zone autorisée")
    else:
        print(f"❌ Aucune position récente trouvée")
    
    # 6. Nettoyer et restaurer
    print(f"\n🧹 Nettoyage...")
    pos1.delete()
    pos2.delete()
    pos3.delete()
    pos4.delete()
    
    settings.heure_debut_apres_midi = original_debut
    settings.heure_fin_apres_midi = original_fin
    settings.save()
    
    print(f"✅ Positions supprimées et heures restaurées")

if __name__ == "__main__":
    debug_geofencing_logic()
