import requests
import json

try:
    # First, let's get a token by logging in
    login_url = 'http://localhost:8000/api/token/'
    login_data = {
        'username': 'franck',
        'password': 'franck123'  # Assuming this is the password
    }
    
    print("Getting authentication token...")
    login_response = requests.post(login_url, json=login_data, timeout=10)
    
    if login_response.status_code == 200:
        token_data = login_response.json()
        access_token = token_data['access']
        print(f"Token obtained successfully")
        
        # Now test the diligences endpoint
        url = 'http://localhost:8000/api/diligences/'
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        print(f"\nMaking GET request to: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success! Response data type: {type(data)}")
            if isinstance(data, dict) and 'results' in data:
                print(f"Results count: {len(data['results'])}")
            elif isinstance(data, list):
                print(f"List length: {len(data)}")
        else:
            print(f"Error response:")
            print(f"Content: {response.text[:500]}")
    else:
        print(f"Login failed: {login_response.status_code}")
        print(f"Login response: {login_response.text}")
        
except Exception as e:
    print(f"Exception: {e}")
    import traceback
    traceback.print_exc()
