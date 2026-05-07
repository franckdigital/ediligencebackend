#!/usr/bin/env python
"""
Test du système de pointage via les APIs REST
"""
import requests
import json
from math import radians, cos, sin, asin, sqrt

def haversine(lat1, lon1, lat2, lon2):
    """Calcul de distance avec formule de Haversine"""
    R = 6371000  # Rayon de la Terre en mètres
    phi1 = radians(lat1)
    phi2 = radians(lat2)
    dphi = radians(lat2 - lat1)
    dlambda = radians(lon2 - lon1)
    a = sin(dphi/2)**2 + cos(phi1)*cos(phi2)*sin(dlambda/2)**2
    c = 2*asin(sqrt(a))
    return R * c

def test_pointage_system():
    """Tester le système de pointage avec différentes distances"""
    
    print("TEST DU SYSTEME DE POINTAGE AVEC VALIDATION DE DISTANCE")
    print("=" * 60)
    
    # Configuration
    base_url = "http://localhost:8000"
    
    # Note: Vous devez remplacer ce token par un token valide
    # Obtenez-le via: POST /api/auth/login/ avec vos identifiants
    token = "YOUR_JWT_TOKEN_HERE"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print("1. VERIFICATION DES BUREAUX")
    print("-" * 30)
    
    try:
        # Récupérer les bureaux
        response = requests.get(f"{base_url}/api/bureaux/", headers=headers)
        
        if response.status_code == 200:
            bureaux = response.json()
            print(f"Bureaux trouvés: {len(bureaux)}")
            
            for bureau in bureaux:
                print(f"  - {bureau['nom']}: ({bureau['latitude_centre']}, {bureau['longitude_centre']}) - Rayon: {bureau['rayon_metres']}m")
                
            if bureaux:
                bureau_principal = next((b for b in bureaux if 'Principal' in b['nom']), bureaux[0])
                
                print(f"\nBureau de test: {bureau_principal['nom']}")
                print(f"Coordonnées: {bureau_principal['latitude_centre']}, {bureau_principal['longitude_centre']}")
                print(f"Rayon autorisé: {bureau_principal['rayon_metres']}m")
                
                # Tests de pointage
                print(f"\n2. TESTS DE POINTAGE")
                print("-" * 30)
                
                test_positions = [
                    # Position exacte du bureau
                    (float(bureau_principal['latitude_centre']), float(bureau_principal['longitude_centre']), "Position exacte du bureau"),
                    
                    # Position proche (dans le rayon)
                    (float(bureau_principal['latitude_centre']) + 0.0005, float(bureau_principal['longitude_centre']), "Position proche (~50m)"),
                    
                    # Position limite
                    (float(bureau_principal['latitude_centre']) + 0.001, float(bureau_principal['longitude_centre']), "Position limite (~100m)"),
                    
                    # Position trop loin
                    (float(bureau_principal['latitude_centre']) + 0.002, float(bureau_principal['longitude_centre']), "Position trop loin (~200m)"),
                ]
                
                for lat, lon, description in test_positions:
                    distance = haversine(
                        float(bureau_principal['latitude_centre']), float(bureau_principal['longitude_centre']),
                        lat, lon
                    )
                    
                    print(f"\nTest: {description}")
                    print(f"Coordonnées: {lat:.6f}, {lon:.6f}")
                    print(f"Distance calculée: {distance:.1f}m")
                    
                    # Test de pointage arrivée
                    pointage_data = {
                        "action": "arrivee",
                        "latitude": lat,
                        "longitude": lon
                    }
                    
                    try:
                        response = requests.post(f"{base_url}/api/simple-presence/", 
                                               headers=headers, 
                                               json=pointage_data)
                        
                        if response.status_code == 200:
                            result = response.json()
                            print(f"Résultat: AUTORISÉ - {result.get('message', 'Succès')}")
                        else:
                            error_data = response.json()
                            print(f"Résultat: REFUSÉ - {error_data.get('error', 'Erreur inconnue')}")
                            if 'distance' in error_data:
                                print(f"Distance serveur: {error_data['distance']}m")
                    
                    except requests.exceptions.RequestException as e:
                        print(f"Erreur de requête: {e}")
                    except json.JSONDecodeError:
                        print(f"Erreur de décodage JSON: {response.text}")
                
            else:
                print("Aucun bureau trouvé !")
                
        else:
            print(f"Erreur lors de la récupération des bureaux: {response.status_code}")
            print(f"Réponse: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"Erreur de connexion: {e}")
        print("\nVérifiez que:")
        print("1. Le serveur Django est démarré")
        print("2. L'URL est correcte (http://localhost:8000)")
        print("3. Le token JWT est valide")
    
    print(f"\n3. INSTRUCTIONS POUR OBTENIR UN TOKEN")
    print("-" * 40)
    print("Pour tester avec un vrai token, exécutez:")
    print(f"curl -X POST {base_url}/api/auth/login/ \\")
    print("  -H 'Content-Type: application/json' \\")
    print("  -d '{\"username\": \"votre_username\", \"password\": \"votre_password\"}'")
    print("\nPuis remplacez YOUR_JWT_TOKEN_HERE dans ce script par le token reçu.")
    
    print(f"\n4. TEST MANUEL RAPIDE")
    print("-" * 25)
    print("Testez manuellement avec curl:")
    print(f"curl -X POST {base_url}/api/simple-presence/ \\")
    print("  -H 'Authorization: Bearer YOUR_TOKEN' \\")
    print("  -H 'Content-Type: application/json' \\")
    print("  -d '{")
    print("    \"action\": \"arrivee\",")
    print("    \"latitude\": 14.692800,")
    print("    \"longitude\": -17.446700")
    print("  }'")

if __name__ == "__main__":
    test_pointage_system()
