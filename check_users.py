import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ediligence.settings')
django.setup()

from core.models import User, UserProfile, Service

print("Tous les utilisateurs avec leurs services:")
for user in User.objects.all():
    try:
        profile = user.profile
        service_name = profile.service.nom if profile.service else "Aucun service"
        print(f"- {user.username} - Role: {profile.role} - Service: {service_name}")
    except UserProfile.DoesNotExist:
        print(f"- {user.username} - Pas de profil")

print("\nServices disponibles:")
for service in Service.objects.all():
    print(f"- Service ID {service.id}: {service.nom}")
    users_in_service = User.objects.filter(profile__service=service)
    print(f"  Utilisateurs: {users_in_service.count()}")
    for user in users_in_service:
        print(f"    - {user.username} ({user.profile.role})")
