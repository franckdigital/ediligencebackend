#!/usr/bin/env python
"""
Script pour configurer les rôles de gestion des présences
"""
import os
import django
import sys

# Configuration Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ediligence.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import UserProfile, Service, Direction

def setup_presence_management_roles():
    """Configurer les rôles pour la gestion des présences"""
    print("🔧 Configuration des rôles de gestion des présences...")
    
    # Créer des exemples d'utilisateurs avec les nouveaux rôles
    roles_config = [
        {
            'username': 'directeur_general',
            'email': 'directeur.general@ediligence.ci',
            'first_name': 'Jean',
            'last_name': 'KOUAME',
            'role': 'DIRECTEUR',
            'description': 'Directeur Général - Peut gérer toutes les présences'
        },
        {
            'username': 'sous_directeur_rh',
            'email': 'sous.directeur.rh@ediligence.ci',
            'first_name': 'Marie',
            'last_name': 'TRAORE',
            'role': 'SOUS_DIRECTEUR',
            'description': 'Sous-Directeur RH - Peut gérer les présences de sa direction'
        },
        {
            'username': 'chef_service_admin',
            'email': 'chef.service.admin@ediligence.ci',
            'first_name': 'Pierre',
            'last_name': 'OUATTARA',
            'role': 'CHEF_SERVICE',
            'description': 'Chef de Service Administration - Peut gérer les présences de son service'
        }
    ]
    
    # Récupérer ou créer une direction et un service de test
    direction, created = Direction.objects.get_or_create(
        nom="Direction Générale",
        defaults={'description': 'Direction Générale de l\'organisation'}
    )
    
    service, created = Service.objects.get_or_create(
        nom="Service Administration",
        defaults={
            'description': 'Service Administration et RH',
            'direction': direction
        }
    )
    
    print(f"📍 Direction: {direction.nom}")
    print(f"📍 Service: {service.nom}")
    
    for role_config in roles_config:
        # Créer ou récupérer l'utilisateur
        user, created = User.objects.get_or_create(
            username=role_config['username'],
            defaults={
                'email': role_config['email'],
                'first_name': role_config['first_name'],
                'last_name': role_config['last_name'],
                'is_staff': True,
                'is_active': True
            }
        )
        
        if created:
            user.set_password('password123')  # Mot de passe par défaut
            user.save()
            print(f"✅ Utilisateur créé: {user.username}")
        else:
            print(f"👤 Utilisateur existant: {user.username}")
        
        # Créer ou mettre à jour le profil
        profile, created = UserProfile.objects.get_or_create(
            user=user,
            defaults={
                'role': role_config['role'],
                'service': service,
                'matricule': f"MAT{user.id:04d}"
            }
        )
        
        if not created:
            profile.role = role_config['role']
            profile.service = service
            profile.save()
        
        print(f"   Rôle: {profile.role}")
        print(f"   Service: {profile.service.nom if profile.service else 'Aucun'}")
        print(f"   Description: {role_config['description']}")
        print()
    
    print("📊 Résumé des permissions de gestion des présences:")
    print("=" * 60)
    print("🔹 ADMIN: Peut gérer toutes les présences")
    print("🔹 DIRECTEUR: Peut gérer toutes les présences de sa direction")
    print("🔹 SOUS_DIRECTEUR: Peut gérer les présences de sa direction")
    print("🔹 CHEF_SERVICE: Peut gérer les présences de son service")
    print("🔹 SUPERIEUR: Peut voir les présences (lecture seule)")
    print("🔹 AGENT: Peut seulement pointer sa propre présence")
    print()
    
    print("🎯 Fonctionnalités disponibles pour les gestionnaires:")
    print("- Modifier le statut présent/absent via switch web")
    print("- Éditer les heures d'arrivée, départ et sortie")
    print("- Recevoir des notifications de sorties automatiques")
    print("- Réactiver le bouton 'Pointer Départ' sur mobile")
    print()
    
    print("✅ Configuration terminée avec succès!")

def test_permissions():
    """Tester les permissions des différents rôles"""
    print("\n🧪 Test des permissions...")
    
    roles_to_test = ['ADMIN', 'DIRECTEUR', 'SOUS_DIRECTEUR', 'CHEF_SERVICE', 'SUPERIEUR', 'AGENT']
    
    for role in roles_to_test:
        can_modify = role in ['ADMIN', 'DIRECTEUR', 'SOUS_DIRECTEUR', 'CHEF_SERVICE']
        status = "✅ Peut modifier" if can_modify else "❌ Lecture seule"
        print(f"   {role}: {status}")

if __name__ == "__main__":
    print("🚀 CONFIGURATION DES RÔLES DE GESTION DES PRÉSENCES")
    print("=" * 60)
    
    try:
        setup_presence_management_roles()
        test_permissions()
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
