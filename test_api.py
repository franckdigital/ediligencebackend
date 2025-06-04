import requests
import json
from pprint import pprint

BASE_URL = 'http://127.0.0.1:8000/api'

def login_user(username, password):
    """Se connecter et obtenir un token JWT"""
    url = f'{BASE_URL}/auth/login/'
    data = {
        'username': username,
        'password': password
    }
    headers = {'Content-Type': 'application/json'}
    
    print(f"URL: {url}")
    print(f"Headers: {headers}")
    print(f"Data: {json.dumps(data)}")
    
    response = requests.post(url, json=data, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {response.headers}")
    print(f"Response Body: {response.text}")
    
    if response.status_code != 200:
        raise Exception(f"Status code: {response.status_code}, Response: {response.text}")
    return response.json()['access']

def get_diligences(token):
    """Récupérer les diligences avec le token JWT"""
    url = f'{BASE_URL}/diligences/'
    headers = {'Authorization': f'Bearer {token}'}
    
    print(f"\nURL: {url}")
    print(f"Headers: {headers}")
    
    response = requests.get(url, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {response.headers}")
    
    if response.status_code != 200:
        raise Exception(f"Status code: {response.status_code}, Response: {response.text}")
    return response.json()

def test_user_api(username, password):
    print(f"\n{'='*50}")
    print(f"Test de l'API pour l'utilisateur : {username}")
    print(f"{'='*50}")
    
    # Login
    print(f"\n1. Tentative de connexion...")
    try:
        token = login_user(username, password)
        print("[OK] Connexion reussie")
    except Exception as e:
        print(f"[ERREUR] Connexion impossible : {str(e)}")
        return
    
    # Récupérer les diligences
    print("\n2. Récupération des diligences...")
    try:
        diligences = get_diligences(token)
        print(f"[OK] {len(diligences['results'])} diligences recuperees")
        print("\nDetail des diligences :")
        for diligence in diligences['results']:
            print(f"\n- Reference : {diligence['reference_courrier']}")
            print(f"  Statut : {diligence['statut']}")
            if 'services_concernes' in diligence:
                services = [s['nom'] for s in diligence['services_concernes']]
                print(f"  Services : {', '.join(services)}")
            if 'direction_details' in diligence and diligence['direction_details']:
                print(f"  Direction : {diligence['direction_details']['nom']}")
    except Exception as e:
        print(f"[ERREUR] Recuperation des diligences impossible : {str(e)}")

print("Test des permissions via l'API REST")
print("="*50)

# Tester le directeur
test_user_api('directeur_rh', 'DirecteurRH2024!')

# Tester les agents
for i in range(1, 4):
    test_user_api(f'agent{i}_rh', 'AgentRH2024!')
