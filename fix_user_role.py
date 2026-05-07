#!/usr/bin/env python
import os
import sys
import django

# Configuration Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ediligence.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import UserProfile

def fix_user_role():
    try:
        # Trouver l'utilisateur par email
        user = User.objects.get(email='franckalain.digital@gmail.com')
        print(f"Utilisateur trouvé: {user.username} ({user.email})")
        
        # Obtenir ou créer le profil
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        if created:
            print("Profil créé pour l'utilisateur")
        else:
            print(f"Profil existant trouvé - Rôle actuel: {profile.role}")
        
        # Mettre à jour le rôle vers ADMIN
        profile.role = 'ADMIN'
        profile.save()
        
        print(f"Rôle mis à jour vers: {profile.role}")
        print("Correction terminée avec succès!")
        
    except User.DoesNotExist:
        print("Erreur: Utilisateur avec l'email 'franckalain.digital@gmail.com' non trouvé")
    except Exception as e:
        print(f"Erreur lors de la correction: {e}")

if __name__ == '__main__':
    fix_user_role()
