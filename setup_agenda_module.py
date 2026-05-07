"""
Script d'initialisation du module Agenda
Crée les données de test et configure les permissions
"""
import os
import django
import sys

# Configuration Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ediligence.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import RendezVous, Reunion, ReunionPresence, UserProfile
from datetime import datetime, timedelta
from django.utils import timezone

def create_sample_data():
    """Créer des données de test pour le module Agenda"""
    
    print("=" * 60)
    print("INITIALISATION DU MODULE AGENDA")
    print("=" * 60)
    
    # Vérifier les utilisateurs
    print("\n1. Vérification des utilisateurs...")
    users = User.objects.all()
    print(f"   ✅ {users.count()} utilisateurs trouvés")
    
    if users.count() < 2:
        print("   ⚠️  Pas assez d'utilisateurs pour créer des exemples")
        return
    
    # Trouver un directeur/supérieur et un agent
    try:
        directeur = User.objects.filter(profile__role__in=['ADMIN', 'DIRECTEUR', 'SUPERIEUR']).first()
        agent = User.objects.filter(profile__role='AGENT').first()
        
        if not directeur:
            directeur = users.first()
        if not agent:
            agent = users.last()
            
        print(f"   ✅ Organisateur : {directeur.username} ({directeur.profile.role if hasattr(directeur, 'profile') else 'N/A'})")
        print(f"   ✅ Participant : {agent.username} ({agent.profile.role if hasattr(agent, 'profile') else 'N/A'})")
    except Exception as e:
        print(f"   ❌ Erreur lors de la récupération des utilisateurs : {e}")
        return
    
    # Créer des rendez-vous de test
    print("\n2. Création de rendez-vous de test...")
    try:
        # Rendez-vous dans 2 jours
        rdv1 = RendezVous.objects.create(
            titre="Entretien individuel de performance",
            description="Évaluation annuelle des performances et objectifs",
            date_debut=timezone.now() + timedelta(days=2, hours=9),
            date_fin=timezone.now() + timedelta(days=2, hours=10),
            lieu="Bureau du directeur",
            organisateur=directeur,
            participant=agent,
            statut='prevu',
            mode='presentiel',
            commentaires="Préparer le bilan de l'année"
        )
        print(f"   ✅ Rendez-vous créé : {rdv1.titre}")
        
        # Rendez-vous en ligne dans 5 jours
        rdv2 = RendezVous.objects.create(
            titre="Point hebdomadaire",
            description="Suivi des dossiers en cours",
            date_debut=timezone.now() + timedelta(days=5, hours=14),
            date_fin=timezone.now() + timedelta(days=5, hours=15),
            lieu="En ligne",
            organisateur=directeur,
            participant=agent,
            statut='prevu',
            mode='en_ligne',
            lien_visio="https://meet.google.com/abc-defg-hij",
            commentaires="Lien Teams à venir"
        )
        print(f"   ✅ Rendez-vous créé : {rdv2.titre}")
        
    except Exception as e:
        print(f"   ❌ Erreur lors de la création des rendez-vous : {e}")
    
    # Créer des réunions de test
    print("\n3. Création de réunions de test...")
    try:
        # Réunion de service dans 3 jours
        reunion1 = Reunion.objects.create(
            intitule="Réunion de service mensuelle",
            description="Ordre du jour :\n1. Bilan du mois\n2. Objectifs du mois prochain\n3. Questions diverses",
            type_reunion='presentiel',
            date_debut=timezone.now() + timedelta(days=3, hours=10),
            date_fin=timezone.now() + timedelta(days=3, hours=12),
            lieu="Salle de conférence A",
            organisateur=directeur,
            statut='prevu'
        )
        
        # Ajouter des participants
        participants = User.objects.all()[:5]  # Prendre les 5 premiers utilisateurs
        reunion1.participants.set(participants)
        reunion1.save()
        
        print(f"   ✅ Réunion créée : {reunion1.intitule}")
        print(f"      👥 {reunion1.participants.count()} participants ajoutés")
        
        # Réunion en ligne dans 7 jours
        reunion2 = Reunion.objects.create(
            intitule="Comité de direction",
            description="Points stratégiques et décisions importantes",
            type_reunion='en_ligne',
            date_debut=timezone.now() + timedelta(days=7, hours=15),
            date_fin=timezone.now() + timedelta(days=7, hours=17),
            lieu="Zoom",
            lien_zoom="https://zoom.us/j/123456789",
            organisateur=directeur,
            statut='prevu'
        )
        
        # Ajouter des participants
        reunion2.participants.set(participants[:3])
        reunion2.save()
        
        print(f"   ✅ Réunion créée : {reunion2.intitule}")
        print(f"      👥 {reunion2.participants.count()} participants ajoutés")
        
    except Exception as e:
        print(f"   ❌ Erreur lors de la création des réunions : {e}")
    
    # Statistiques finales
    print("\n" + "=" * 60)
    print("STATISTIQUES")
    print("=" * 60)
    print(f"📅 Rendez-vous créés : {RendezVous.objects.count()}")
    print(f"👥 Réunions créées : {Reunion.objects.count()}")
    print(f"✅ Événements à venir : {RendezVous.objects.filter(statut='prevu').count() + Reunion.objects.filter(statut='prevu').count()}")
    
    print("\n" + "=" * 60)
    print("✅ INITIALISATION TERMINÉE AVEC SUCCÈS")
    print("=" * 60)
    print("\n📝 Prochaines étapes :")
    print("   1. Accéder à l'agenda : http://localhost:3000/agenda")
    print("   2. Créer vos propres rendez-vous et réunions")
    print("   3. Tester les différentes vues du calendrier")
    print("\n")

def check_models():
    """Vérifier que les modèles sont bien créés"""
    print("\n" + "=" * 60)
    print("VÉRIFICATION DES MODÈLES")
    print("=" * 60)
    
    try:
        from core.models import RendezVous, RendezVousDocument, Reunion, ReunionPresence
        print("✅ Modèle RendezVous importé")
        print("✅ Modèle RendezVousDocument importé")
        print("✅ Modèle Reunion importé")
        print("✅ Modèle ReunionPresence importé")
        return True
    except ImportError as e:
        print(f"❌ Erreur d'import : {e}")
        print("\n⚠️  Les migrations n'ont pas encore été appliquées.")
        print("   Exécutez : python manage.py makemigrations && python manage.py migrate")
        return False

def main():
    """Fonction principale"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "SETUP MODULE AGENDA - E-DILIGENCE" + " " * 15 + "║")
    print("╚" + "═" * 58 + "╝")
    
    # Vérifier les modèles
    if not check_models():
        return
    
    # Demander confirmation
    print("\n⚠️  Ce script va créer des données de test.")
    response = input("Continuer ? (o/n) : ")
    
    if response.lower() != 'o':
        print("❌ Opération annulée")
        return
    
    # Créer les données
    create_sample_data()

if __name__ == '__main__':
    main()
