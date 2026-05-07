#!/usr/bin/env python3
"""
Test des heures étendues de détection de sortie
Usage: python manage.py shell < test_extended_hours.py
"""
import os
import sys
import django
from datetime import time

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ediligencebackend.settings')
django.setup()

def test_work_hours():
    """Tester les nouvelles heures de travail"""
    
    print("🕐 TEST DES HEURES DE TRAVAIL ÉTENDUES")
    print("=" * 50)
    
    # Nouvelles heures définies
    morning_start = time(7, 30)
    morning_end = time(12, 30)
    afternoon_start = time(13, 30)
    afternoon_end = time(23, 59)
    
    print(f"Heures de surveillance :")
    print(f"  Matin : {morning_start} - {morning_end}")
    print(f"  Après-midi/Soir : {afternoon_start} - {afternoon_end}")
    print()
    
    # Heures de test
    test_times = [
        time(6, 0),   # Avant travail
        time(7, 30),  # Début matin
        time(9, 0),   # Matin
        time(12, 30), # Fin matin
        time(13, 0),  # Pause déjeuner
        time(13, 30), # Début après-midi
        time(16, 30), # Ancienne fin
        time(18, 0),  # Heures sup
        time(20, 0),  # Heures sup tardives
        time(22, 0),  # Heures sup très tardives
        time(23, 59), # Fin surveillance
        time(0, 30),  # Nuit
    ]
    
    print("Test des heures :")
    print("-" * 30)
    
    for test_time in test_times:
        is_morning = morning_start <= test_time <= morning_end
        is_afternoon = afternoon_start <= test_time <= afternoon_end
        is_work_hours = is_morning or is_afternoon
        
        period = ""
        if is_morning:
            period = "MATIN"
        elif is_afternoon:
            period = "APRÈS-MIDI/SOIR"
        else:
            period = "HORS TRAVAIL"
        
        status = "✅ SURVEILLÉ" if is_work_hours else "❌ NON SURVEILLÉ"
        
        print(f"{test_time.strftime('%H:%M')} - {period:15} - {status}")
    
    print()
    print("📊 RÉSUMÉ :")
    print("✅ Surveillance de 07:30 à 12:30 (matin)")
    print("❌ Pause de 12:31 à 13:29 (déjeuner)")
    print("✅ Surveillance de 13:30 à 23:59 (après-midi + heures sup)")
    print("❌ Pause de 00:00 à 07:29 (nuit)")

def test_current_time():
    """Tester l'heure actuelle"""
    from django.utils import timezone
    
    now = timezone.now()
    current_time = now.time()
    
    morning_start = time(7, 30)
    morning_end = time(12, 30)
    afternoon_start = time(13, 30)
    afternoon_end = time(23, 59)
    
    is_morning = morning_start <= current_time <= morning_end
    is_afternoon = afternoon_start <= current_time <= afternoon_end
    is_work_hours = is_morning or is_afternoon
    
    print(f"\n🕐 HEURE ACTUELLE : {current_time.strftime('%H:%M:%S')}")
    print(f"Période : {'MATIN' if is_morning else 'APRÈS-MIDI/SOIR' if is_afternoon else 'HORS TRAVAIL'}")
    print(f"Surveillance : {'✅ ACTIVE' if is_work_hours else '❌ INACTIVE'}")
    
    if is_work_hours:
        print("🔍 La détection de sortie est ACTIVE maintenant")
    else:
        if current_time < morning_start:
            next_start = morning_start
            print(f"⏰ Prochaine surveillance à {next_start}")
        elif morning_end < current_time < afternoon_start:
            print(f"⏰ Prochaine surveillance à {afternoon_start} (pause déjeuner)")
        else:
            print(f"⏰ Prochaine surveillance à {morning_start} (demain matin)")

def main():
    test_work_hours()
    test_current_time()
    
    print(f"\n🔧 POUR APPLIQUER LES CHANGEMENTS :")
    print("1. Redémarrez Celery Beat : celery -A ediligencebackend beat")
    print("2. Redémarrez Celery Worker : celery -A ediligencebackend worker")
    print("3. Ou testez manuellement : check_agent_exits()")

if __name__ == "__main__":
    main()
