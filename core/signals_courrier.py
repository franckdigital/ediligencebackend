from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import (
    Courrier, CourrierAccess, CourrierImputation, 
    CourrierNotification, CourrierStatut, Diligence
)


def creer_notification(utilisateur, courrier, type_notification, titre, message, priorite='normale', cree_par=None, metadata=None):
    """Fonction utilitaire pour créer une notification"""
    CourrierNotification.objects.create(
        utilisateur=utilisateur,
        courrier=courrier,
        type_notification=type_notification,
        titre=titre,
        message=message,
        priorite=priorite,
        cree_par=cree_par,
        metadata=metadata or {}
    )


@receiver(post_save, sender=Courrier)
def notifier_nouveau_courrier(sender, instance, created, **kwargs):
    """Notifier lors de la création d'un nouveau courrier"""
    if created:
        # Déterminer qui doit être notifié
        utilisateurs_a_notifier = []
        
        # Pour les courriers confidentiels, notifier uniquement les ADMIN et DIRECTEUR
        if instance.type_courrier == 'confidentiel':
            utilisateurs_a_notifier = User.objects.filter(
                profile__role__in=['ADMIN', 'DIRECTEUR']
            )
            priorite = 'haute'
        else:
            # Pour les courriers ordinaires, notifier tous les utilisateurs du service concerné
            if instance.service:
                utilisateurs_a_notifier = User.objects.filter(
                    profile__service=instance.service
                )
            else:
                # Si pas de service, notifier les ADMIN et DIRECTEUR
                utilisateurs_a_notifier = User.objects.filter(
                    profile__role__in=['ADMIN', 'DIRECTEUR']
                )
            priorite = 'normale'
        
        # Créer les notifications
        type_courrier_label = 'confidentiel' if instance.type_courrier == 'confidentiel' else 'ordinaire'
        sens_label = 'en arrivée' if instance.sens == 'arrivee' else 'en départ'
        
        for utilisateur in utilisateurs_a_notifier:
            creer_notification(
                utilisateur=utilisateur,
                courrier=instance,
                type_notification='nouveau_courrier',
                titre=f'Nouveau courrier {type_courrier_label} {sens_label}',
                message=f'Un nouveau courrier {type_courrier_label} {sens_label} a été enregistré : {instance.reference}. Objet: {instance.objet}',
                priorite=priorite,
                metadata={
                    'courrier_id': instance.id,
                    'reference': instance.reference,
                    'type_courrier': instance.type_courrier,
                    'sens': instance.sens
                }
            )


@receiver(post_save, sender=CourrierImputation)
def notifier_imputation_courrier(sender, instance, created, **kwargs):
    """Notifier l'utilisateur lorsqu'un courrier lui est imputé"""
    if created:
        type_courrier_label = 'confidentiel' if instance.courrier.type_courrier == 'confidentiel' else 'ordinaire'
        access_label = 'en édition' if instance.access_type == 'edit' else 'en lecture'
        
        creer_notification(
            utilisateur=instance.user,
            courrier=instance.courrier,
            type_notification='courrier_impute',
            titre=f'Courrier {type_courrier_label} imputé',
            message=f'Le courrier {instance.courrier.reference} vous a été imputé {access_label} par {instance.granted_by.get_full_name() or instance.granted_by.username}.',
            priorite='haute' if instance.courrier.type_courrier == 'confidentiel' else 'normale',
            cree_par=instance.granted_by,
            metadata={
                'courrier_id': instance.courrier.id,
                'reference': instance.courrier.reference,
                'access_type': instance.access_type,
                'imputation_id': instance.id
            }
        )


@receiver(post_save, sender=CourrierAccess)
def notifier_acces_courrier(sender, instance, created, **kwargs):
    """Notifier l'utilisateur lorsqu'un accès à un courrier confidentiel lui est accordé"""
    if created:
        access_label = 'en édition' if instance.access_type == 'edit' else 'en lecture'
        
        creer_notification(
            utilisateur=instance.user,
            courrier=instance.courrier,
            type_notification='acces_accorde',
            titre='Accès à un courrier confidentiel accordé',
            message=f'Vous avez reçu un accès {access_label} au courrier confidentiel {instance.courrier.reference} de la part de {instance.granted_by.get_full_name() or instance.granted_by.username}.',
            priorite='haute',
            cree_par=instance.granted_by,
            metadata={
                'courrier_id': instance.courrier.id,
                'reference': instance.courrier.reference,
                'access_type': instance.access_type,
                'access_id': instance.id
            }
        )


