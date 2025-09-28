import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ediligence.settings')
django.setup()

from django.contrib.auth.models import User
from core.serializers import UserSerializer
from rest_framework.request import Request
from django.test import RequestFactory

# Create a mock request
factory = RequestFactory()
request = factory.get('/api/users/')

# Get users with profiles
users = User.objects.select_related('profile', 'profile__service', 'profile__service__direction').all()

print("Testing UserSerializer output:")
for user in users:
    serializer = UserSerializer(user, context={'request': request})
    data = serializer.data
    print(f"\nUser {user.username}:")
    print(f"  Full data: {data}")
    print(f"  Has profile field: {'profile' in data}")
    print(f"  Has service_obj field: {'service_obj' in data}")
    if 'profile' in data:
        print(f"  Profile data: {data['profile']}")
    if 'service_obj' in data:
        print(f"  Service_obj data: {data['service_obj']}")
