"""
Script pour lister les utilisateurs avec des rôles spécifiques
"""
import os
import django

# Configuration de l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ediligence.settings')
django.setup()

def list_users_with_roles(roles=None):
    if roles is None:
        roles = ['ADMIN', 'SUPERIEUR', 'DIRECTEUR']
    
    from django.contrib.auth import get_user_model
    from django.db.models import Q
    
    User = get_user_model()
    
    # Créer une condition Q pour chaque rôle
    q_objects = Q()
    for role in roles:
        q_objects |= Q(profile__role=role)
    
    # Récupérer les utilisateurs avec les rôles spécifiés
    users = User.objects.filter(q_objects).select_related('profile', 'profile__service', 'profile__service__direction')
    
    if not users.exists():
        print(f"Aucun utilisateur trouvé avec les rôles: {', '.join(roles)}")
        return
    
    print(f"\n=== Utilisateurs avec rôles {', '.join(roles)} ===\n")
    
    for user in users:
        profile = getattr(user, 'profile', None)
        role = getattr(profile, 'role', 'Aucun')
        service = getattr(profile, 'service', None)
        service_name = service.nom if service else 'Aucun'
        direction_name = service.direction.nom if service and hasattr(service, 'direction') else 'Aucune'
        
        print(f"Utilisateur: {user.username} ({user.get_full_name()})")
        print(f"  Email: {user.email}")
        print(f"  Rôle: {role}")
        print(f"  Service: {service_name}")
        print(f"  Direction: {direction_name}")
        print(f"  Superutilisateur: {user.is_superuser}")
        print(f"  Staff: {user.is_staff}")
        print()

if __name__ == "__main__":
    import sys
    roles = sys.argv[1:] if len(sys.argv) > 1 else None
    list_users_with_roles(roles)
