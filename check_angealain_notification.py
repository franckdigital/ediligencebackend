"""
Script pour vérifier pourquoi Ange Alain n'a pas reçu de notification pour son approbation d'absence
"""
import os
import sys
import django

# Configuration de l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ediligence.settings')
django.setup()

from core.models import User, DemandeAbsence, DiligenceNotification, Notification
from django.utils import timezone

def main():
    # Récupérer l'utilisateur Ange Alain
    try:
        user = User.objects.get(username='angealain')
        print(f"Utilisateur trouvé: {user.get_full_name()} ({user.username})")
    except User.DoesNotExist:
        print("Erreur: L'utilisateur 'angealain' n'existe pas.")
        return
    
    # Vérifier les demandes d'absence
    demandes = DemandeAbsence.objects.filter(demandeur=user).order_by('-created_at')
    print(f"\n=== Demandes d'absence pour {user.username} ===")
    
    if not demandes.exists():
        print("Aucune demande d'absence trouvée.")
        return
    
    for d in demandes:
        print(f"\nID: {d.id}")
        print(f"Type: {getattr(d, 'type_absence', 'Inconnu')}")
        print(f"Date début: {d.date_debut}")
        print(f"Date fin: {d.date_fin}")
        print(f"Statut: {d.statut}")
        print(f"Date création: {d.created_at}")
        print(f"Date validation: {getattr(d, 'date_validation', 'Non définie')}")
        print(f"Validé par: {d.superieur_hierarchique if d.superieur_hierarchique else 'Inconnu'}")
        print(f"Commentaire: {getattr(d, 'commentaire_validation', 'Aucun')}")
    
    # Vérifier les notifications
    print("\n=== Notifications de diligence ===")
    notifs_diligence = DiligenceNotification.objects.filter(user=user).order_by('-created_at')
    if notifs_diligence.exists():
        for n in notifs_diligence:
            print(f"\nID: {n.id}")
            print(f"Type: {n.type_notification}")
            print(f"Message: {n.message}")
            print(f"Lien: {n.lien}")
            print(f"Date: {n.created_at}")
            print(f"Lu: {'Oui' if n.read else 'Non'}")
    else:
        print("Aucune notification de diligence trouvée.")
    
    print("\n=== Notifications standard ===")
    notifs_std = Notification.objects.filter(user=user).order_by('-created_at')
    if notifs_std.exists():
        for n in notifs_std:
            print(f"\nID: {n.id}")
            print(f"Message: {n.message}")
            print(f"Type: {getattr(n, 'type_notif', 'Non spécifié')}")
            print(f"Lien: {getattr(n, 'lien', 'Aucun')}")
            print(f"Date: {n.created_at}")
            print(f"Lu: {'Oui' if n.read else 'Non'}")
    else:
        print("Aucune notification standard trouvée.")

if __name__ == "__main__":
    main()
