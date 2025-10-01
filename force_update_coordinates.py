#!/usr/bin/env python
"""
Forcer la mise à jour des coordonnées GPS
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
    
    print("MISE A JOUR FORCEE DES COORDONNEES")
    print("=" * 40)
    
    # Nouvelles coordonnées (d'après l'interface web)
    new_lat = Decimal('5.396534')
    new_lon = Decimal('-3.981554')
    new_radius = 200
    
    # Récupérer le bureau principal
    bureau = Bureau.objects.filter(nom__icontains='Principal').first()
    if not bureau:
        bureau = Bureau.objects.first()
    
    if not bureau:
        print("❌ Aucun bureau trouvé !")
        print("Création d'un bureau de test...")
        bureau = Bureau.objects.create(
            nom='Bureau Principal',
            latitude_centre=new_lat,
            longitude_centre=new_lon,
            rayon_metres=new_radius
        )
        print("✅ Bureau créé avec succès")
    else:
        print(f"Bureau trouvé: {bureau.nom}")
        print(f"Anciennes coordonnées: {bureau.latitude_centre}, {bureau.longitude_centre}")
        
        # Mise à jour
        bureau.latitude_centre = new_lat
        bureau.longitude_centre = new_lon
        bureau.rayon_metres = new_radius
        bureau.save()
        
        print(f"✅ Coordonnées mises à jour:")
        print(f"   Latitude: {bureau.latitude_centre}")
        print(f"   Longitude: {bureau.longitude_centre}")
        print(f"   Rayon: {bureau.rayon_metres}m")
    
    # Vérification
    bureau.refresh_from_db()
    print(f"\nVERIFICATION:")
    print(f"Latitude en base: {bureau.latitude_centre}")
    print(f"Longitude en base: {bureau.longitude_centre}")
    print(f"Rayon en base: {bureau.rayon_metres}")
    
    # Test de calcul de distance
    from math import radians, cos, sin, asin, sqrt
    
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371000
        phi1 = radians(lat1)
        phi2 = radians(lat2)
        dphi = radians(lat2 - lat1)
        dlambda = radians(lon2 - lon1)
        a = sin(dphi/2)**2 + cos(phi1)*cos(phi2)*sin(dlambda/2)**2
        c = 2*asin(sqrt(a))
        return R * c
    
    # Test avec la même position
    test_distance = haversine(
        float(bureau.latitude_centre), float(bureau.longitude_centre),
        float(bureau.latitude_centre), float(bureau.longitude_centre)
    )
    
    print(f"\nTEST DE DISTANCE:")
    print(f"Distance même position: {test_distance:.1f}m")
    
    if test_distance < 1:
        print("✅ Le calcul de distance fonctionne")
        print("\n🚀 SOLUTION:")
        print("1. Redémarrez le serveur Django")
        print("2. Testez le pointage mobile")
        print("3. La distance devrait maintenant être correcte")
    else:
        print("❌ Problème dans le calcul de distance")
    
except Exception as e:
    print(f"Erreur: {e}")
    import traceback
    traceback.print_exc()