@receiver(post_delete, sender=CourrierAccess)
def notifier_revocation_acces(sender, instance, **kwargs):
    """Notifier l'utilisateur lorsqu'un accès est révoqué"""
    creer_notification(
        utilisateur=instance.user,
        courrier=instance.courrier,
        type_notification='acces_revoque',
        titre='Accès à un courrier confidentiel révoqué',
        message=f'Votre accès au courrier confidentiel {instance.courrier.reference} a été révoqué.',
        priorite='normale',
        metadata={
            'courrier_id': instance.courrier.id,
            'reference': instance.courrier.reference
        }
    )


@receiver(post_delete, sender=CourrierImputation)
def notifier_suppression_imputation(sender, instance, **kwargs):
    """Notifier l'utilisateur lorsqu'une imputation est supprimée"""
    creer_notification(
        utilisateur=instance.user,
        courrier=instance.courrier,
        type_notification='acces_revoque',
        titre='Imputation de courrier supprimée',
        message=f'Votre imputation sur le courrier {instance.courrier.reference} a été supprimée.',
        priorite='normale',
        metadata={
            'courrier_id': instance.courrier.id,
            'reference': instance.courrier.reference
        }
    )


@receiver(post_save, sender=CourrierStatut)
def notifier_changement_statut(sender, instance, created, **kwargs):
    """Notifier les utilisateurs concernés lors d'un changement de statut"""
    if created:
        # Récupérer tous les utilisateurs ayant une imputation sur ce courrier
        imputations = CourrierImputation.objects.filter(courrier=instance.courrier)
        
        statut_labels = {
            'nouveau': 'Nouveau',
            'en_cours': 'En cours de traitement',
            'traite': 'Traité',
            'archive': 'Archivé'
        }
        
        for imputation in imputations:
            creer_notification(
                utilisateur=imputation.user,
                courrier=instance.courrier,
                type_notification='statut_modifie',
                titre='Statut de courrier modifié',
                message=f'Le statut du courrier {instance.courrier.reference} a été modifié en "{statut_labels.get(instance.statut, instance.statut)}" par {instance.modifie_par.get_full_name() if instance.modifie_par else "le système"}.',
                priorite='normale',
                cree_par=instance.modifie_par,
                metadata={
                    'courrier_id': instance.courrier.id,
                    'reference': instance.courrier.reference,
                    'ancien_statut': kwargs.get('old_statut'),
                    'nouveau_statut': instance.statut
                }
            )


@receiver(post_save, sender=Diligence)
def notifier_creation_diligence(sender, instance, created, **kwargs):
    """Notifier lors de la création d'une diligence liée à un courrier"""
    if created and instance.courrier:
        # Notifier le responsable de la diligence
        if instance.responsable:
            creer_notification(
                utilisateur=instance.responsable,
                courrier=instance.courrier,
                type_notification='diligence_creee',
                titre='Nouvelle diligence créée',
                message=f'Une diligence a été créée pour le courrier {instance.courrier.reference}. Vous en êtes le responsable.',
                priorite='haute',
                cree_par=instance.created_by,
                metadata={
                    'courrier_id': instance.courrier.id,
                    'reference': instance.courrier.reference,
                    'diligence_id': instance.id,
                    'diligence_reference': instance.reference_courrier
                }
            )
        
        # Notifier les agents assignés
        for agent in instance.agents.all():
            if agent != instance.responsable:  # Éviter de notifier deux fois le responsable
                creer_notification(
                    utilisateur=agent,
                    courrier=instance.courrier,
                    type_notification='diligence_creee',
                    titre='Assigné à une nouvelle diligence',
                    message=f'Vous avez été assigné à une diligence pour le courrier {instance.courrier.reference}.',
                    priorite='normale',
                    cree_par=instance.created_by,
                    metadata={
                        'courrier_id': instance.courrier.id,
                        'reference': instance.courrier.reference,
                        'diligence_id': instance.id,
                        'diligence_reference': instance.reference_courrier
                    }
                )


def notifier_rappel_traitement(courrier, utilisateur, message_rappel):
    """Fonction pour créer une notification de rappel de traitement"""
    creer_notification(
        utilisateur=utilisateur,
        courrier=courrier,
        type_notification='rappel_traitement',
        titre='Rappel de traitement de courrier',
        message=message_rappel,
        priorite='urgente',
        metadata={
            'courrier_id': courrier.id,
            'reference': courrier.reference
        }
    )
