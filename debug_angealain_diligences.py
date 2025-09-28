import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ediligence.settings')
django.setup()

from core.models import Diligence, User, ImputationAccess
from django.db.models import Prefetch

# Simuler la requête pour angealain
angealain = User.objects.get(username='angealain')
print(f"Utilisateur: {angealain.username} (ID: {angealain.id})")
print(f"Rôle: {angealain.profile.role}")

# Base queryset
base_qs = Diligence.objects.select_related(
    'courrier',
    'courrier__service',
    'courrier__service__direction',
    'direction'
).prefetch_related(
    Prefetch('agents', queryset=User.objects.select_related('profile', 'profile__service')),
    'services_concernes',
    'services_concernes__direction'
).all().order_by('-created_at')

print(f"\nTotal diligences dans le système: {base_qs.count()}")

# Diligences assignées à angealain
assigned_qs = base_qs.filter(agents=angealain)
print(f"Diligences assignées à angealain: {assigned_qs.count()}")
for d in assigned_qs:
    print(f"  - {d.reference_courrier}")

# Diligences avec ImputationAccess pour angealain
imputation_access_qs = base_qs.filter(imputation_access__user=angealain)
print(f"Diligences avec ImputationAccess pour angealain: {imputation_access_qs.count()}")
for d in imputation_access_qs:
    print(f"  - {d.reference_courrier}")

# Queryset final (union)
final_qs = (assigned_qs | imputation_access_qs).distinct()
print(f"\nQueryset final pour angealain: {final_qs.count()}")
for d in final_qs:
    print(f"  - {d.reference_courrier}")

# Vérifier la diligence MF2025CA001
diligence_1 = Diligence.objects.get(id=1)
print(f"\nDiligence MF2025CA001:")
print(f"  Agents assignés:")
for agent in diligence_1.agents.all():
    print(f"    - {agent.username} (ID: {agent.id})")

print(f"  ImputationAccess:")
for access in ImputationAccess.objects.filter(diligence=diligence_1):
    print(f"    - {access.user.username} (ID: {access.user.id})")
