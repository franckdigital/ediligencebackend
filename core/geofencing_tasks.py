from celery import shared_task
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import timedelta
import math
from .models import (
    GeofenceAlert, GeofenceSettings, AgentLocation, 
    Bureau, UserProfile
)
from .notifications import send_geofence_notification, send_push_notification


def calculate_distance(lat1, lon1, lat2, lon2):
    """Calcule la distance entre deux points GPS en mètres (formule de Haversine)"""
    R = 6371000  # Rayon de la Terre en mètres
    
    lat1_rad = math.radians(float(lat1))
    lon1_rad = math.radians(float(lon1))
    lat2_rad = math.radians(float(lat2))
    lon2_rad = math.radians(float(lon2))
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c


@shared_task
def check_geofence_violations():
    """
    Tâche périodique pour vérifier les violations de géofencing
    À exécuter toutes les 5 minutes via Celery Beat
    """
    try:
        # Récupérer les paramètres de géofencing
        settings = GeofenceSettings.objects.first()
        if not settings:
            print("Aucune configuration de géofencing trouvée")
            return
        
        now = timezone.now()
        
        # Vérifier si on est dans les heures de travail
        if not settings.is_heure_travail(now):
            print("Hors des heures de travail, pas de vérification nécessaire")
            return
        
        # Récupérer tous les agents actifs
        agents = User.objects.filter(
            profile__role='AGENT',
            is_active=True
        ).select_related('profile', 'agent_profile')
        
        violations_count = 0
        
        for agent in agents:
            try:
                # Récupérer la dernière position de l'agent (dans les 10 dernières minutes)
                recent_location = AgentLocation.objects.filter(
                    agent=agent,
                    timestamp__gte=now - timedelta(minutes=10)
                ).order_by('-timestamp').first()
                
                if not recent_location:
                    continue  # Pas de position récente
                
                # Récupérer le bureau assigné à l'agent
                bureau = None
                if hasattr(agent, 'agent_profile') and agent.agent_profile.bureau:
                    bureau = agent.agent_profile.bureau
                elif hasattr(agent, 'profile') and agent.profile.service:
                    # Chercher un bureau par défaut pour le service
                    # À adapter selon votre logique métier
                    bureau = Bureau.objects.first()
                
                if not bureau:
                    continue  # Pas de bureau assigné
                
                # Calculer la distance
                distance = calculate_distance(
                    recent_location.latitude,
                    recent_location.longitude,
                    bureau.latitude_centre,
                    bureau.longitude_centre
                )
                
                # Vérifier si l'agent est hors de la zone autorisée
                if distance > settings.distance_alerte_metres:
                    # Vérifier depuis quand l'agent est hors de la zone (durée configurable)
                    duree_minimale = timedelta(minutes=settings.duree_minimale_hors_bureau_minutes)
                    time_threshold = now - duree_minimale
                    
                    # Chercher la dernière position dans la zone autorisée
                    last_inside_position = AgentLocation.objects.filter(
                        agent=agent,
                        dans_zone_autorisee=True,
                        timestamp__gte=time_threshold
                    ).order_by('-timestamp').first()
                    
                    # Si aucune position dans la zone dans la période définie, vérifier plus loin
                    if not last_inside_position:
                        # Chercher la dernière position dans la zone (sans limite de temps)
                        last_inside_position = AgentLocation.objects.filter(
                            agent=agent,
                            dans_zone_autorisee=True
                        ).order_by('-timestamp').first()
                        
                        # Si l'agent est hors zone depuis plus que la durée minimale, déclencher l'alerte
                        if last_inside_position and (now - last_inside_position.timestamp) >= duree_minimale:
                            # Vérifier qu'il n'y a pas déjà une alerte active récente
                            recent_alert = GeofenceAlert.objects.filter(
                                agent=agent,
                                bureau=bureau,
                                type_alerte='sortie_zone',
                                statut='active',
                                timestamp_alerte__gte=now - timedelta(hours=2)
                            ).exists()
                            
                            if not recent_alert:
                                # Créer une nouvelle alerte
                                alert = GeofenceAlert.objects.create(
                                    agent=agent,
                                    bureau=bureau,
                                    type_alerte='sortie_zone',
                                    latitude_agent=recent_location.latitude,
                                    longitude_agent=recent_location.longitude,
                                    distance_metres=int(distance),
                                    en_heures_travail=True
                                )
                                
                                # Envoyer les notifications
                                send_geofence_notifications_task.delay(alert.id)
                                violations_count += 1
                                
                                print(f"Alerte créée pour {agent.username}: {int(distance)}m du bureau {bureau.nom}")
            
            except Exception as e:
                print(f"Erreur lors de la vérification pour {agent.username}: {e}")
                continue
        
        print(f"Vérification géofencing terminée: {violations_count} nouvelles alertes créées")
        return violations_count
        
    except Exception as e:
        print(f"Erreur lors de la vérification géofencing: {e}")
        return 0


