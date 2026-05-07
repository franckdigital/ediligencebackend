from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.utils import timezone

from .models import Tache, SousTache, Projet, NotificationProjet


@receiver(post_save, sender=Tache)
def on_tache_saved(sender, instance, created, **kwargs):
    """
    Quand une tâche est sauvegardée :
    - Si terminée : recalculer l'avancement du projet
    - Si le statut change et que la tâche est en retard : notifier
    """
    if not created:
        # Recalculer l'avancement du projet à chaque modification de tâche
        try:
            instance.projet.mettre_a_jour_avancement()
        except Exception:
            pass


@receiver(post_save, sender=SousTache)
def on_sous_tache_saved(sender, instance, created, **kwargs):
    """
    Quand une sous-tâche est sauvegardée :
    - Recalculer l'avancement de la tâche parent
    """
    if not created:
        try:
            tache = instance.tache
            tache.pourcentage_avancement = tache.calculer_avancement()
            tache.save(update_fields=['pourcentage_avancement', 'updated_at'])
        except Exception:
            pass


@receiver(m2m_changed, sender=Tache.agents_assignes.through)
def on_agents_assignes_changed(sender, instance, action, pk_set, **kwargs):
    """Notifier les agents nouvellement assignés à une tâche."""
    if action == 'post_add' and pk_set:
        from django.contrib.auth.models import User
        nouveaux_agents = User.objects.filter(id__in=pk_set)
        notifs = []
        for agent in nouveaux_agents:
            notifs.append(NotificationProjet(
                user=agent,
                projet=instance.projet,
                tache=instance,
                type_notification='assignation',
                titre=f"Nouvelle assignation : {instance.titre}",
                message=f"Vous avez été assigné à la tâche « {instance.titre} » du projet « {instance.projet.titre} ».",
            ))
        if notifs:
            NotificationProjet.objects.bulk_create(notifs)


@receiver(m2m_changed, sender=Projet.equipe.through)
def on_equipe_changed(sender, instance, action, pk_set, **kwargs):
    """Notifier les membres nouvellement ajoutés à l'équipe du projet."""
    if action == 'post_add' and pk_set:
        from django.contrib.auth.models import User
        nouveaux_membres = User.objects.filter(id__in=pk_set)
        notifs = []
        for membre in nouveaux_membres:
            notifs.append(NotificationProjet(
                user=membre,
                projet=instance,
                type_notification='assignation',
                titre=f"Ajouté au projet : {instance.titre}",
                message=f"Vous faites maintenant partie de l'équipe du projet « {instance.titre} ».",
            ))
        if notifs:
            NotificationProjet.objects.bulk_create(notifs)
