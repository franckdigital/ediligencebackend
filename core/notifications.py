import json
import requests
from django.conf import settings
from django.contrib.auth.models import User
from .models import Notification, PushNotificationToken, GeofenceAlert


# ── Generic notification helper ───────────────────────────────────────────────

def create_notification(user, type_notif, titre, message, lien='', extra_data=None):
    """
    Crée une notification in-app pour un utilisateur donné.
    Peut être importée et appelée depuis n'importe quelle vue/signal du projet.

    Paramètres:
        user        : instance django User (destinataire)
        type_notif  : str — clé de type (voir TYPE_MAP ci-dessous)
        titre       : str — titre court affiché dans la liste
        message     : str — corps du message
        lien        : str — URL relative frontend pour le lien "voir"
        extra_data  : dict optionnel — données supplémentaires sérialisées en JSON

    Retourne: instance Notification ou None en cas d'erreur
    """
    try:
        notif = Notification.objects.create(
            user=user,
            type_notif=type_notif,
            titre=titre,
            contenu=message,
            message=message,
            lien=lien,
            read=False,
        )
        return notif
    except Exception as e:
        print(f"[Notifications] Erreur création notification pour {user}: {e}")
        return None


def notify_users(users, type_notif, titre, message, lien=''):
    """Envoie la même notification à une liste d'utilisateurs."""
    results = []
    for user in users:
        n = create_notification(user, type_notif, titre, message, lien)
        if n:
            results.append(n)
    return results


# ── Diligences ────────────────────────────────────────────────────────────────

def notify_nouvelle_diligence(diligence):
    """Notifie les impactés + superviseurs d'une nouvelle diligence."""
    from .models import Diligence
    try:
        titre = f"Nouvelle diligence : {diligence.objet or diligence.reference or '—'}"
        message = f"Une nouvelle diligence a été créée et vous a été assignée."
        lien = f"/diligences"
        users_to_notify = set()

        if diligence.responsable and diligence.responsable != diligence.createur:
            users_to_notify.add(diligence.responsable)
        # Notifier aussi les imputés
        for imp in diligence.imputations.select_related('agent').all():
            if imp.agent and imp.agent != diligence.createur:
                users_to_notify.add(imp.agent)

        notify_users(list(users_to_notify), 'nouvelle_diligence', titre, message, lien)
    except Exception as e:
        print(f"[Notifications] notify_nouvelle_diligence: {e}")


def notify_diligence_validated(diligence):
    """Notifie le créateur que sa diligence a été validée."""
    try:
        titre = f"Diligence validée : {diligence.objet or diligence.reference or '—'}"
        message = "Votre diligence a été validée."
        lien = "/diligences"
        if diligence.createur:
            create_notification(diligence.createur, 'document_valide', titre, message, lien)
    except Exception as e:
        print(f"[Notifications] notify_diligence_validated: {e}")


def notify_diligence_rappel(diligence):
    """Rappel d'échéance imminente sur une diligence."""
    try:
        titre = f"Délai imminant : {diligence.objet or diligence.reference or '—'}"
        message = f"Le délai de cette diligence est proche. Date limite : {diligence.date_limite}"
        lien = "/diligences"
        users = set()
        if diligence.responsable:
            users.add(diligence.responsable)
        if diligence.createur:
            users.add(diligence.createur)
        notify_users(list(users), 'rappel_delai', titre, message, lien)
    except Exception as e:
        print(f"[Notifications] notify_diligence_rappel: {e}")


# ── Courriers ─────────────────────────────────────────────────────────────────

def notify_nouveau_courrier(courrier, recipient):
    """Notifie un utilisateur qu'un courrier lui est imputable."""
    try:
        titre = f"Nouveau courrier : {courrier.objet or courrier.reference or '—'}"
        message = "Un courrier vous a été imputable ou transmis."
        lien = "/courriers"
        create_notification(recipient, 'nouvelle_diligence', titre, message, lien)
    except Exception as e:
        print(f"[Notifications] notify_nouveau_courrier: {e}")


# ── Congés & Absences ─────────────────────────────────────────────────────────

def notify_conge_soumis(demande):
    """Notifie les approbateurs d'une nouvelle demande de congé."""
    try:
        from django.contrib.auth.models import User as DjUser
        titre = f"Nouvelle demande de congé — {demande.user.get_full_name() or demande.user.username}"
        message = f"Type : {demande.type_conge} | Du {demande.date_debut} au {demande.date_fin}"
        lien = "/personnel/conges"
        approbateurs = DjUser.objects.filter(
            profile__role__in=['ADMIN', 'DIRECTEUR', 'CHEF_SERVICE']
        )
        notify_users(list(approbateurs), 'validation_requise', titre, message, lien)
    except Exception as e:
        print(f"[Notifications] notify_conge_soumis: {e}")


