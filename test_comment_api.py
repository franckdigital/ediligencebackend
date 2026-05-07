import os
import django
import requests

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ediligence.settings')
django.setup()

from core.models import Diligence

# Test direct de l'API de commentaires
diligence = Diligence.objects.first()
print(f"Diligence ID: {diligence.id}")
print(f"Commentaires actuels: {diligence.commentaires_agents}")

# Test API PATCH
url = f"http://localhost:8000/api/enhanced-diligences/{diligence.id}/"
data = {
    "commentaires_agents": "Test commentaire API direct"
}

print(f"\nEnvoi PATCH vers: {url}")
print(f"Données: {data}")

try:
    response = requests.patch(url, json=data, headers={
        'Content-Type': 'application/json'
    })
    print(f"Status: {response.status_code}")
    print(f"Réponse: {response.text}")
    
    # Vérifier en base
    diligence.refresh_from_db()
    print(f"Commentaires après PATCH: {diligence.commentaires_agents}")
    
except Exception as e:
    print(f"Erreur: {e}")
