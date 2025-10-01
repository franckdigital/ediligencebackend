#!/usr/bin/env python
"""
Test de l'API des bureaux pour vérifier les coordonnées GPS
"""
import requests
import json

def test_bureau_api():
    """Tester l'API des bureaux"""
    
    print("TEST DE L'API DES BUREAUX")
    print("=" * 40)
    
    base_url = "http://localhost:8000"
    
    # Test sans authentification d'abord
    print("\n1. TEST SANS AUTHENTIFICATION")
    print("-" * 30)
    
    try:
        response = requests.get(f"{base_url}/api/bureaux/")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 401:
            print("✓ Authentification requise (normal)")
        elif response.status_code == 200:
            data = response.json()
            print(f"✓ Bureaux trouvés: {len(data)}")
            for bureau in data:
                print(f"  - {bureau['nom']}: ({bureau['latitude_centre']}, {bureau['longitude_centre']}) - {bureau['rayon_metres']}m")
        else:
            print(f"✗ Erreur inattendue: {response.status_code}")
            print(f"Réponse: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"✗ Erreur de connexion: {e}")
        print("\nVérifiez que le serveur Django est démarré:")
        print("python manage.py runserver")
        return
    
    print("\n2. INSTRUCTIONS POUR TEST AVEC TOKEN")
    print("-" * 40)
    print("Pour tester avec authentification:")
    print(f"1. Obtenez un token:")
    print(f"   curl -X POST {base_url}/api/auth/login/ \\")
    print("     -H 'Content-Type: application/json' \\")
    print("     -d '{\"username\": \"votre_username\", \"password\": \"votre_password\"}'")
    print()
    print(f"2. Testez l'API des bureaux:")
    print(f"   curl -H 'Authorization: Bearer YOUR_TOKEN' \\")
    print(f"     {base_url}/api/bureaux/")
    print()
    print(f"3. Testez le pointage:")
    print(f"   curl -X POST {base_url}/api/presence/simple/ \\")
    print("     -H 'Authorization: Bearer YOUR_TOKEN' \\")
    print("     -H 'Content-Type: application/json' \\")
    print("     -d '{")
    print('       "action": "arrivee",')
    print('       "latitude": 5.396534,')
    print('       "longitude": -3.981554')
    print("     }'")
    
    print("\n3. COORDONNÉES ATTENDUES")
    print("-" * 30)
    print("D'après l'interface web:")
    print("Latitude: 5.396534")
    print("Longitude: -3.981554")
    print("Rayon: 200m")
    
    print("\n4. DIAGNOSTIC DE L'ERREUR MOBILE")
    print("-" * 35)
    print("L'erreur mobile montre:")
    print("Distance: 12051555.1m > 200m")
    print()
    print("Causes possibles:")
    print("1. L'app mobile utilise les anciennes coordonnées")
    print("2. Cache de l'application non rafraîchi")
    print("3. Problème de synchronisation API")
    print("4. Erreur dans le calcul de distance")
    
    print("\n5. SOLUTIONS RECOMMANDÉES")
    print("-" * 30)
    print("1. Redémarrer l'application mobile")
    print("2. Vider le cache de l'app")
    print("3. Vérifier les logs du serveur")
    print("4. Tester l'API manuellement")

if __name__ == "__main__":
    test_bureau_api()