def notify_conge_decision(demande):
    """Notifie l'agent de la décision sur sa demande de congé."""
    try:
        statut = demande.statut
        titre = f"Congé {'approuvé' if statut == 'approuve' else 'refusé'}"
        message = f"Votre demande de congé du {demande.date_debut} au {demande.date_fin} a été {statut}."
        lien = "/personnel/conges"
        type_notif = 'document_valide' if statut == 'approuve' else 'changement_statut'
        create_notification(demande.user, type_notif, titre, message, lien)
    except Exception as e:
        print(f"[Notifications] notify_conge_decision: {e}")


def notify_absence_soumise(demande):
    """Notifie les approbateurs d'une demande d'absence."""
    try:
        from django.contrib.auth.models import User as DjUser
        titre = f"Demande d'absence — {demande.user.get_full_name() or demande.user.username}"
        message = f"Motif : {demande.motif} | Date : {demande.date_debut}"
        lien = "/personnel/absences"
        approbateurs = DjUser.objects.filter(
            profile__role__in=['ADMIN', 'DIRECTEUR', 'CHEF_SERVICE']
        )
        notify_users(list(approbateurs), 'validation_requise', titre, message, lien)
    except Exception as e:
        print(f"[Notifications] notify_absence_soumise: {e}")


def notify_absence_decision(demande):
    """Notifie l'agent de la décision sur sa demande d'absence."""
    try:
        statut = demande.statut
        titre = f"Absence {'approuvée' if statut == 'approuve' else 'refusée'}"
        message = f"Votre demande d'absence du {demande.date_debut} a été {statut}."
        lien = "/personnel/absences"
        type_notif = 'document_valide' if statut == 'approuve' else 'changement_statut'
        create_notification(demande.user, type_notif, titre, message, lien)
    except Exception as e:
        print(f"[Notifications] notify_absence_decision: {e}")


# ── Projets & Tâches ──────────────────────────────────────────────────────────

def notify_tache_assignee(tache, assigned_user):
    """Notifie un agent qu'une tâche lui a été assignée."""
    try:
        titre = f"Nouvelle tâche assignée : {tache.titre}"
        message = f"Une tâche vous a été assignée dans le projet : {getattr(tache, 'projet', None) and tache.projet.nom or '—'}"
        lien = "/projets"
        create_notification(assigned_user, 'assignation', titre, message, lien)
    except Exception as e:
        print(f"[Notifications] notify_tache_assignee: {e}")


def notify_tache_terminee(tache):
    """Notifie le chef de projet qu'une tâche est terminée."""
    try:
        if not hasattr(tache, 'projet') or not tache.projet:
            return
        titre = f"Tâche terminée : {tache.titre}"
        message = f"La tâche «{tache.titre}» a été marquée comme terminée."
        lien = "/projets"
        chef = getattr(tache.projet, 'responsable', None) or getattr(tache.projet, 'chef', None)
        if chef:
            create_notification(chef, 'tache_terminee', titre, message, lien)
    except Exception as e:
        print(f"[Notifications] notify_tache_terminee: {e}")


# ── Réunions ──────────────────────────────────────────────────────────────────

def notify_invitation_reunion(reunion, participant):
    """Notifie un participant d'une invitation à une réunion."""
    try:
        titre = f"Invitation : {reunion.titre or reunion.objet or 'Réunion'}"
        message = f"Vous êtes invité(e) à une réunion le {reunion.date_reunion or '—'}."
        lien = "/agenda"
        create_notification(participant, 'assignation', titre, message, lien)
    except Exception as e:
        print(f"[Notifications] notify_invitation_reunion: {e}")


# ── Géofencing (existant, conservé) ──────────────────────────────────────────

def send_geofence_notification(user, alert):
    """Envoyer une notification dans l'application pour une alerte de géofencing"""
    try:
        # Créer une notification dans la base de données
        notification = Notification.objects.create(
            user=user,
            type_notif='geofence_alert',
            contenu=alert.message_alerte,
            message=alert.message_alerte,
            lien=f'/geofencing/alerts/{alert.id}',
            read=False
        )
        
        return notification
    except Exception as e:
        print(f"Erreur lors de l'envoi de la notification géofencing: {e}")
        return None


def send_push_notification(user, alert):
    """Envoyer une notification push pour une alerte de géofencing"""
    try:
        # Récupérer les tokens actifs de l'utilisateur
        tokens = PushNotificationToken.objects.filter(
            user=user,
            is_active=True
        )
        
        if not tokens.exists():
            return False
        
        # Préparer le message
        title = "Alerte de géofencing"
        body = alert.message_alerte
        
        # Données supplémentaires
        data = {
            'type': 'geofence_alert',
            'alert_id': str(alert.id),
            'agent_name': alert.agent.get_full_name() or alert.agent.username,
            'bureau_name': alert.bureau.nom,
            'distance': str(alert.distance_metres),
            'timestamp': alert.timestamp_alerte.isoformat()
        }
        
        success_count = 0
        
        for token in tokens:
            if token.platform == 'android':
                success = send_fcm_notification(token.token, title, body, data)
            elif token.platform == 'ios':
                success = send_apns_notification(token.token, title, body, data)
            else:
                success = send_web_notification(token.token, title, body, data)
            
            if success:
                success_count += 1
                token.last_used = alert.timestamp_alerte
                token.save()
        
        return success_count > 0
        
    except Exception as e:
        print(f"Erreur lors de l'envoi de la notification push: {e}")
        return False


