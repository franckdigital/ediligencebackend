import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ediligence.settings')
django.setup()

from core.models import ImputationAccess, User, Diligence

print("ImputationAccess count:", ImputationAccess.objects.count())

print("\nTous les ImputationAccess:")
for access in ImputationAccess.objects.all():
    print(f"User {access.user.id} ({access.user.username}) - Diligence {access.diligence.id}")

print("\nUtilisateur ID 3:")
user_3_access = ImputationAccess.objects.filter(user_id=3)
print(f"Accès pour user 3: {user_3_access.count()}")
for access in user_3_access:
    print(f"- Diligence {access.diligence.id}")

print("\nDiligences disponibles:")
for diligence in Diligence.objects.all():
    print(f"Diligence {diligence.id}: {diligence.reference_courrier}")
