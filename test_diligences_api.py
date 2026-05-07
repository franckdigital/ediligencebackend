import os
import django
import traceback

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ediligence.settings')
django.setup()

try:
    from django.contrib.auth.models import User
    from core.models import UserProfile, Diligence
    from rest_framework.test import APIClient
    from rest_framework_simplejwt.tokens import RefreshToken
    
    # Obtenir un token pour franck
    franck = User.objects.get(username='franck')
    refresh = RefreshToken.for_user(franck)
    token = str(refresh.access_token)
    
    print(f'User: {franck.username} (ID: {franck.id})')
    print(f'Profile: {franck.profile.role if hasattr(franck, "profile") else "No profile"}')
    
    # Tester l'API
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    
    print('\nTesting /api/diligences/ endpoint...')
    response = client.get('/api/diligences/')
    print(f'Status: {response.status_code}')
    
    if response.status_code != 200:
        print(f'Error content: {response.content.decode()}')
    else:
        data = response.json()
        if isinstance(data, dict) and 'results' in data:
            print(f'Success: {len(data["results"])} diligences returned')
        elif isinstance(data, list):
            print(f'Success: {len(data)} diligences returned')
        else:
            print(f'Unexpected response format: {type(data)}')
        
except Exception as e:
    print(f'Exception: {e}')
    traceback.print_exc()
