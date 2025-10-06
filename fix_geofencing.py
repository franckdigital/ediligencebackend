#!/usr/bin/env python3
"""
Script pour corriger les paramètres de géofencing
Usage: python fix_geofencing.py
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

def fix_geofencing_settings():
    """Corriger les paramètres de géofencing dans tasks_presence.py"""
    
    print("🔧 CORRECTION DES PARAMÈTRES GÉOFENCING")
    print("=" * 50)
    
    # Lire le fichier tasks_presence.py
    tasks_file = "core/tasks_presence.py"
    
    try:
        with open(tasks_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"✅ Fichier lu: {tasks_file}")
        
        # Corrections à appliquer
        corrections = [
            # 1. Désactiver le mode test
            ("TEST_MODE = True", "TEST_MODE = False"),
            
            # 2. Activer la vérification forcée temporairement
            ("FORCE_CHECK = False", "FORCE_CHECK = True"),
            
            # 3. Réduire le seuil de temps pour les tests (optionnel)
            # Cette ligne sera commentée pour garder le mode normal
        ]
        
        modified = False
        for old, new in corrections:
            if old in content:
                content = content.replace(old, new)
                print(f"✅ Corrigé: {old} → {new}")
                modified = True
            else:
                print(f"⚠️ Non trouvé: {old}")
        
        if modified:
            # Sauvegarder le fichier modifié
            with open(tasks_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Fichier sauvegardé: {tasks_file}")
            print("\n🔄 REDÉMARRAGE REQUIS:")
            print("   1. Redémarrez Celery Beat: celery -A ediligencebackend beat")
            print("   2. Redémarrez Celery Worker: celery -A ediligencebackend worker")
        else:
            print("ℹ️ Aucune modification nécessaire")
            
    except FileNotFoundError:
        print(f"❌ Fichier non trouvé: {tasks_file}")
    except Exception as e:
        print(f"❌ Erreur: {e}")

def test_manual_detection():
    """Tester manuellement la détection pour franck.alain"""
    
    print("\n🧪 TEST MANUEL DE DÉTECTION")
    print("=" * 40)
    
    try:
        user = User.objects.get(username='franck.alain')
        agent = Agent.objects.get(user=user)
        
        today = timezone.now().date()
        presence = Presence.objects.get(agent=agent, date_presence=today)
        
        # Vérifier si les conditions sont remplies
        if presence.sortie_detectee:
            print("✅ Sortie déjà détectée")
            return
        
        bureau = agent.bureau
        if not bureau or not bureau.latitude_centre or not bureau.longitude_centre:
            print("❌ Bureau ou coordonnées manquantes")
            return
        
        # Récupérer la dernière position
        last_location = AgentLocation.objects.filter(
            agent=user,
            timestamp__date=today
        ).order_by('-timestamp').first()
        
        if not last_location:
            print("❌ Aucune position GPS trouvée")
            return
        
        # Calculer la distance
        distance = calculate_distance(
            float(last_location.latitude),
            float(last_location.longitude),
            float(bureau.latitude_centre),
            float(bureau.longitude_centre)
        )
        
        print(f"📍 Distance actuelle: {distance:.1f}m")
        
        if distance > 200:
            # Forcer la détection de sortie
            now = timezone.now()
            
            # Marquer la sortie
            presence.heure_sortie = now.time()
            presence.sortie_detectee = True
            presence.statut = 'absent'
            presence.temps_absence_minutes = 60  # 1 heure par défaut
            presence.commentaire = f"Sortie forcée manuellement - Distance: {distance:.1f}m"
            presence.save()
            
            print(f"✅ SORTIE FORCÉE MANUELLEMENT")
            print(f"   Heure: {now.time()}")
            print(f"   Distance: {distance:.1f}m")
            print(f"   Statut: absent")
        else:
            print(f"ℹ️ Agent au bureau (distance: {distance:.1f}m)")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

def main():
    print("DIAGNOSTIC ET CORRECTION GÉOFENCING")
    print("=" * 60)
    
    choice = input("\nChoisir une action:\n1. Corriger les paramètres\n2. Test manuel\n3. Les deux\nChoix (1/2/3): ")
    
    if choice in ['1', '3']:
        fix_geofencing_settings()
    
    if choice in ['2', '3']:
        test_manual_detection()

if __name__ == "__main__":
    main()
