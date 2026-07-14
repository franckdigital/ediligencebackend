"""
Tâches Celery pour la surveillance des présences et sorties
"""
from celery import shared_task
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import datetime, timedelta, time
from .models import Presence, Agent, Bureau, AgentLocation, GeofenceAlert, GeofenceSettings, Notification
from .geofencing_utils import calculate_distance, get_gps_reference_for_user
from .notifications import send_push_to_user
import logging

logger = logging.getLogger(__name__)

# Nombre maximum de points conservés dans une trace (évite les JSON trop volumineux
# pour un agent resté hors zone toute la journée)
MAX_TRACE_POINTS = 200


def _build_trace(agent_user, since, until, ref_lat, ref_lon):
    """
    Construit la trace des positions GPS d'un agent entre deux instants,
    avec la distance par rapport au point de référence (site/bureau) à chaque relevé.
    Sous-échantillonne si nécessaire pour rester sous MAX_TRACE_POINTS.
    """
    locations = list(AgentLocation.objects.filter(
        agent=agent_user,
        timestamp__gte=since,
        timestamp__lte=until,
    ).order_by('timestamp'))

    step = max(1, len(locations) // MAX_TRACE_POINTS)
    trace = []
    for idx, loc in enumerate(locations):
        if idx % step != 0:
            continue
        distance = calculate_distance(float(loc.latitude), float(loc.longitude), ref_lat, ref_lon)
        trace.append({
            'latitude': float(loc.latitude),
            'longitude': float(loc.longitude),
            'timestamp': loc.timestamp.isoformat(),
            'distance_metres': round(distance, 1),
        })
    return trace


@shared_task
def check_agent_exits():
    """
    Détecte les agents éloignés de la zone GPS de leur site (palier actif > site > bureau,
    voir get_gps_reference_for_user) depuis plus d'une heure — seuil configurable via
    GeofenceSettings.seuil_absence_prolongee_minutes (défaut 60 min).

    Pour chaque absence prolongée confirmée :
      - marque automatiquement la sortie sur la présence du jour,
      - enregistre la trace complète des positions GPS relevées pendant l'absence,
      - enregistre la dernière position connue de l'agent,
      - crée une alerte de géofencing dédiée (type 'absence_prolongee') consultable
        depuis le tableau de bord des alertes,
      - notifie la hiérarchie (in-app + push) avec la durée et un lien vers la position.

    Surveillance continue de 7h30 à 22h00.
    Exécutée toutes les 5 minutes par Celery Beat (fréquence des remontées GPS mobile).
    """
    logger.info("🔍 Vérification des sorties d'agents...")

    now = timezone.now()
    current_time = now.time()
    current_date = now.date()

    surveillance_start = time(7, 30)
    surveillance_end = time(22, 0)

    if not (surveillance_start <= current_time <= surveillance_end):
        logger.info("⏰ Hors des heures de surveillance (7h30-22h00), pas de vérification")
        return

    settings_obj = GeofenceSettings.objects.first()
    seuil_minutes = settings_obj.seuil_absence_prolongee_minutes if settings_obj else 60
    time_threshold = timedelta(minutes=seuil_minutes)

    logger.info(f"⏰ Heure actuelle: {current_time} - Seuil d'absence prolongée: {seuil_minutes} min")

    # Récupérer toutes les présences du jour qui ne sont pas encore marquées comme sorties
    presences_today = Presence.objects.filter(
        date_presence=current_date,
        heure_arrivee__isnull=False,  # Agent a pointé arrivée
        heure_depart__isnull=True,    # Pas encore de départ
        sortie_detectee=False,        # Pas encore de sortie détectée
        statut='présent'              # Statut présent
    ).select_related('agent', 'agent__user', 'agent__bureau')

    logger.info(f"📊 {presences_today.count()} présences à vérifier")

    for presence in presences_today:
        try:
            agent = presence.agent
            agent_user = agent.user

            logger.info(f"🔍 Vérification agent: {agent_user.username}")

            ref = get_gps_reference_for_user(agent_user)
            if not ref:
                logger.info(f"❌ Aucune zone GPS configurée (site/palier/bureau) pour {agent_user.username}")
                continue

            ref_lat, ref_lon, ref_rayon = ref['latitude'], ref['longitude'], ref['rayon_metres']

            # Dernière position connue de l'agent aujourd'hui
            last_location = AgentLocation.objects.filter(
                agent=agent_user,
                timestamp__date=current_date
            ).order_by('-timestamp').first()

            if not last_location:
                logger.info(f"❌ Aucune position trouvée pour {agent_user.username}")
                continue

            distance = calculate_distance(
                float(last_location.latitude), float(last_location.longitude), ref_lat, ref_lon
            )

            if distance <= ref_rayon:
                continue  # L'agent est actuellement dans la zone autorisée

            logger.info(f"📏 {agent_user.username} à {distance:.1f}m de {ref['nom']} (rayon {ref_rayon:.0f}m)")

            # Rechercher le début de la sortie continue actuelle (dernier passage en zone -> maintenant)
            # en ignorant les positions aberrantes (>10km, typiques d'un émulateur/mauvais fix GPS)
            all_locations_today = AgentLocation.objects.filter(
                agent=agent_user,
                timestamp__date=current_date
            ).order_by('timestamp')

            first_away_time = None
            for loc in all_locations_today:
                loc_distance = calculate_distance(
                    float(loc.latitude), float(loc.longitude), ref_lat, ref_lon
                )
                if loc_distance > 10000:
                    continue  # position aberrante ignorée
                if loc_distance > ref_rayon:
                    if first_away_time is None:
                        first_away_time = loc.timestamp
                else:
                    # Retour en zone détecté : on repart de zéro pour ne tracer que la sortie en cours
                    first_away_time = None

            if not first_away_time:
                continue

            duree = now - first_away_time
            duree_minutes = int(duree.total_seconds() / 60)

            if duree < time_threshold:
                logger.info(f"⏳ {agent_user.username} hors zone depuis {duree_minutes} min (< {seuil_minutes} min), pas encore d'alerte")
                continue

            logger.warning(f"🚨 ABSENCE PROLONGÉE DÉTECTÉE : {agent_user.username} — {duree_minutes} min hors de {ref['nom']}")

            # Construire la trace complète de l'absence (pour affichage sur carte côté admin)
            trace = _build_trace(agent_user, first_away_time, now, ref_lat, ref_lon)

            # Marquer la sortie sur la présence du jour + enregistrer trace et dernière position
            presence.heure_sortie = first_away_time.time()
            presence.sortie_detectee = True
            presence.statut = 'absent'
            presence.temps_absence_minutes = duree_minutes
            presence.derniere_latitude_connue = last_location.latitude
            presence.derniere_longitude_connue = last_location.longitude
            presence.trace_absence = trace
            presence.commentaire = (
                f"{(presence.commentaire or '').strip()} | Absence prolongée détectée automatiquement : "
                f"{distance:.0f}m de {ref['nom']} depuis {duree_minutes} min"
            ).strip(' |')
            presence.save()

            agent_name = f"{agent.nom} {agent.prenom or ''}".strip() or agent_user.username
            maps_link = f"https://www.google.com/maps?q={last_location.latitude},{last_location.longitude}"

            # Créer une alerte de géofencing dédiée si un bureau est résolvable
            # (visible dans le tableau de bord des alertes existant, avec workflow de résolution)
            bureau = ref.get('bureau')
            if bureau:
                alerte_recente = GeofenceAlert.objects.filter(
                    agent=agent_user, bureau=bureau, type_alerte='absence_prolongee',
                    statut='active', timestamp_alerte__gte=now - timedelta(hours=2)
                ).exists()
                if not alerte_recente:
                    GeofenceAlert.objects.create(
                        agent=agent_user,
                        bureau=bureau,
                        type_alerte='absence_prolongee',
                        latitude_agent=last_location.latitude,
                        longitude_agent=last_location.longitude,
                        distance_metres=int(distance),
                        en_heures_travail=True,
                        duree_hors_zone_minutes=duree_minutes,
                        trace_positions=trace,
                    )

            # Notifier la hiérarchie (in-app + push), avec durée et position
            superieurs = User.objects.filter(
                profile__role__in=['ADMIN', 'DIRECTEUR', 'SOUS_DIRECTEUR', 'CHEF_SERVICE', 'SUPERIEUR'],
                profile__service=agent.service
            ) if agent.service else User.objects.filter(profile__role__in=['ADMIN', 'DIRECTEUR'])
            superieurs = set(superieurs)

            heures = duree_minutes // 60
            minutes = duree_minutes % 60
            duree_str = f"{heures}h{minutes:02d}" if heures else f"{minutes} min"

            titre = f"Absence prolongée : {agent_name}"
            message = (
                f"{agent_name} est éloigné(e) de {ref['nom']} depuis {duree_str} "
                f"(à {distance:.0f}m). Dernière position connue : {maps_link}"
            )

            for superieur in superieurs:
                Notification.objects.create(
                    user=superieur,
                    type_notif='rappel',
                    contenu=message,
                    message=message,
                    lien='/presences',
                    read=False,
                )
                send_push_to_user(superieur, titre, message, data={
                    'type': 'absence_prolongee',
                    'agent_id': str(agent_user.id),
                    'latitude': str(last_location.latitude),
                    'longitude': str(last_location.longitude),
                    'duree_minutes': str(duree_minutes),
                })

            logger.info(f"📧 Notifications d'absence prolongée envoyées à {len(superieurs)} supérieur(s)")

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

            # Essayer de détecter l'heure réelle de départ via GPS
            detected_departure_time = None

            ref = get_gps_reference_for_user(agent.user)
            if ref:
                # Récupérer toutes les positions de l'agent aujourd'hui après 16h30
                positions_after_work = AgentLocation.objects.filter(
                    agent=agent.user,
                    timestamp__date=current_date,
                    timestamp__time__gte=time(16, 30)
                ).order_by('timestamp')

                # Chercher la première position où l'agent s'est éloigné de sa zone
                for location in positions_after_work:
                    distance = calculate_distance(
                        float(location.latitude),
                        float(location.longitude),
                        ref['latitude'],
                        ref['longitude'],
                    )

                    if distance > ref['rayon_metres']:
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
