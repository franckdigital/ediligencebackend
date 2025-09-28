import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ediligence.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import UserProfile, Service

# Get available services
services = Service.objects.all()
print("Available services:")
for s in services:
    print(f"  {s.id}: {s.nom}")

# Assign services to users without service
users_without_service = User.objects.filter(profile__service__isnull=True)
print(f"\nUsers without service: {users_without_service.count()}")

if users_without_service.exists():
    # Assign Service Développement d'Application (ID=1) to users without service
    service_dev = Service.objects.get(id=1)
    
    for user in users_without_service:
        user.profile.service = service_dev
        user.profile.save()
        print(f"Assigned service '{service_dev.nom}' to user {user.username}")

print("\nFinal user service assignments:")
for u in User.objects.all():
    service_name = u.profile.service.nom if u.profile.service else "NO_SERVICE"
    print(f"  {u.username}: {service_name}")
