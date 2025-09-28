import requests
import json
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ediligence.settings')
django.setup()

try:
    # Get token for franck
    user = User.objects.get(username='franck')
    refresh = RefreshToken.for_user(user)
    token = str(refresh.access_token)
    
    print(f"Testing API request for user: {user.username}")
    print(f"Token: {token[:50]}...")
    
    # Make request to the API
    url = 'http://localhost:8000/api/diligences/'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    print(f"\nMaking GET request to: {url}")
    response = requests.get(url, headers=headers, timeout=10)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Success! Response data type: {type(data)}")
        if isinstance(data, dict) and 'results' in data:
            print(f"Results count: {len(data['results'])}")
        elif isinstance(data, list):
            print(f"List length: {len(data)}")
    else:
        print(f"Error response:")
        print(f"Content: {response.text[:1000]}")
        
except Exception as e:
    print(f"Exception: {e}")
    import traceback
    traceback.print_exc()
