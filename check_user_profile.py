"""
Script pour vérifier les informations d'un utilisateur et son profil
"""
import os
import django

# Configuration de l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ediligence.settings')
django.setup()

def check_user_profile(username):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    try:
        # Récupérer l'utilisateur
        user = User.objects.get(username=username)
        print(f"\n=== Informations de l'utilisateur ===")
        print(f"Nom d'utilisateur: {user.username}")
        print(f"Nom complet: {user.get_full_name()}")
        print(f"Email: {user.email}")
        print(f"Superutilisateur: {user.is_superuser}")
        print(f"Staff: {user.is_staff}")
        
        # Vérifier les permissions
        print("\n=== Permissions globales ===")
        if user.user_permissions.exists():
            for perm in user.user_permissions.all():
                print(f"- {perm.codename}")
        else:
            print("Aucune permission spécifique")
        
        # Vérifier les groupes
        print("\n=== Groupes ===")
        if user.groups.exists():
            for group in user.groups.all():
                print(f"- {group.name}")
                print("  Permissions du groupe:")
                for perm in group.permissions.all():
                    print(f"  - {perm.codename}")
        else:
            print("Aucun groupe")
        
        # Vérifier le profil
        print("\n=== Profil utilisateur ===")
        if hasattr(user, 'profile'):
            profile = user.profile
            print(f"Rôle: {getattr(profile, 'role', 'Non défini')}")
            
            # Informations sur le service
            if hasattr(profile, 'service') and profile.service:
                print(f"Service: {profile.service.nom}")
                if hasattr(profile.service, 'direction'):
                    print(f"Direction: {profile.service.direction.nom if profile.service.direction else 'Aucune'}")
            else:
                print("Service: Aucun")
                
            # Vérifier si l'utilisateur est un supérieur hiérarchique
            print("\n=== Droits de validation ===")
            if profile.role in ['ADMIN', 'SUPERIEUR', 'DIRECTEUR']:
                print(f"Peut valider les demandes (rôle: {profile.role})")
            else:
                print(f"Ne peut pas valider les demandes (rôle: {profile.role})")
                print("Rôles requis: ADMIN, SUPERIEUR ou DIRECTEUR")
        else:
            print("Aucun profil associé à cet utilisateur")
        
    except User.DoesNotExist:
        print(f"Erreur: L'utilisateur '{username}' n'existe pas.")
    except Exception as e:
        print(f"Erreur lors de la récupération des informations: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import sys
    username = sys.argv[1] if len(sys.argv) > 1 else 'franckalain'
    check_user_profile(username)
