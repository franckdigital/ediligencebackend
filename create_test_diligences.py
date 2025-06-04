import os
import django
from datetime import datetime, timedelta

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ediligence.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import Direction, Service, Diligence, Courrier, UserProfile
from django.db import transaction
from django.db.models import Q

def create_test_diligences():
    print("Création des diligences de test...")
    
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
    
    # Récupérer les utilisateurs
    try:
        directeur = User.objects.get(username='directeur_rh')
        agents = list(User.objects.filter(Q(username='agent1_rh') | Q(username='agent2_rh') | Q(username='agent3_rh')))
        if not agents:
            raise User.DoesNotExist
            
        # Vérifier que les utilisateurs ont le bon rôle
        for agent in agents:
            profile = agent.profile
            if not profile.role == 'AGENT':
                profile.role = 'AGENT'
                profile.save()
                
        directeur_profile = directeur.profile
        if not directeur_profile.role == 'DIRECTEUR':
            directeur_profile.role = 'DIRECTEUR'
            directeur_profile.save()
            
    except User.DoesNotExist:
        print("Erreur : Les utilisateurs n'existent pas. Veuillez d'abord exécuter create_test_users.py")
        return
    
    # Créer quelques courriers et diligences
    with transaction.atomic():
        # Supprimer les diligences existantes
        Diligence.objects.all().delete()
        
        # Courrier 1 - Demande de formation
        courrier1, _ = Courrier.objects.get_or_create(
            reference="FORM-2024-001",
            defaults={
                'expediteur': "Service Formation",
                'objet': "Demande de formation Excel avancé",
                'date_reception': datetime.now().date(),
                'service': service_rh,
                'categorie': 'Demande'
            }
        )
        
        # Diligence 1 - Liée au courrier 1
        diligence1 = Diligence.objects.create(
            reference_courrier="FORM-2024-001",
            courrier=courrier1,
            categorie='Formation',
            statut='en_cours',
            instructions="Analyser la demande de formation et établir un plan",
            date_limite=datetime.now().date() + timedelta(days=14),
            expediteur=courrier1.expediteur,
            objet=courrier1.objet,
            date_reception=courrier1.date_reception,
            direction=direction_rh
        )
        diligence1.agents.add(agents[0])
        diligence1.services_concernes.add(service_rh)
        
        # Courrier 2 - Recrutement
        courrier2, _ = Courrier.objects.get_or_create(
            reference="REC-2024-001",
            defaults={
                'expediteur': "Direction Générale",
                'objet': "Recrutement développeur fullstack",
                'date_reception': datetime.now().date(),
                'service': service_rh,
                'categorie': 'Demande'
            }
        )
        
        # Diligence 2 - Liée au courrier 2
        diligence2 = Diligence.objects.create(
            reference_courrier="REC-2024-001",
            courrier=courrier2,
            categorie='Recrutement',
            statut='en_attente',
            instructions="Lancer le processus de recrutement pour un développeur fullstack",
            date_limite=datetime.now().date() + timedelta(days=30),
            expediteur=courrier2.expediteur,
            objet=courrier2.objet,
            date_reception=courrier2.date_reception,
            direction=direction_rh
        )
        diligence2.agents.add(agents[1])
        diligence2.services_concernes.add(service_rh)
        
        print("Diligences créées avec succès")

if __name__ == '__main__':
    create_test_diligences()
