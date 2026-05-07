import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ediligence.settings')
django.setup()

from core.models import ImputationAccess, User

# Vérifier l'utilisateur angealain (ID 5)
angealain = User.objects.get(username='angealain')
print(f"Utilisateur: {angealain.username} (ID: {angealain.id})")
print(f"Rôle: {angealain.profile.role}")

# Vérifier ses accès d'imputation
accesses = ImputationAccess.objects.filter(user=angealain)
print(f"\nImputationAccess pour angealain: {accesses.count()}")
for access in accesses:
    print(f"- Diligence {access.diligence.id}: {access.diligence.reference_courrier}")

# Supprimer tous les accès d'imputation pour angealain
if accesses.exists():
    print(f"\nSuppression de {accesses.count()} accès d'imputation pour angealain...")
    accesses.delete()
    print("Accès supprimés.")
else:
    print("\nAucun accès d'imputation à supprimer.")

# Vérifier le résultat
final_accesses = ImputationAccess.objects.filter(user=angealain)
print(f"\nAccès restants pour angealain: {final_accesses.count()}")