@shared_task
def send_geofence_notifications_task(alert_id):
    """
    Tâche pour envoyer les notifications de géofencing
    """
    try:
        alert = GeofenceAlert.objects.get(id=alert_id)
        settings = GeofenceSettings.objects.first()
        
        if not settings:
            return
        
        # Récupérer les utilisateurs à notifier
        users_to_notify = []
        
        if settings.notification_directeurs:
            # Notifier les directeurs
            directeurs = User.objects.filter(profile__role='DIRECTEUR')
            users_to_notify.extend(directeurs)
        
        if settings.notification_superieurs:
            # Notifier les supérieurs
            superieurs = User.objects.filter(profile__role='SUPERIEUR')
            users_to_notify.extend(superieurs)
        
        # Envoyer les notifications
        notification_count = 0
        push_count = 0
        
        for user in users_to_notify:
            # Notification dans l'application
            if send_geofence_notification(user, alert):
                notification_count += 1
            
            # Notification push si activée
            if settings.notification_push_active:
                if send_push_notification(user, alert):
                    push_count += 1
        
        # Marquer les notifications comme envoyées
        alert.notification_envoyee = notification_count > 0
        alert.notification_push_envoyee = push_count > 0
        alert.save()
        
        print(f"Notifications envoyées pour l'alerte {alert_id}: {notification_count} app, {push_count} push")
        
    except GeofenceAlert.DoesNotExist:
        print(f"Alerte {alert_id} non trouvée")
    except Exception as e:
        print(f"Erreur lors de l'envoi des notifications pour l'alerte {alert_id}: {e}")


@shared_task
def cleanup_old_locations():
    """
    Tâche pour nettoyer les anciennes positions (garder seulement les 7 derniers jours)
    À exécuter quotidiennement
    """
    try:
        cutoff_date = timezone.now() - timedelta(days=7)
        deleted_count = AgentLocation.objects.filter(timestamp__lt=cutoff_date).delete()[0]
        print(f"Nettoyage des positions: {deleted_count} enregistrements supprimés")
        return deleted_count
    except Exception as e:
        print(f"Erreur lors du nettoyage des positions: {e}")
        return 0


@shared_task
def cleanup_old_alerts():
    """
    Tâche pour nettoyer les anciennes alertes résolues (garder seulement les 30 derniers jours)
    À exécuter hebdomadairement
    """
    try:
        cutoff_date = timezone.now() - timedelta(days=30)
        deleted_count = GeofenceAlert.objects.filter(
            statut__in=['resolue', 'ignoree'],
            date_resolution__lt=cutoff_date
        ).delete()[0]
        print(f"Nettoyage des alertes: {deleted_count} alertes supprimées")
        return deleted_count
    except Exception as e:
        print(f"Erreur lors du nettoyage des alertes: {e}")
        return 0


@shared_task
def generate_geofence_report():
    """
    Tâche pour générer un rapport quotidien des alertes de géofencing
    À exécuter quotidiennement à 18h
    """
    try:
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        
        # Statistiques du jour précédent
        alerts_yesterday = GeofenceAlert.objects.filter(
            date_detection=yesterday
        )
        
        total_alerts = alerts_yesterday.count()
        active_alerts = alerts_yesterday.filter(statut='active').count()
        resolved_alerts = alerts_yesterday.filter(statut='resolue').count()
        ignored_alerts = alerts_yesterday.filter(statut='ignoree').count()
        
        # Agents les plus concernés
        top_agents = alerts_yesterday.values('agent__username').annotate(
            count=models.Count('id')
        ).order_by('-count')[:5]
        
        report = {
            'date': yesterday.isoformat(),
            'total_alerts': total_alerts,
            'active_alerts': active_alerts,
            'resolved_alerts': resolved_alerts,
            'ignored_alerts': ignored_alerts,
            'top_agents': list(top_agents)
        }
        
        print(f"Rapport géofencing du {yesterday}: {total_alerts} alertes")
        
        # Ici, vous pourriez envoyer le rapport par email aux administrateurs
        # ou le sauvegarder dans un modèle de rapport
        
        return report
        
    except Exception as e:
        print(f"Erreur lors de la génération du rapport: {e}")
        return None
