import json
import requests
from django.conf import settings
from django.contrib.auth.models import User
from .models import Notification, PushNotificationToken, GeofenceAlert


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


def create_geofence_notification_types():
    """Créer les types de notifications pour le géofencing (à exécuter lors de la migration)"""
    from .models import Notification
    
    # Ajouter le nouveau type de notification si ce n'est pas déjà fait
    # Cette fonction peut être appelée dans une migration de données
    pass
