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
    
    # Vérifier seulement pendant les heures de travail (7h30-12h30 et 13h30-16h30)
    morning_start = time(7, 30)
    morning_end = time(12, 30)
    afternoon_start = time(13, 30)
    afternoon_end = time(16, 30)
    
    # Vérifier si on est dans les heures de travail (matin ou après-midi)
    is_morning = morning_start <= current_time <= morning_end
    is_afternoon = afternoon_start <= current_time <= afternoon_end
    
    # MODE TEST: Désactiver temporairement la vérification des heures
    FORCE_CHECK = False  # Mettre à False pour réactiver la vérification des heures
    
    if not FORCE_CHECK and not (is_morning or is_afternoon):
        logger.info("⏰ Hors heures de travail (pause déjeuner ou hors horaires), pas de vérification")
        return
    
    logger.info(f"⏰ Heure actuelle: {current_time} - Vérification en cours")
    
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
            
            # MODE TEST: Si l'agent est à plus de 200m et plus de 5 minutes
            TEST_MODE = True  # Mettre à False pour revenir au mode normal
            distance_threshold = 200 if TEST_MODE else 200
            time_threshold = timedelta(minutes=5) if TEST_MODE else timedelta(hours=1)
            
            if distance > distance_threshold:
                logger.info(f"⚠️ Agent éloigné: {distance:.1f}m > {distance_threshold}m")
                # Vérifier depuis combien de temps il est loin
                locations_recent = AgentLocation.objects.filter(
                    agent=agent.user,  # AgentLocation utilise User, pas Agent
                    timestamp__date=current_date,
                    timestamp__gte=now - time_threshold
                ).order_by('timestamp')
                
                logger.info(f"🕐 Positions récentes: {locations_recent.count()}")
                
                # Vérifier si toutes les positions récentes sont éloignées
                all_away = True
                
                for loc in locations_recent:
                    logger.info(f"   📍 {loc.timestamp.strftime('%H:%M')} - Lat: {loc.latitude}, Lon: {loc.longitude}")
                    loc_distance = calculate_distance(
                        float(loc.latitude),
                        float(loc.longitude),
                        float(bureau.latitude_centre),
                        float(bureau.longitude_centre)
                    )
                    
                    logger.info(f"      Distance: {loc_distance:.1f}m")
                    
                    if loc_distance <= distance_threshold:
                        logger.info(f"      ✅ Position proche trouvée, agent pas toujours loin")
                        all_away = False
                        break
                
                # Si toutes les positions récentes sont éloignées, chercher la VRAIE première position éloignée
                first_away_time = None
                if all_away:
                    # Chercher toutes les positions du jour, triées par timestamp
                    all_locations_today = AgentLocation.objects.filter(
                        agent=agent.user,
                        timestamp__date=current_date
                    ).order_by('timestamp')
                    
                    logger.info(f"🔍 Recherche de la première position éloignée parmi {all_locations_today.count()} positions du jour")
                    
                    for loc in all_locations_today:
                        loc_distance = calculate_distance(
                            float(loc.latitude),
                            float(loc.longitude),
                            float(bureau.latitude_centre),
                            float(bureau.longitude_centre)
                        )
                        
                        if loc_distance > distance_threshold:
                            first_away_time = loc.timestamp
                            logger.info(f"      🎯 VRAIE première position éloignée: {first_away_time.strftime('%H:%M')} - Distance: {loc_distance:.1f}m")
                            break
                
                logger.info(f"🔍 Résultat vérification:")
                logger.info(f"   all_away: {all_away}")
                logger.info(f"   first_away_time: {first_away_time}")
                if first_away_time:
                    duration = now - first_away_time
                    logger.info(f"   Durée d'absence: {duration.total_seconds()/60:.1f} minutes")
                
                # Si l'agent est loin depuis le temps défini (1 minute en mode test, 1 heure en mode normal)
                if all_away and first_away_time and (now - first_away_time) >= time_threshold:
                    duration_minutes = int((now - first_away_time).total_seconds() / 60)
                    logger.info(f"🚨 SORTIE DÉTECTÉE ! Agent loin depuis {duration_minutes} minutes")
                    # Calculer l'heure de sortie (première position éloignée)
                    heure_sortie = first_away_time.time()
                    
                    # Marquer la sortie automatique
                    presence.heure_sortie = heure_sortie
                    presence.sortie_detectee = True
                    presence.statut = 'absent'
                    presence.temps_absence_minutes = duration_minutes
                    presence.commentaire = f"Sortie automatique détectée - Distance: {distance:.1f}m du bureau (MODE TEST: {distance_threshold}m, {int(time_threshold.total_seconds()/60)}min)"
                    presence.save()
                    
                    agent_name = agent.user.username if hasattr(agent, 'user') else f"{agent.nom} {agent.prenom}"
                    logger.info(f"🚨 Sortie détectée: {agent_name} - Distance: {distance:.1f}m - Heure sortie: {heure_sortie}")
                    
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
                            type_notif='rappel',  # Utiliser un type existant
                            contenu=f"Sortie automatique détectée: {agent.nom} {agent.prenom} s'est éloigné du bureau (distance: {distance:.1f}m) depuis plus d'une heure. Sortie marquée à {heure_sortie.strftime('%H:%M')}.",
                            message=f"Sortie automatique: {agent.nom} {agent.prenom}",
                            lien=f"/presences"
                        )
                    
                    logger.info(f"📧 Notifications envoyées à {superieurs.count()} supérieurs")
        
        except Exception as e:
            agent_name = presence.agent.user.username if hasattr(presence.agent, 'user') else str(presence.agent)
            logger.error(f"❌ Erreur lors de la vérification pour {agent_name}: {e}")
    
    logger.info("✅ Vérification des sorties terminée")

