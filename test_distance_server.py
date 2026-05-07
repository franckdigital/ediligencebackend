#!/usr/bin/env python
"""
Tester le calcul de distance côté serveur
"""
import os
import sys
import django
from decimal import Decimal
from math import radians, cos, sin, asin, sqrt

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ediligencebackend.settings')

try:
    django.setup()
    from core.models import Bureau
    
    print("🧪 TEST DU CALCUL DE DISTANCE CÔTÉ SERVEUR")
    print("=" * 50)
    
    # Fonction Haversine (même que dans le serveur)
    def haversine_distance(lat1, lon1, lat2, lon2):
        R = 6371000  # Rayon de la Terre en mètres
        
        # Convertir en radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        # Différences
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        # Formule Haversine
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        
        return R * c
    
    # Récupérer le bureau
    bureau = Bureau.objects.filter(nom__icontains='Principal').first()
    if not bureau:
        bureau = Bureau.objects.first()
    
    if bureau:
        print(f"📍 Bureau testé: {bureau.nom}")
        print(f"   Coordonnées: {bureau.latitude_centre}, {bureau.longitude_centre}")
        print(f"   Rayon: {bureau.rayon_metres}m")
        
        # Position de test (même que le bureau)
        test_lat = float(bureau.latitude_centre)
        test_lon = float(bureau.longitude_centre)
        
        print(f"\n📱 Position de test: {test_lat}, {test_lon}")
        
        # Calculer la distance
        distance = haversine_distance(
            test_lat, test_lon,  # Position mobile
            float(bureau.latitude_centre), float(bureau.longitude_centre)  # Position bureau
        )
        
        print(f"📏 Distance calculée: {distance:.1f} mètres")
        
        if distance < 1:
            print("✅ CALCUL CORRECT - Distance proche de 0")
        else:
            print("❌ PROBLÈME DE CALCUL - Distance non nulle")
        
        # Test avec les coordonnées attendues
        expected_lat = 5.396534
        expected_lon = -3.981554
        
        distance_expected = haversine_distance(
            expected_lat, expected_lon,
            expected_lat, expected_lon
        )
        
        print(f"\n🎯 Test avec coordonnées attendues:")
        print(f"   Position: {expected_lat}, {expected_lon}")
        print(f"   Distance: {distance_expected:.1f} mètres")
        
        # Test avec d'anciennes coordonnées possibles
        old_lat = 14.692800  # Exemple d'anciennes coordonnées
        old_lon = -17.446700
        
        distance_old = haversine_distance(
            expected_lat, expected_lon,  # Position actuelle
            old_lat, old_lon  # Anciennes coordonnées
        )
        
        print(f"\n⚠️  Test avec anciennes coordonnées:")
        print(f"   Anciennes: {old_lat}, {old_lon}")
        print(f"   Distance: {distance_old:.1f} mètres")
        
        if abs(distance_old - 12051115.6) < 1000:
            print("🎯 BINGO ! Le serveur utilise les anciennes coordonnées")
        
    else:
        print("❌ Aucun bureau trouvé")
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
