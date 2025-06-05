import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from core.models import UserProfile

@pytest.mark.django_db
def test_user_registration_with_fingerprint():
    User = get_user_model()
    client = APIClient()
    payload = {
        'username': 'biotest',
        'password': 'Testpass123!',
        'password2': 'Testpass123!',
        'email': 'bio@test.com',
        'first_name': 'Bio',
        'last_name': 'Test',
        'role': 'AGENT',
        'fingerprint_hash': 'fingerprint_abc123',
    }
    resp = client.post('/api/register/', payload, format='json')
    assert resp.status_code == 201 or resp.status_code == 200
    user = User.objects.get(username='biotest')
    profile = UserProfile.objects.get(user=user)
    assert profile.empreinte_hash == 'fingerprint_abc123'

@pytest.mark.django_db
def test_login_with_fingerprint():
    User = get_user_model()
    user = User.objects.create_user(
        username='bio2',
        password='Testpass456!',
        email='bio2@test.com',
        first_name='Bio2',
        last_name='Test2',
    )
    UserProfile.objects.create(user=user, role='AGENT', empreinte_hash='fingerprint_login123')
    client = APIClient()
    resp = client.post('/api/login/', {'fingerprint_hash': 'fingerprint_login123'}, format='json')
    assert resp.status_code == 200
    assert 'token' in resp.json()