def send_fcm_notification(token, title, body, data):
    """Envoyer une notification FCM pour Android"""
    try:
        # Configuration FCM (à adapter selon votre configuration)
        fcm_server_key = getattr(settings, 'FCM_SERVER_KEY', None)
        if not fcm_server_key:
            print("FCM_SERVER_KEY non configuré")
            return False
        
        url = 'https://fcm.googleapis.com/fcm/send'
        headers = {
            'Authorization': f'key={fcm_server_key}',
            'Content-Type': 'application/json',
        }
        
        payload = {
            'to': token,
            'notification': {
                'title': title,
                'body': body,
                'sound': 'default',
                'priority': 'high'
            },
            'data': data,
            'priority': 'high'
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            return result.get('success', 0) > 0
        else:
            print(f"Erreur FCM: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"Erreur lors de l'envoi FCM: {e}")
        return False


def send_apns_notification(token, title, body, data):
    """Envoyer une notification APNS pour iOS"""
    try:
        # Configuration APNS (à adapter selon votre configuration)
        # Vous devrez configurer les certificats APNS appropriés
        
        # Pour l'instant, retourner True comme placeholder
        # Dans une implémentation réelle, vous utiliseriez une bibliothèque comme PyAPNs2
        print(f"APNS notification à implémenter pour token: {token[:20]}...")
        return True
        
    except Exception as e:
        print(f"Erreur lors de l'envoi APNS: {e}")
        return False


def send_web_notification(token, title, body, data):
    """Envoyer une notification web push"""
    try:
        # Configuration Web Push (à adapter selon votre configuration)
        # Vous devrez configurer les clés VAPID appropriées
        
        # Pour l'instant, retourner True comme placeholder
        # Dans une implémentation réelle, vous utiliseriez une bibliothèque comme pywebpush
        print(f"Web push notification à implémenter pour token: {token[:20]}...")
        return True
        
    except Exception as e:
        print(f"Erreur lors de l'envoi Web Push: {e}")
        return False


def send_bulk_geofence_notifications(alerts):
    """Envoyer des notifications en lot pour plusieurs alertes"""
    success_count = 0
    
    for alert in alerts:
        # Récupérer les utilisateurs à notifier selon les paramètres
        from .models import GeofenceSettings
        settings = GeofenceSettings.objects.first()
        
        if not settings:
            continue
        
        users_to_notify = []
        
        if settings.notification_directeurs:
            directeurs = User.objects.filter(profile__role='DIRECTEUR')
            users_to_notify.extend(directeurs)
        
        if settings.notification_superieurs:
            superieurs = User.objects.filter(profile__role='SUPERIEUR')
            users_to_notify.extend(superieurs)
        
        # Envoyer les notifications
        for user in users_to_notify:
            if send_geofence_notification(user, alert):
                success_count += 1
            
            if settings.notification_push_active:
                send_push_notification(user, alert)
    
    return success_count


def send_push_to_user(user, title: str, body: str, data: dict = None):
    """
    Envoie une notification push à TOUS les appareils actifs d'un utilisateur.
    Supporte Expo Push (token commençant par ExponentPushToken),
    FCM (Android), APNS (iOS).
    Silencieux en cas d'erreur — ne pas bloquer le signal/vue appelant.
    """
    try:
        tokens = PushNotificationToken.objects.filter(user=user, is_active=True)
        if not tokens.exists():
            return

        payload_data = data or {}

        for token_obj in tokens:
            tok = token_obj.token

            # ── Expo Push Notification Service ──────────────────────────────
            if tok.startswith('ExponentPushToken') or tok.startswith('ExpoPushToken'):
                try:
                    response = requests.post(
                        'https://exp.host/--/api/v2/push/send',
                        headers={
                            'Accept': 'application/json',
                            'Accept-Encoding': 'gzip, deflate',
                            'Content-Type': 'application/json',
                        },
                        json={
                            'to': tok,
                            'title': title,
                            'body': body,
                            'data': payload_data,
                            'sound': 'default',
                            'priority': 'high',
                            'channelId': 'ediligence',
                        },
                        timeout=8,
                    )
                    if response.status_code != 200:
                        print(f"[Push] Expo error {response.status_code}: {response.text[:200]}")
                except Exception as e:
                    print(f"[Push] Expo exception: {e}")

            # ── FCM (Android natif) ──────────────────────────────────────────
            elif token_obj.platform == 'android':
                send_fcm_notification(tok, title, body, payload_data)

            # ── APNS (iOS natif) ─────────────────────────────────────────────
            elif token_obj.platform == 'ios':
                send_apns_notification(tok, title, body, payload_data)

    except Exception as e:
        print(f"[Push] send_push_to_user error: {e}")


def create_geofence_notification_types():
    """Créer les types de notifications pour le géofencing (à exécuter lors de la migration)"""
    from .models import Notification
    
    # Ajouter le nouveau type de notification si ce n'est pas déjà fait
    # Cette fonction peut être appelée dans une migration de données
    pass
