#!/usr/bin/env python3
"""
Test immédiat de la détection avec les nouvelles heures
Usage: python manage.py shell < test_detection_now.py
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ediligencebackend.settings')
django.setup()

from django.utils import timezone
from datetime import time
import logging

# Configurer les logs
logging.basicConfig(level=logging.INFO, format='%(message)s')

def test_detection_now():
    """Tester la détection maintenant avec les nouvelles heures"""
    
    print("🔍 TEST DE DÉTECTION IMMÉDIAT")
    print("=" * 40)
    
    # Vérifier l'heure actuelle
    now = timezone.now()
    current_time = now.time()
    
    # Nouvelles heures
    morning_start = time(7, 30)
    morning_end = time(12, 30)
    afternoon_start = time(13, 30)
    afternoon_end = time(23, 59)
    
    is_morning = morning_start <= current_time <= morning_end
    is_afternoon = afternoon_start <= current_time <= afternoon_end
    is_work_hours = is_morning or is_afternoon
    
    print(f"Heure actuelle : {current_time.strftime('%H:%M:%S')}")
    print(f"Dans les heures de travail : {is_work_hours}")
    
    if is_work_hours:
        print("✅ HEURES DE TRAVAIL - Détection active")
        
        # Importer et exécuter la tâche
        from core.tasks_presence import check_agent_exits
        
        print("\n🔄 Exécution de check_agent_exits()...")
        print("-" * 40)
        
        # Exécuter la tâche
        result = check_agent_exits()
        
        print("-" * 40)
        print("✅ Tâche terminée")
        
    else:
        print("❌ HORS HEURES DE TRAVAIL")
        
        if current_time < morning_start:
            print(f"⏰ Prochaine détection à {morning_start}")
        elif morning_end < current_time < afternoon_start:
            print(f"⏰ Pause déjeuner - Prochaine détection à {afternoon_start}")
        else:
            print(f"⏰ Nuit - Prochaine détection à {morning_start} (demain)")
    
    # Vérifier franckalain spécifiquement
    print(f"\n👤 VÉRIFICATION FRANCKALAIN")
    print("-" * 30)
    
    try:
        from django.contrib.auth.models import User
        from core.models import Agent, Presence
        
        user = User.objects.get(username='franckalain')
        agent = Agent.objects.get(user=user)
        today = now.date()
        
        try:
            presence = Presence.objects.get(agent=agent, date_presence=today)
            print(f"Statut : {presence.statut}")
            print(f"Arrivée : {presence.heure_arrivee}")
            print(f"Sortie détectée : {presence.sortie_detectee}")
            print(f"Heure sortie : {presence.heure_sortie}")
            
            if presence.sortie_detectee:
                print("✅ Sortie déjà détectée")
            else:
                print("⏳ Sortie pas encore détectée")
                
        except Presence.DoesNotExist:
            print("❌ Pas de présence aujourd'hui")
            
    except Exception as e:
        print(f"❌ Erreur : {e}")

def main():
    test_detection_now()

if __name__ == "__main__":
    main()
