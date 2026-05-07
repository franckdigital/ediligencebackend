#!/usr/bin/env python
"""
Vérifier et corriger les coordonnées du bureau en base de données
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
    
    print("🔍 VÉRIFICATION DES COORDONNÉES EN BASE")
    print("=" * 50)
    
    # Récupérer tous les bureaux
    bureaux = Bureau.objects.all()
    print(f"Nombre de bureaux: {bureaux.count()}")
    
    for bureau in bureaux:
        print(f"\n📍 Bureau: {bureau.nom}")
        print(f"   ID: {bureau.id}")
        print(f"   Latitude: {bureau.latitude_centre}")
        print(f"   Longitude: {bureau.longitude_centre}")
        print(f"   Rayon: {bureau.rayon_metres}m")
        
        # Vérifier si ce sont les nouvelles coordonnées attendues
        lat_float = float(bureau.latitude_centre)
        lon_float = float(bureau.longitude_centre)
        
        expected_lat = 5.396534
        expected_lon = -3.981554
        
        lat_diff = abs(lat_float - expected_lat)
        lon_diff = abs(lon_float - expected_lon)
        
        if lat_diff < 0.001 and lon_diff < 0.001:
            print("   ✅ COORDONNÉES CORRECTES (nouvelles)")
        else:
            print("   ❌ COORDONNÉES INCORRECTES")
            print(f"   📍 Attendu: {expected_lat}, {expected_lon}")
            print(f"   📍 Trouvé:  {lat_float}, {lon_float}")
            
            # Proposer la correction
            print(f"\n🔧 CORRECTION AUTOMATIQUE:")
            bureau.latitude_centre = Decimal(str(expected_lat))
            bureau.longitude_centre = Decimal(str(expected_lon))
            bureau.rayon_metres = 200
            bureau.save()
            print(f"   ✅ Coordonnées corrigées automatiquement")
            print(f"   📍 Nouvelles: {bureau.latitude_centre}, {bureau.longitude_centre}")
    
    print(f"\n🎯 RÉSUMÉ:")
    print("Les coordonnées ont été vérifiées et corrigées si nécessaire.")
    print("Redémarrez le serveur Django pour appliquer les changements.")
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
