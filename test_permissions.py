import os
import django
from django.db.models import Q

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ediligence.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import Direction, Service, Diligence, UserProfile

def test_user_permissions(username):
    user = User.objects.get(username=username)
    print(f"\nTest des permissions pour {user.get_full_name()} ({username})")
    print(f"Rôle : {user.profile.role}")
    print(f"Service : {user.profile.service}")
    
    # Simuler la logique du DiligenceViewSet
    if user.profile.role == 'DIRECTEUR':
        # Pour un directeur : toutes les diligences de sa direction
        diligences = Diligence.objects.filter(
            Q(direction=user.profile.service.direction) |
            Q(services_concernes__direction=user.profile.service.direction)
        ).distinct()
    elif user.profile.role in ['SUPERIEUR', 'SECRETAIRE']:
        # Pour un supérieur/secrétaire : diligences de son service
        diligences = Diligence.objects.filter(
            services_concernes=user.profile.service
        ).distinct()
    elif user.profile.role == 'AGENT':
        # Pour un agent : ses propres diligences
        diligences = Diligence.objects.filter(
            agents=user
        ).distinct()
    else:
        diligences = Diligence.objects.none()

    print(f"\nDiligences visibles ({diligences.count()}) :")
    for diligence in diligences:
        services = ", ".join([s.nom for s in diligence.services_concernes.all()])
        print(f"- {diligence.reference_courrier}")
        print(f"  Service(s) : {services}")
        print(f"  Direction : {diligence.direction}")
        print(f"  Statut : {diligence.statut}")
        print(f"  Agent(s) : {', '.join([a.get_full_name() for a in diligence.agents.all()])}")
        print()

# Tester le directeur
print("="*50)
print("TEST DU DIRECTEUR")
print("="*50)
test_user_permissions('directeur_rh')

# Tester chaque agent
print("\n"+"="*50)
print("TEST DES AGENTS")
print("="*50)
for i in range(1, 4):
    test_user_permissions(f'agent{i}_rh')
