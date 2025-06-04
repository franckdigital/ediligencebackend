import os
import django

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ediligence.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import UserProfile, Direction, Service
from django.db import transaction

def create_test_users():
    print("Création des utilisateurs de test...")
    
    # Créer la direction RH si elle n'existe pas
    direction_rh, _ = Direction.objects.get_or_create(
        nom="Direction des Ressources Humaines",
        defaults={
            'description': "Direction en charge de la gestion des ressources humaines"
        }
    )
    print(f"Direction RH créée : {direction_rh}")
    
    # Créer le service RH si il n'existe pas
    service_rh, _ = Service.objects.get_or_create(
        nom="Service RH",
        defaults={
            'description': "Service principal des ressources humaines",
            'direction': direction_rh
        }
    )
    print(f"Service RH créé : {service_rh}")
    
    # Créer le directeur RH
    with transaction.atomic():
        try:
            directeur = User.objects.get(username='directeur_rh')
            print("Le directeur RH existe déjà")
        except User.DoesNotExist:
            directeur = User.objects.create_user(
                username='directeur_rh',
                password='DirecteurRH2024!',
                email='directeur.rh@example.com',
                first_name='Directeur',
                last_name='RH'
            )
            UserProfile.objects.create(
                user=directeur,
                role='DIRECTEUR',
                service=service_rh
            )
            print("Directeur RH créé avec succès")
    
    # Créer les agents RH
    for i in range(1, 4):
        with transaction.atomic():
            try:
                agent = User.objects.get(username=f'agent{i}_rh')
                print(f"L'agent {i} RH existe déjà")
            except User.DoesNotExist:
                agent = User.objects.create_user(
                    username=f'agent{i}_rh',
                    password='AgentRH2024!',
                    email=f'agent{i}.rh@example.com',
                    first_name=f'Agent{i}',
                    last_name='RH'
                )
                UserProfile.objects.create(
                    user=agent,
                    role='AGENT',
                    service=service_rh
                )
                print(f"Agent {i} RH créé avec succès")

if __name__ == '__main__':
    create_test_users()
