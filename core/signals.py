from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import UserProfile
from .notifications import send_push_to_user
import secrets

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        role = 'ADMIN' if instance.is_superuser else 'AGENT'
        if not hasattr(instance, 'profile'):
            UserProfile.objects.create(user=instance, role=role)
        elif instance.is_superuser and instance.profile.role != 'ADMIN':
            instance.profile.role = 'ADMIN'
            instance.profile.save(update_fields=['role'])
    elif instance.is_superuser:
        # Superuser promu après coup → on garantit le rôle ADMIN
        try:
            profile = instance.profile
            if profile.role != 'ADMIN':
                profile.role = 'ADMIN'
                profile.save(update_fields=['role'])
        except UserProfile.DoesNotExist:
            UserProfile.objects.create(user=instance, role='ADMIN')

@receiver(post_save, sender=UserProfile)
def create_profile_fields(sender, instance, created, **kwargs):
    updated = False
    if created and not instance.matricule:
        instance.matricule = f"M{instance.id:05d}"
        updated = True
    if updated:
        instance.save()


# --- AUTOMATISATION DES TÂCHES ---

@receiver(pre_save, sender='core.Tache')
def capturer_etat_avant_modification(sender, instance, **kwargs):
    """Mémorise l'état précédent de la tâche avant la sauvegarde."""
    if instance.pk:
        try:
            instance._etat_precedent = sender.objects.get(pk=instance.pk).etat
        except sender.DoesNotExist:
            instance._etat_precedent = None
    else:
        instance._etat_precedent = None


@receiver(post_save, sender='core.Tache')
def automatisation_tache(sender, instance, created, **kwargs):
    """
    - Tâche terminée → notifier le responsable et les supérieurs assignés.
    - Tâche en retard (date_fin_prevue dépassée, non terminée) → créer une alerte.
    """
    from .models import Notification

    etat_precedent = getattr(instance, '_etat_precedent', None)
    aujourd_hui = timezone.now().date()

    # 1. Tâche passée à l'état "terminée" → notifier supérieur(s) et responsable
    if instance.etat == 'terminee' and etat_precedent != 'terminee':
        destinataires = set()

        # Le responsable de la tâche
        if instance.responsable:
            destinataires.add(instance.responsable)

        # Les supérieurs assignés à la tâche (champ M2M superieurs)
        for superieur in instance.superieurs.all():
            destinataires.add(superieur)

        # Le superviseur du domaine si présent
        if instance.domaine and instance.domaine.superviseur:
            destinataires.add(instance.domaine.superviseur)

        for destinataire in destinataires:
            try:
                titre_notif = f"Tâche terminée : « {instance.titre} »"
                msg_notif = (
                    f"La tâche « {instance.titre} » a été marquée comme terminée"
                    + (f" le {instance.date_fin_effective.strftime('%d/%m/%Y')}" if instance.date_fin_effective else "")
                    + "."
                )
                Notification.objects.create(
                    user=destinataire,
                    type_notif='demande_approuvee',
                    contenu=titre_notif,
                    message=msg_notif,
                    lien="/taches"
                )
                # Push mobile
                send_push_to_user(
                    user=destinataire,
                    title=titre_notif,
                    body=msg_notif,
                    data={'type': 'tache_terminee', 'tache_id': str(instance.pk)}
                )
            except Exception:
                pass

    # 1b. Tâche nouvellement créée → notifier les agents assignés
    if created:
        assignes = list(instance.agents_taches.all()) if hasattr(instance, 'agents_taches') else []
        if instance.responsable:
            assignes.append(instance.responsable)
        for agent in set(assignes):
            try:
                Notification.objects.create(
                    user=agent,
                    type_notif='assignation',
                    contenu=f"Nouvelle tâche assignée : « {instance.titre} »",
                    message=f"La tâche « {instance.titre} » vous a été assignée.",
                    lien="/taches"
                )
                send_push_to_user(
                    user=agent,
                    title=f"Tâche assignée 📋",
                    body=f"« {instance.titre} » vous a été assignée.",
                    data={'type': 'tache_assignee', 'tache_id': str(instance.pk)}
                )
            except Exception:
                pass

    # 2. Tâche en retard → alerter le responsable et les supérieurs
    if (
        instance.date_fin_prevue
        and instance.date_fin_prevue < aujourd_hui
        and instance.etat not in ('terminee', 'annulee')
    ):
        destinataires = set()
        if instance.responsable:
            destinataires.add(instance.responsable)
        for superieur in instance.superieurs.all():
            destinataires.add(superieur)
        if instance.domaine and instance.domaine.superviseur:
            destinataires.add(instance.domaine.superviseur)

        for destinataire in destinataires:
            # Évite les doublons : ne crée pas une alerte si une alerte de retard existe déjà aujourd'hui
            existe_deja = Notification.objects.filter(
                user=destinataire,
                type_notif='rappel',
                contenu__startswith=f"RETARD — Tâche : « {instance.titre} »",
            ).filter(created_at__date=aujourd_hui).exists()

            if not existe_deja:
                try:
                    jours_retard = (aujourd_hui - instance.date_fin_prevue).days
                    msg_retard = (
                        f"La tâche « {instance.titre} » est en retard de {jours_retard} jour(s). "
                        f"Date limite : {instance.date_fin_prevue.strftime('%d/%m/%Y')}. "
                        f"État actuel : {instance.get_etat_display()}."
                    )
                    Notification.objects.create(
                        user=destinataire,
                        type_notif='rappel',
                        contenu=f"RETARD — Tâche : « {instance.titre} »",
                        message=msg_retard,
                        lien="/taches"
                    )
                    send_push_to_user(
                        user=destinataire,
                        title=f"Tâche en retard ⚠️",
                        body=f"« {instance.titre} » — {jours_retard} jour(s) de retard.",
                        data={'type': 'tache_retard', 'tache_id': str(instance.pk)}
                    )
                except Exception:
                    pass