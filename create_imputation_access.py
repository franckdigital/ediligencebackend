import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ediligence.settings')
django.setup()

from core.models import ImputationAccess, User, Diligence

# Créer un accès d'imputation pour l'utilisateur ID 3 (franckalain)
user_3 = User.objects.get(id=3)
diligence_1 = Diligence.objects.get(id=1)

# Vérifier si l'accès existe déjà
existing_access = ImputationAccess.objects.filter(user=user_3, diligence=diligence_1).first()

if existing_access:
    print(f"Accès déjà existant pour {user_3.username} sur diligence {diligence_1.id}")
else:
    # Créer l'accès
    new_access = ImputationAccess.objects.create(
        user=user_3,
        diligence=diligence_1,
        access_type='edit'
    )
    print(f"Accès créé pour {user_3.username} sur diligence {diligence_1.id}")

# Vérifier le résultat
print(f"\nAccès d'imputation pour user 3: {ImputationAccess.objects.filter(user_id=3).count()}")
for access in ImputationAccess.objects.filter(user_id=3):
    print(f"- Diligence {access.diligence.id} en mode {access.access_type}")
