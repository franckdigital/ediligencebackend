#!/usr/bin/env python3
"""
Script de diagnostic pour le système de géofencing
Usage: python debug_geofencing.py
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
from core.models import Presence, Agent, Bureau, AgentLocation
from core.geofencing_utils import calculate_distance

def debug_franck_alain():
    """Diagnostiquer le problème de franck.alain"""
    print("🔍 DIAGNOSTIC GÉOFENCING - franck.alain")
    print("=" * 60)
    
    # 1. Vérifier l'utilisateur
    try:
        user = User.objects.get(username='franck.alain')
        print(f"✅ Utilisateur trouvé: {user.username}")
    except User.DoesNotExist:
        print("❌ Utilisateur franck.alain non trouvé")
        return
    
    # 2. Vérifier l'agent
    try:
        agent = Agent.objects.get(user=user)
        print(f"✅ Agent trouvé: {agent.nom} {agent.prenom}")
        print(f"   Service: {agent.service}")
        print(f"   Bureau: {agent.bureau}")
    except Agent.DoesNotExist:
        print("❌ Agent non trouvé pour cet utilisateur")
        return
    
    # 3. Vérifier le bureau et ses coordonnées
    if agent.bureau:
        bureau = agent.bureau
        print(f"✅ Bureau: {bureau.nom}")
        print(f"   Latitude: {bureau.latitude_centre}")
        print(f"   Longitude: {bureau.longitude_centre}")
        
        if not bureau.latitude_centre or not bureau.longitude_centre:
            print("❌ PROBLÈME: Coordonnées GPS du bureau manquantes!")
            return
    else:
        print("❌ PROBLÈME: Aucun bureau assigné à l'agent!")
        return
    
    # 4. Vérifier la présence d'aujourd'hui
    today = timezone.now().date()
    try:
        presence = Presence.objects.get(
            agent=agent,
            date_presence=today
        )
        print(f"✅ Présence trouvée:")
        print(f"   Date: {presence.date_presence}")
        print(f"   Heure arrivée: {presence.heure_arrivee}")
        print(f"   Heure départ: {presence.heure_depart}")
        print(f"   Statut: {presence.statut}")
        print(f"   Sortie détectée: {presence.sortie_detectee}")
        print(f"   Heure sortie: {presence.heure_sortie}")
    except Presence.DoesNotExist:
        print("❌ PROBLÈME: Aucune présence trouvée pour aujourd'hui!")
        return
    
    # 5. Vérifier les positions GPS
    locations = AgentLocation.objects.filter(
        agent=user,  # AgentLocation utilise User
        timestamp__date=today
    ).order_by('timestamp')
    
    print(f"\n📍 POSITIONS GPS ({locations.count()} positions):")
    print("-" * 40)
    
    if locations.count() == 0:
        print("❌ PROBLÈME: Aucune position GPS trouvée!")
        return
    
    # Analyser chaque position
    for i, loc in enumerate(locations):
        distance = calculate_distance(
            float(loc.latitude),
            float(loc.longitude),
            float(bureau.latitude_centre),
            float(bureau.longitude_centre)
        )
        
        status = "🏢 BUREAU" if distance <= 200 else f"🚶 ÉLOIGNÉ ({distance:.1f}m)"
        
        print(f"{i+1:2d}. {loc.timestamp.strftime('%H:%M:%S')} - {status}")
        print(f"    Lat: {loc.latitude}, Lon: {loc.longitude}")
        
        # Détecter les positions aberrantes (émulateur)
        if distance > 10000:
            print(f"    ⚠️ POSITION ABERRANTE (émulateur): {distance:.1f}m")
    
    # 6. Analyser la logique de détection
    print(f"\n🔍 ANALYSE DE DÉTECTION:")
    print("-" * 40)
    
    now = timezone.now()
    
    # Positions éloignées (>200m) non aberrantes
    away_positions = []
    for loc in locations:
        distance = calculate_distance(
            float(loc.latitude),
            float(loc.longitude),
            float(bureau.latitude_centre),
            float(bureau.longitude_centre)
        )
        
        # Ignorer positions aberrantes et ne garder que les éloignées
        if 200 < distance <= 10000:
            away_positions.append((loc, distance))
    
    if away_positions:
        first_away = away_positions[0]
        duration = now - first_away[0].timestamp
        
        print(f"✅ Première position éloignée: {first_away[0].timestamp.strftime('%H:%M:%S')}")
        print(f"   Distance: {first_away[1]:.1f}m")
        print(f"   Durée depuis: {duration.total_seconds()/60:.1f} minutes")
        
        # Vérifier les seuils
        TEST_MODE = True  # Comme dans le code
        time_threshold = timedelta(minutes=5) if TEST_MODE else timedelta(hours=1)
        
        print(f"\n⚙️ PARAMÈTRES ACTUELS:")
        print(f"   Mode test: {TEST_MODE}")
        print(f"   Seuil distance: 200m")
        print(f"   Seuil temps: {int(time_threshold.total_seconds()/60)} minutes")
        
        if duration >= time_threshold:
            print(f"✅ SEUILS ATTEINTS - Sortie devrait être détectée!")
        else:
            remaining = time_threshold - duration
            print(f"⏳ Seuils pas encore atteints - Reste {remaining.total_seconds()/60:.1f} minutes")
    else:
        print("❌ Aucune position éloignée valide trouvée")
    
    # 7. Vérifier les heures de travail
    current_time = now.time()
    morning_start = time(7, 30)
    morning_end = time(12, 30)
    afternoon_start = time(13, 30)
    afternoon_end = time(16, 30)
    
    is_morning = morning_start <= current_time <= morning_end
    is_afternoon = afternoon_start <= current_time <= afternoon_end
    is_work_hours = is_morning or is_afternoon
    
    print(f"\n⏰ HEURES DE TRAVAIL:")
    print(f"   Heure actuelle: {current_time}")
    print(f"   Dans les heures de travail: {is_work_hours}")
    if not is_work_hours:
        print("   ⚠️ HORS HEURES DE TRAVAIL - Vérification désactivée!")

def main():
    debug_franck_alain()

if __name__ == "__main__":
    main()
