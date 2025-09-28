#!/usr/bin/env python3
"""
Script pour tester l'API des instructions personnelles
"""

import os
import sys
import django
import requests
import json

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ediligence.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib.auth.models import User
from core.models import UserDiligenceInstruction, Diligence
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

def test_instructions_api():
    print("=== TEST API INSTRUCTIONS PERSONNELLES ===\n")
    
    # Créer un client API
    client = APIClient()
    
    # Récupérer un utilisateur pour les tests
    try:
        user = User.objects.get(username='angealain')
        print(f"Utilisateur de test: {user.username} (ID: {user.id})")
    except User.DoesNotExist:
        print("Utilisateur 'angealain' non trouvé")
        return
    
    # Générer un token JWT pour l'authentification
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
    
    # Test 1: GET - Récupérer les instructions existantes
    print("\n1. Test GET instructions existantes:")
    response = client.get('/api/user-diligence-instructions/')
    print(f"Status: {response.status_code}")
    print(f"Data: {response.data}")
    
    # Test 2: GET avec filtres
    print("\n2. Test GET avec filtres (diligence=2, user=5):")
    response = client.get('/api/user-diligence-instructions/?diligence=2&user=5')
    print(f"Status: {response.status_code}")
    print(f"Data: {response.data}")
    
    # Test 3: POST - Créer une nouvelle instruction
    print("\n3. Test POST nouvelle instruction:")
    new_instruction_data = {
        'diligence': 2,
        'user': user.id,
        'instruction': 'Test instruction via API'
    }
    response = client.post('/api/user-diligence-instructions/', new_instruction_data)
    print(f"Status: {response.status_code}")
    print(f"Data: {response.data}")
    
    if response.status_code == 201:
        instruction_id = response.data['id']
        
        # Test 4: PATCH - Mettre à jour l'instruction
        print(f"\n4. Test PATCH instruction ID {instruction_id}:")
        update_data = {
            'instruction': 'Instruction mise à jour via API'
        }
        response = client.patch(f'/api/user-diligence-instructions/{instruction_id}/', update_data)
        print(f"Status: {response.status_code}")
        print(f"Data: {response.data}")
        
        # Test 5: DELETE - Supprimer l'instruction
        print(f"\n5. Test DELETE instruction ID {instruction_id}:")
        response = client.delete(f'/api/user-diligence-instructions/{instruction_id}/')
        print(f"Status: {response.status_code}")
    
    print("\n=== FIN DES TESTS ===")

if __name__ == "__main__":
    test_instructions_api()
