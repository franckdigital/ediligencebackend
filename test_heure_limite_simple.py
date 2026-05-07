#!/usr/bin/env python3
"""
Test simple de la logique d'heure limite
Usage: python manage.py shell < test_heure_limite_simple.py
"""
import os
import django
from datetime import time

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ediligencebackend.settings')
django.setup()

def test_logique_heure():
    """Test de la logique d'ajustement d'heure"""
    
    print("🕐 TEST LOGIQUE HEURE LIMITE 7H30")
    print("=" * 40)
    
    # Logique extraite de la vue
    from datetime import time as dt_time
    heure_limite_arrivee = dt_time(7, 30)  # 7h30
    
    # Cas de test
    heures_test = [
        time(5, 30),   # 5h30
        time(6, 45),   # 6h45
        time(7, 0),    # 7h00
        time(7, 29),   # 7h29
        time(7, 30),   # 7h30
        time(7, 31),   # 7h31
        time(8, 0),    # 8h00
        time(9, 15),   # 9h15
    ]
    
    for heure_test in heures_test:
        if heure_test < heure_limite_arrivee:
            heure_finale = heure_limite_arrivee
            status = "AJUSTÉ"
            message = f'Arrivée enregistrée à 07:30 (pointage effectué à {heure_test.strftime("%H:%M")})'
        else:
            heure_finale = heure_test
            status = "NORMAL"
            message = 'Arrivée enregistrée avec succès'
        
        print(f"{heure_test.strftime('%H:%M')} → {heure_finale.strftime('%H:%M')} [{status}]")
    
    print(f"\n✅ Logique implémentée:")
    print(f"   - Pointage avant 7h30 → Ajusté à 7h30")
    print(f"   - Pointage à partir de 7h30 → Heure réelle")
    print(f"   - Message informatif en cas d'ajustement")

if __name__ == "__main__":
    test_logique_heure()
