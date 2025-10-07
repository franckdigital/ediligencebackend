#!/usr/bin/env python3
"""
Script pour ajuster les heures de travail et tester
Usage: python fix_work_hours.py
"""
import os
import sys
import django
from datetime import datetime, timedelta, time

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ediligence.settings')
django.setup()

from django.utils import timezone
from core.models import GeofenceSettings

def fix_work_hours():
    """Ajuster les heures de travail pour inclure maintenant"""
    print("🔧 AJUSTEMENT DES HEURES DE TRAVAIL")
    print("=" * 50)
    
    settings = GeofenceSettings.objects.first()
    if not settings:
        print("❌ Aucune configuration trouvée")
        return
    
    now = timezone.now()
    current_time = now.time()
    
    print(f"⏰ Heure actuelle: {current_time}")
    print(f"📋 Heures actuelles:")
    print(f"   Matin: {settings.heure_debut_matin} - {settings.heure_fin_matin}")
    print(f"   Après-midi: {settings.heure_debut_apres_midi} - {settings.heure_fin_apres_midi}")
    print(f"   Dans heures de travail: {settings.is_heure_travail(now)}")
    
    if settings.is_heure_travail(now):
        print("✅ Déjà dans les heures de travail")
        return
    
    # Ajuster les heures pour inclure maintenant
    current_hour = now.hour
    current_minute = now.minute
    
    # Étendre la plage d'après-midi pour inclure maintenant
    new_debut = time(max(7, current_hour - 1), 0)
    new_fin = time(min(23, current_hour + 2), 59)
    
    print(f"\n🔧 Nouvelles heures proposées:")
    print(f"   Après-midi: {new_debut} - {new_fin}")
    
    # Appliquer les changements
    settings.heure_debut_apres_midi = new_debut
    settings.heure_fin_apres_midi = new_fin
    settings.save()
    
    print(f"✅ Heures mises à jour!")
    print(f"   Maintenant dans heures de travail: {settings.is_heure_travail(now)}")
    
    return settings

def main():
    """Fonction principale"""
    print("🔧 CORRECTION DES HEURES DE TRAVAIL GÉOFENCING")
    print("=" * 60)
    
    try:
        settings = fix_work_hours()
        
        if settings:
            print(f"\n💡 Maintenant vous pouvez:")
            print("1. Tester: python debug_step_by_step.py")
            print("2. Ou tester: python setup_test_and_debug.py")
            print("3. Ou tester: python test_fix_geofencing.py")
            
            print(f"\n⚠️  N'oubliez pas de restaurer les heures originales après les tests!")
            print("   Heures originales recommandées: 13:30:00 - 16:30:00")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
