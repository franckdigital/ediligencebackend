"""
Script de test pour vérifier l'envoi des notifications d'approbation d'absence
"""
import os
import sys
import django
from datetime import datetime, timedelta

# Configuration de l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ediligence.settings')
django.setup()

from django.contrib.auth import get_user_model
from core.models import DemandeAbsence, Notification, DiligenceNotification
from core.serializers import DemandeAbsenceSerializer
from rest_framework.test import APIRequestFactory, force_authenticate
from core.views import DemandeAbsenceViewSet

def main():
    # Récupérer les utilisateurs
    User = get_user_model()
    
    try:
        # Récupérer Ange Alain (demandeur)
        demandeur = User.objects.get(username='angealain')
        print(f"Demandeur trouvé: {demandeur.get_full_name()} ({demandeur.username})")
        
        # Utiliser l'utilisateur 'alainfranck' comme validateur (qui a le rôle DIRECTEUR)
        try:
            validateur = User.objects.get(username='alainfranck')
            print(f"Validateur trouvé: {validateur.get_full_name()} ({validateur.username})")
            
            # Vérifier si l'utilisateur a un profil avec des droits de validation
            if hasattr(validateur, 'profile') and validateur.profile.role in ['ADMIN', 'SUPERIEUR', 'DIRECTEUR']:
                print(f"Le validateur a le rôle: {validateur.profile.role}")
            else:
                print("Attention: Le validateur n'a pas les rôles nécessaires pour valider les demandes.")
                return
                
        except User.DoesNotExist:
            print("Erreur: L'utilisateur 'alainfranck' n'existe pas.")
            return
        
        # Créer une demande d'absence de test si elle n'existe pas déjà
        demande, created = DemandeAbsence.objects.get_or_create(
            demandeur=demandeur,
            type_absence='personnelle',
            date_debut=datetime.now() + timedelta(days=1),
            date_fin=datetime.now() + timedelta(days=2),
            defaults={
                'statut': 'en_attente',
                'superieur_hierarchique': validateur,
                'motif': 'Test d\'approbation d\'absence',
                'duree_heures': 8
            }
        )
        
        if created:
            print(f"Nouvelle demande d'absence créée avec l'ID: {demande.id}")
        else:
            print(f"Utilisation de la demande d'absence existante ID: {demande.id}")
        
        # Simuler une requête d'approbation
        factory = APIRequestFactory()
        view = DemandeAbsenceViewSet.as_view({'post': 'approuver'})
        
        # Créer une requête PUT pour approuver la demande
        request = factory.post(f'/api/demandes-absence/{demande.id}/approuver/', {
            'commentaire': 'Test d\'approbation automatique',
        }, format='json')
        
        # Authentifier la requête avec le validateur
        force_authenticate(request, user=validateur)
        
        print("\n=== Simulation de l'approbation de la demande ===")
        response = view(request, pk=demande.id)
        
        print(f"\nRésultat de l'approbation: {response.status_code} {response.data}")
        
        # Vérifier que la demande a été approuvée
        demande.refresh_from_db()
        print(f"\nStatut de la demande après approbation: {demande.statut}")
        
        # Vérifier les notifications créées
        print("\n=== Vérification des notifications ===")
        
        # Notifications standard
        notifs_std = Notification.objects.filter(user=demandeur).order_by('-created_at')
        print(f"\nNotifications standard pour {demandeur.username}:")
        for n in notifs_std[:3]:  # Afficher les 3 dernières
            print(f"- {n.get_type_notif_display()}: {n.contenu} (Date: {n.created_at})")
        
        # Notifications de diligence
        notifs_diligence = DiligenceNotification.objects.filter(user=demandeur).order_by('-created_at')
        print(f"\nNotifications de diligence pour {demandeur.username}:")
        for n in notifs_diligence[:3]:  # Afficher les 3 dernières
            print(f"- {n.get_type_notification_display()}: {n.message} (Date: {n.created_at})")
        
        # Vérifier si les notifications ont été créées
        if not notifs_std.exists() and not notifs_diligence.exists():
            print("\nAucune notification n'a été créée. Vérifiez les logs pour les erreurs potentielles.")
            
    except User.DoesNotExist:
        print("Erreur: L'utilisateur 'angealain' n'existe pas.")
    except Exception as e:
        print(f"Erreur lors du test: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