@shared_task
def auto_close_forgotten_departures():
    """
    Fermer automatiquement les présences dont le départ n'a pas été pointé
    après la fin de la journée de travail (16h30)
    Cette tâche s'exécute à 17h00 pour marquer les départs oubliés à 16h30
    """
    logger.info("🔚 Vérification des départs oubliés...")
    
    now = timezone.now()
    current_date = now.date()
    current_time = now.time()
    
    # Ne s'exécuter qu'après 17h00
    if current_time < time(17, 0):
        logger.info("⏰ Trop tôt pour fermer les présences (avant 17h)")
        return
    
    # Récupérer les présences sans départ pointé
    presences_without_departure = Presence.objects.filter(
        date_presence=current_date,
        heure_arrivee__isnull=False,  # A pointé l'arrivée
        heure_depart__isnull=True,    # N'a pas pointé le départ
        sortie_detectee=False          # Pas de sortie automatique détectée
    )
    
    logger.info(f"📊 {presences_without_departure.count()} présences sans départ pointé")
    
    for presence in presences_without_departure:
        try:
            agent = presence.agent
            bureau = agent.bureau
            
            # Essayer de détecter l'heure réelle de départ via GPS
            detected_departure_time = None
            
            if bureau and bureau.latitude_centre and bureau.longitude_centre:
                # Récupérer toutes les positions de l'agent aujourd'hui après 16h30
                positions_after_work = AgentLocation.objects.filter(
                    agent=agent.user,
                    timestamp__date=current_date,
                    timestamp__time__gte=time(16, 30)
                ).order_by('timestamp')
                
                # Chercher la première position où l'agent s'est éloigné du bureau (>200m)
                for location in positions_after_work:
                    distance = calculate_distance(
                        float(location.latitude),
                        float(location.longitude),
                        float(bureau.latitude_centre),
                        float(bureau.longitude_centre)
                    )
                    
                    if distance > 200:
                        # Première position éloignée = heure de départ
                        detected_departure_time = location.timestamp.time()
                        logger.info(f"📍 Départ détecté via GPS à {detected_departure_time} (distance: {distance:.1f}m)")
                        break
            
            # Si on a détecté l'heure via GPS, l'utiliser, sinon 16h30 par défaut
            if detected_departure_time:
                presence.heure_depart = detected_departure_time
                presence.commentaire = f"{presence.commentaire or ''} | Départ détecté automatiquement via GPS".strip()
            else:
                presence.heure_depart = time(16, 30)
                presence.commentaire = f"{presence.commentaire or ''} | Départ automatique à 16h30 (non pointé, pas de données GPS)".strip()
            
            presence.save()
            
            agent_name = presence.agent.user.username if hasattr(presence.agent, 'user') else str(presence.agent)
            logger.info(f"✅ Départ automatique marqué pour {agent_name} à {presence.heure_depart}")
            
        except Exception as e:
            agent_name = presence.agent.user.username if hasattr(presence.agent, 'user') else str(presence.agent)
            logger.error(f"❌ Erreur lors de la fermeture pour {agent_name}: {e}")
    
    logger.info("✅ Fermeture automatique des présences terminée")

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
