#!/usr/bin/env python
"""
Test de l'API device-locks
"""
import requests
import json

# Configuration
BASE_URL = "https://e-diligence.numerix.digital"
# Remplacez par vos credentials admin
USERNAME = "franckalain"
PASSWORD = "votre_mot_de_passe"

def test_device_locks_api():
    print("=" * 60)
    print("TEST DE L'API DEVICE LOCKS")
    print("=" * 60)
    
    # 1. Connexion
    print("\n1. Connexion...")
    login_url = f"{BASE_URL}/api/token/"
    response = requests.post(login_url, json={
        "username": USERNAME,
        "password": PASSWORD
    })
    
    if response.status_code != 200:
        print(f"   ❌ Erreur connexion: {response.status_code}")
        print(f"   {response.text}")
        return
    
    token = response.json()['access']
    print(f"   ✅ Connecté avec succès")
    
    # 2. Tester l'endpoint device-locks
    print("\n2. Test GET /api/device-locks/...")
    headers = {"Authorization": f"Bearer {token}"}
    
    device_locks_url = f"{BASE_URL}/api/device-locks/"
    response = requests.get(device_locks_url, headers=headers)
    
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text[:500]}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n   ✅ {len(data)} appareils trouvés:")
        for lock in data:
            print(f"      - {lock.get('device_id', 'N/A')[:30]}... -> {lock.get('username', 'N/A')}")
    else:
        print(f"   ❌ Erreur: {response.status_code}")
    
    # 3. Vérifier directement en base
    print("\n3. Vérification SQL directe...")
    print("   Exécutez cette requête SQL sur le serveur:")
    print("   SELECT * FROM device_locks;")
    
    print("\n" + "=" * 60)

if __name__ == '__main__':
    test_device_locks_api()
