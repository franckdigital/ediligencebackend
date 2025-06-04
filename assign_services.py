import os
import django

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ediligence.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import Direction, Service, UserProfile
from django.db import transaction

def assign_services():
    print("Attribution des services aux utilisateurs...")
    
    # Récupérer la direction RH
    try:
        direction_rh = Direction.objects.get(nom="Direction des Ressources Humaines")
    except Direction.DoesNotExist:
        print("Erreur : La Direction RH n'existe pas. Veuillez d'abord exécuter create_test_users.py")
        return
    
    # Récupérer le service RH
    try:
        service_rh = Service.objects.get(nom="Service RH", direction=direction_rh)
    except Service.DoesNotExist:
        print("Erreur : Le Service RH n'existe pas. Veuillez d'abord exécuter create_test_users.py")
        return
    
    # Assigner les services aux utilisateurs
    with transaction.atomic():
        # Directeur RH
        try:
            directeur = User.objects.get(username='directeur_rh')
            profile = directeur.profile
            profile.service = service_rh
            profile.save()
            print(f"Service assigné au directeur RH : {service_rh}")
        except User.DoesNotExist:
            print("Erreur : Le directeur RH n'existe pas")
        
        # Agents RH
        for i in range(1, 4):
            try:
                agent = User.objects.get(username=f'agent{i}_rh')
                profile = agent.profile
                profile.service = service_rh
                profile.save()
                print(f"Service assigné à l'agent {i} RH : {service_rh}")
            except User.DoesNotExist:
                print(f"Erreur : L'agent {i} RH n'existe pas")

if __name__ == '__main__':
    assign_services()
