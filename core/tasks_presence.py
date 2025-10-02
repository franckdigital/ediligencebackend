"""
Tâches Celery pour la surveillance des présences et sorties
"""
from celery import shared_task
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import datetime, timedelta, time
from .models import Presence, Agent, Bureau, AgentLocation
from .geofencing_utils import calculate_distance
import logging

logger = logging.getLogger(__name__)

@shared_task
def check_agent_exits():
    """
    Vérifier si des agents se sont éloignés de plus de 200m du bureau
    pendant plus d'une heure et marquer leur sortie automatiquement
    """
    logger.info("🔍 Vérification des sorties d'agents...")
    
    # Obtenir l'heure actuelle
    now = timezone.now()
    current_time = now.time()
    current_date = now.date()
    
    # Vérifier seulement pendant les heures de travail (7h30-16h30)
    work_start = time(7, 30)
    work_end = time(16, 30)
    
    if not (work_start <= current_time <= work_end):
        logger.info("⏰ Hors heures de travail, pas de vérification")
        return
    
    # Récupérer toutes les présences du jour qui ne sont pas encore marquées comme sorties
    presences_today = Presence.objects.filter(
        date_presence=current_date,
        heure_arrivee__isnull=False,  # Agent a pointé arrivée
        heure_depart__isnull=True,    # Pas encore de départ
        sortie_detectee=False,        # Pas encore de sortie détectée
        statut='présent'              # Statut présent
    )
    
    logger.info(f"📊 {presences_today.count()} présences à vérifier")
    
    for presence in presences_today:
        try:
            agent = presence.agent
            bureau = agent.bureau
            
            logger.info(f"🔍 Vérification agent: {agent.user.username}")
            
            if not bureau or not bureau.latitude_centre or not bureau.longitude_centre:
                logger.info(f"❌ Bureau manquant ou coordonnées manquantes pour {agent.user.username}")
                continue
            
            # Récupérer la dernière position de l'agent
            last_location = AgentLocation.objects.filter(
                agent=agent.user,  # AgentLocation utilise User, pas Agent
                timestamp__date=current_date
            ).order_by('-timestamp').first()
            
            if not last_location:
                logger.info(f"❌ Aucune position trouvée pour {agent.user.username}")
                continue
            
            logger.info(f"📍 Dernière position: {last_location.latitude}, {last_location.longitude} à {last_location.timestamp}")
            
            # Calculer la distance par rapport au bureau
            distance = calculate_distance(
                float(last_location.latitude),
                float(last_location.longitude),
                float(bureau.latitude_centre),
                float(bureau.longitude_centre)
            )
            
            logger.info(f"📏 Distance calculée: {distance:.1f}m du bureau")
            
            # Si l'agent est à plus de 200m
            if distance > 200:
                logger.info(f"⚠️ Agent éloigné: {distance:.1f}m > 200m")
                # Vérifier depuis combien de temps il est loin
                locations_away = AgentLocation.objects.filter(
                    agent=agent.user,  # AgentLocation utilise User, pas Agent
                    timestamp__date=current_date,
                    timestamp__gte=now - timedelta(hours=1)
                ).order_by('timestamp')
                
                logger.info(f"🕐 Positions des 60 dernières minutes: {locations_away.count()}")
                
                # Vérifier si toutes les positions des 60 dernières minutes sont > 200m
                all_away = True
                first_away_time = None
                
                for loc in locations_away:
                    logger.info(f"   📍 {loc.timestamp.strftime('%H:%M')} - Lat: {loc.latitude}, Lon: {loc.longitude}")
                    loc_distance = calculate_distance(
                        float(loc.latitude),
                        float(loc.longitude),
                        float(bureau.latitude_centre),
                        float(bureau.longitude_centre)
                    )
                    
                    logger.info(f"      Distance: {loc_distance:.1f}m")
                    
                    if loc_distance <= 200:
                        logger.info(f"      ✅ Position proche trouvée, agent pas toujours loin")
                        all_away = False
                        break
                    elif first_away_time is None:
                        first_away_time = loc.timestamp
                        logger.info(f"      🕐 Première position loin: {first_away_time.strftime('%H:%M')}")
                
                logger.info(f"🔍 Résultat vérification:")
                logger.info(f"   all_away: {all_away}")
                logger.info(f"   first_away_time: {first_away_time}")
                if first_away_time:
                    duration = now - first_away_time
                    logger.info(f"   Durée d'absence: {duration.total_seconds()/60:.1f} minutes")
                
                # Si l'agent est loin depuis plus d'une heure
                if all_away and first_away_time and (now - first_away_time) >= timedelta(hours=1):
                    logger.info(f"🚨 SORTIE DÉTECTÉE ! Agent loin depuis plus d'1h")
                    # Calculer l'heure de sortie (maintenant - 1 heure)
                    heure_sortie = (now - timedelta(hours=1)).time()
                    
                    # Marquer la sortie automatique
                    presence.heure_sortie = heure_sortie
                    presence.sortie_detectee = True
                    presence.statut = 'absent'
                    presence.temps_absence_minutes = int((now - (now - timedelta(hours=1))).total_seconds() / 60)
                    presence.commentaire = f"Sortie automatique détectée - Distance: {distance:.1f}m du bureau"
                    presence.save()
                    
                    logger.info(f"🚨 Sortie détectée: {agent.username} - Distance: {distance:.1f}m - Heure sortie: {heure_sortie}")
                    
                    # Créer une notification pour les supérieurs
                    from .models import Notification
                    
                    # Trouver les supérieurs hiérarchiques
                    superieurs = User.objects.filter(
                        profile__role__in=['ADMIN', 'DIRECTEUR', 'SOUS_DIRECTEUR', 'CHEF_SERVICE'],
                        profile__service=agent.service
                    )
                    
                    for superieur in superieurs:
                        Notification.objects.create(
                            user=superieur,
                            type='sortie_detectee',
                            title='Sortie automatique détectée',
                            message=f"{agent.nom} {agent.prenom} s'est éloigné du bureau (distance: {distance:.1f}m) depuis plus d'une heure. Sortie marquée à {heure_sortie.strftime('%H:%M')}.",
                            data={
                                'agent_id': agent.id,
                                'presence_id': presence.id,
                                'distance': distance,
                                'heure_sortie': heure_sortie.strftime('%H:%M')
                            }
                        )
                    
                    logger.info(f"📧 Notifications envoyées à {superieurs.count()} supérieurs")
        
        except Exception as e:
            logger.error(f"❌ Erreur lors de la vérification pour {presence.agent.username}: {e}")
    
    logger.info("✅ Vérification des sorties terminée")

@shared_task
def update_presence_departure_status():
    """
    Mettre à jour le statut des boutons de départ sur l'application mobile
    en fonction des sorties détectées
    """
    logger.info("🔄 Mise à jour du statut des départs...")
    
    current_date = timezone.now().date()
    
    # Récupérer toutes les présences avec sortie détectée
    presences_with_exit = Presence.objects.filter(
        date_presence=current_date,
        sortie_detectee=True,
        statut='absent'
    )
    
    logger.info(f"📊 {presences_with_exit.count()} présences avec sortie détectée")
    
    # Pour chaque présence, on peut ajouter une logique supplémentaire
    # comme envoyer des notifications push aux applications mobiles
    # pour griser le bouton "Pointer Départ"
    
    for presence in presences_with_exit:
        logger.info(f"🔒 Bouton départ grisé pour {presence.agent.username}")
    
    logger.info("✅ Mise à jour du statut des départs terminée")
