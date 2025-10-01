import math
from datetime import datetime, timedelta
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import (
    GeofenceAlert, GeofenceSettings, AgentLocation, 
    PushNotificationToken, Bureau, UserProfile
)
from .geofencing_serializers import (
    GeofenceAlertSerializer, GeofenceSettingsSerializer,
    AgentLocationSerializer, PushNotificationTokenSerializer,
    LocationUpdateSerializer
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


class GeofenceAlertViewSet(viewsets.ModelViewSet):
    serializer_class = GeofenceAlertSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        profile = getattr(user, 'profile', None)
        
        # ADMIN peut voir toutes les alertes
        if profile and profile.role == 'ADMIN':
            return GeofenceAlert.objects.all()
        
        # DIRECTEUR peut voir les alertes de sa direction
        elif profile and profile.role == 'DIRECTEUR':
            if profile.direction:
                # Récupérer tous les agents de la direction
                agents_direction = User.objects.filter(
                    Q(profile__service__direction=profile.direction) |
                    Q(agent_profile__service__direction=profile.direction)
                )
                return GeofenceAlert.objects.filter(agent__in=agents_direction)
        
        # SUPERIEUR peut voir les alertes de son service
        elif profile and profile.role == 'SUPERIEUR':
            if profile.service:
                agents_service = User.objects.filter(
                    Q(profile__service=profile.service) |
                    Q(agent_profile__service=profile.service)
                )
                return GeofenceAlert.objects.filter(agent__in=agents_service)
        
        # Par défaut, voir seulement ses propres alertes
        return GeofenceAlert.objects.filter(agent=user)
    
    @action(detail=True, methods=['post'])
    def resoudre(self, request, pk=None):
        """Marquer une alerte comme résolue"""
        alerte = self.get_object()
        commentaire = request.data.get('commentaire_resolution', '')
        
        alerte.statut = 'resolue'
        alerte.resolu_par = request.user
        alerte.date_resolution = timezone.now()
        alerte.commentaire_resolution = commentaire
        alerte.save()
        
        return Response({'message': 'Alerte marquée comme résolue'})
    
    @action(detail=True, methods=['post'])
    def ignorer(self, request, pk=None):
        """Marquer une alerte comme ignorée"""
        alerte = self.get_object()
        commentaire = request.data.get('commentaire_resolution', '')
        
        alerte.statut = 'ignoree'
        alerte.resolu_par = request.user
        alerte.date_resolution = timezone.now()
        alerte.commentaire_resolution = commentaire
        alerte.save()
        
        return Response({'message': 'Alerte ignorée'})
    
    @action(detail=False, methods=['get'])
    def alertes_actives(self, request):
        """Récupérer uniquement les alertes actives"""
        queryset = self.get_queryset().filter(statut='active')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class GeofenceSettingsViewSet(viewsets.ModelViewSet):
    queryset = GeofenceSettings.objects.all()
    serializer_class = GeofenceSettingsSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Seuls les ADMIN peuvent modifier les paramètres
        user = self.request.user
        profile = getattr(user, 'profile', None)
        
        if profile and profile.role in ['ADMIN', 'DIRECTEUR']:
            return GeofenceSettings.objects.all()
        else:
            # Les autres peuvent seulement lire
            return GeofenceSettings.objects.all()
    
    @action(detail=False, methods=['get'])
    def current_settings(self, request):
        """Récupérer les paramètres actuels (crée des paramètres par défaut si aucun n'existe)"""
        settings, created = GeofenceSettings.objects.get_or_create(
            pk=1,  # Un seul objet de configuration
            defaults={
                'heure_debut_matin': '07:30',
                'heure_fin_matin': '12:30',
                'heure_debut_apres_midi': '13:30',
                'heure_fin_apres_midi': '16:30',
                'distance_alerte_metres': 200,
                'frequence_verification_minutes': 5,
            }
        )
        serializer = self.get_serializer(settings)
        return Response(serializer.data)


class AgentLocationViewSet(viewsets.ModelViewSet):
    serializer_class = AgentLocationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        profile = getattr(user, 'profile', None)
        
        # ADMIN peut voir toutes les positions
        if profile and profile.role == 'ADMIN':
            return AgentLocation.objects.all()
        
        # DIRECTEUR peut voir les positions de sa direction
        elif profile and profile.role == 'DIRECTEUR':
            if profile.direction:
                agents_direction = User.objects.filter(
                    Q(profile__service__direction=profile.direction) |
                    Q(agent_profile__service__direction=profile.direction)
                )
                return AgentLocation.objects.filter(agent__in=agents_direction)
        
        # SUPERIEUR peut voir les positions de son service
        elif profile and profile.role == 'SUPERIEUR':
            if profile.service:
                agents_service = User.objects.filter(
                    Q(profile__service=profile.service) |
                    Q(agent_profile__service=profile.service)
                )
                return AgentLocation.objects.filter(agent__in=agents_service)
        
        # Par défaut, voir seulement ses propres positions
        return AgentLocation.objects.filter(agent=user)
    
    @action(detail=False, methods=['post'])
    def update_location(self, request):
        """Endpoint pour mettre à jour la position d'un agent depuis l'app mobile"""
        serializer = LocationUpdateSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            user = request.user
            
            # Récupérer le bureau assigné à l'agent
            bureau = None
            try:
                if hasattr(user, 'agent_profile'):
                    bureau = user.agent_profile.bureau
                elif hasattr(user, 'profile') and user.profile.service:
                    # Chercher un bureau par défaut pour le service/direction
                    bureau = Bureau.objects.first()  # À adapter selon votre logique
            except:
                pass
            
            # Créer l'enregistrement de position
            location = AgentLocation.objects.create(
                agent=user,
                latitude=data['latitude'],
                longitude=data['longitude'],
                accuracy=data.get('accuracy'),
                is_background=data.get('is_background', False),
                battery_level=data.get('battery_level'),
                timestamp=data.get('timestamp', timezone.now())
            )
            
            # Calculer la distance et vérifier les alertes si un bureau est assigné
            if bureau:
                distance = calculate_distance(
                    data['latitude'], data['longitude'],
                    bureau.latitude_centre, bureau.longitude_centre
                )
                location.distance_bureau = distance
                location.dans_zone_autorisee = distance <= bureau.rayon_metres
                location.save()
                
                # Vérifier si une alerte doit être déclenchée
                self._check_geofence_alert(user, bureau, location, distance)
            
            return Response({
                'message': 'Position mise à jour avec succès',
                'location_id': location.id,
                'distance_bureau': location.distance_bureau,
                'dans_zone_autorisee': location.dans_zone_autorisee
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def _check_geofence_alert(self, user, bureau, location, distance):
        """Vérifier si une alerte de géofencing doit être déclenchée"""
        settings = GeofenceSettings.objects.first()
        if not settings:
            return
        
        now = timezone.now()
        is_work_hours = settings.is_heure_travail(now)
        
        # Vérifier si l'agent est sorti de la zone pendant les heures de travail
        if distance > settings.distance_alerte_metres and is_work_hours:
            # Vérifier depuis quand l'agent est hors de la zone (durée configurable)
            duree_minimale = timedelta(minutes=settings.duree_minimale_hors_bureau_minutes)
            time_threshold = now - duree_minimale
            
            # Chercher la dernière position dans la zone autorisée
            last_inside_position = AgentLocation.objects.filter(
                agent=user,
                dans_zone_autorisee=True,
                timestamp__gte=time_threshold
            ).order_by('-timestamp').first()
            
            # Si aucune position dans la zone dans la période définie, vérifier plus loin
            if not last_inside_position:
                # Chercher la dernière position dans la zone (sans limite de temps)
                last_inside_position = AgentLocation.objects.filter(
                    agent=user,
                    dans_zone_autorisee=True
                ).order_by('-timestamp').first()
                
                # Si l'agent est hors zone depuis plus que la durée minimale, déclencher l'alerte
                if last_inside_position and (now - last_inside_position.timestamp) >= duree_minimale:
                    # Vérifier qu'il n'y a pas déjà une alerte active récente
                    recent_alert = GeofenceAlert.objects.filter(
                        agent=user,
                        bureau=bureau,
                        type_alerte='sortie_zone',
                        statut='active',
                        timestamp_alerte__gte=now - timedelta(hours=2)  # Éviter les doublons sur 2h
                    ).exists()
                    
                    if not recent_alert:
                        # Créer une nouvelle alerte
                        alert = GeofenceAlert.objects.create(
                            agent=user,
                            bureau=bureau,
                            type_alerte='sortie_zone',
                            latitude_agent=location.latitude,
                            longitude_agent=location.longitude,
                            distance_metres=int(distance),
                            en_heures_travail=True
                        )
                        
                        # Envoyer les notifications
                        self._send_geofence_notifications(alert)
    
    def _send_geofence_notifications(self, alert):
        """Envoyer les notifications pour une alerte de géofencing"""
        settings = GeofenceSettings.objects.first()
        if not settings:
            return
        
        # Récupérer les utilisateurs à notifier (directeurs et supérieurs)
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
        for user in users_to_notify:
            # Notification dans l'application
            send_geofence_notification(user, alert)
            
            # Notification push si activée
            if settings.notification_push_active:
                send_push_notification(user, alert)
        
        # Marquer les notifications comme envoyées
        alert.notification_envoyee = True
        alert.notification_push_envoyee = settings.notification_push_active
        alert.save()


class PushNotificationTokenViewSet(viewsets.ModelViewSet):
    serializer_class = PushNotificationTokenSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Les utilisateurs ne peuvent voir que leurs propres tokens
        return PushNotificationToken.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        # Désactiver les anciens tokens du même utilisateur et plateforme
        PushNotificationToken.objects.filter(
            user=self.request.user,
            platform=serializer.validated_data['platform']
        ).update(is_active=False)
        
        # Créer le nouveau token
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def register_token(self, request):
        """Enregistrer un nouveau token de notification push"""
        token = request.data.get('token')
        platform = request.data.get('platform')
        device_id = request.data.get('device_id')
        
        if not token or not platform:
            return Response(
                {'error': 'Token et platform sont requis'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Désactiver les anciens tokens
        PushNotificationToken.objects.filter(
            user=request.user,
            platform=platform
        ).update(is_active=False)
        
        # Créer ou mettre à jour le token
        push_token, created = PushNotificationToken.objects.get_or_create(
            user=request.user,
            token=token,
            defaults={
                'platform': platform,
                'device_id': device_id,
                'is_active': True
            }
        )
        
        if not created:
            push_token.platform = platform
            push_token.device_id = device_id
            push_token.is_active = True
            push_token.save()
        
        return Response({
            'message': 'Token enregistré avec succès',
            'token_id': push_token.id
        })
