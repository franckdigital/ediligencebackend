#!/usr/bin/env python
"""
Debug des coordonnées GPS en base de données
"""
import os
import sys
import django
from decimal import Decimal

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ediligencebackend.settings')

try:
    django.setup()
    from core.models import Bureau
    from math import radians, cos, sin, asin, sqrt
    
    print("DEBUG DES COORDONNEES GPS")
    print("=" * 40)
    
    # Récupérer tous les bureaux
    bureaux = Bureau.objects.all()
    print(f"Nombre de bureaux: {bureaux.count()}")
    
    for bureau in bureaux:
        print(f"\nBureau: {bureau.nom}")
        print(f"ID: {bureau.id}")
        print(f"Latitude: {bureau.latitude_centre} (type: {type(bureau.latitude_centre)})")
        print(f"Longitude: {bureau.longitude_centre} (type: {type(bureau.longitude_centre)})")
        print(f"Rayon: {bureau.rayon_metres}m")
        
        # Vérifier si ce sont les nouvelles coordonnées
        lat_float = float(bureau.latitude_centre)
        lon_float = float(bureau.longitude_centre)
        
        print(f"Latitude float: {lat_float}")
        print(f"Longitude float: {lon_float}")
        
        # Vérifier si c'est proche des nouvelles coordonnées attendues
        expected_lat = 5.396534
        expected_lon = -3.981554
        
        lat_diff = abs(lat_float - expected_lat)
        lon_diff = abs(lon_float - expected_lon)
        
        if lat_diff < 0.001 and lon_diff < 0.001:
            print("✅ COORDONNEES CORRECTES (nouvelles)")
        else:
            print("❌ COORDONNEES INCORRECTES (anciennes?)")
            print(f"   Attendu: {expected_lat}, {expected_lon}")
            print(f"   Trouvé:  {lat_float}, {lon_float}")
    
    # Test de calcul de distance
    if bureaux.exists():
        bureau = bureaux.first()
        print(f"\nTEST DE CALCUL DE DISTANCE")
        print("-" * 30)
        
        # Position de test (même que le bureau)
        test_lat = float(bureau.latitude_centre)
        test_lon = float(bureau.longitude_centre)
        
        print(f"Position bureau: {test_lat}, {test_lon}")
        print(f"Position test:   {test_lat}, {test_lon}")
        
        # Fonction Haversine
        def haversine(lat1, lon1, lat2, lon2):
            R = 6371000  # Rayon de la Terre en mètres
            phi1 = radians(lat1)
            phi2 = radians(lat2)
            dphi = radians(lat2 - lat1)
            dlambda = radians(lon2 - lon1)
            a = sin(dphi/2)**2 + cos(phi1)*cos(phi2)*sin(dlambda/2)**2
            c = 2*asin(sqrt(a))
            return R * c
        
        distance = haversine(test_lat, test_lon, test_lat, test_lon)
        print(f"Distance calculée: {distance:.1f}m")
        
        if distance < 1:
            print("✅ CALCUL DE DISTANCE CORRECT")
        else:
            print("❌ PROBLEME DE CALCUL DE DISTANCE")
    
    print(f"\nCONCLUSION:")
    print("Si les coordonnées sont correctes mais la distance est fausse,")
    print("le problème vient du code de validation dans SimplePresenceView.")
    
except Exception as e:
    print(f"Erreur: {e}")
    print("Assurez-vous que Django est correctement configuré.")
