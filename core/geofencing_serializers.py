from rest_framework import serializers
from django.contrib.auth.models import User
from .models import GeofenceAlert, GeofenceSettings, AgentLocation, PushNotificationToken


class GeofenceAlertSerializer(serializers.ModelSerializer):
    agent_name = serializers.SerializerMethodField()
    bureau_name = serializers.SerializerMethodField()
    type_alerte_display = serializers.CharField(source='get_type_alerte_display', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    resolu_par_name = serializers.SerializerMethodField()
    
    class Meta:
        model = GeofenceAlert
        fields = [
            'id', 'agent', 'agent_name', 'bureau', 'bureau_name',
            'type_alerte', 'type_alerte_display', 'latitude_agent', 'longitude_agent',
            'distance_metres', 'timestamp_alerte', 'heure_detection', 'date_detection',
            'en_heures_travail', 'message_alerte', 'statut', 'statut_display',
            'resolu_par', 'resolu_par_name', 'date_resolution', 'commentaire_resolution',
            'notification_envoyee', 'notification_push_envoyee'
        ]
        read_only_fields = [
            'timestamp_alerte', 'heure_detection', 'date_detection', 
            'message_alerte', 'notification_envoyee', 'notification_push_envoyee'
        ]
    
    def get_agent_name(self, obj):
        return f"{obj.agent.first_name} {obj.agent.last_name}".strip() or obj.agent.username
    
    def get_bureau_name(self, obj):
        return obj.bureau.nom if obj.bureau else None
    
    def get_resolu_par_name(self, obj):
        if obj.resolu_par:
            return f"{obj.resolu_par.first_name} {obj.resolu_par.last_name}".strip() or obj.resolu_par.username
        return None


class GeofenceSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeofenceSettings
        fields = [
            'id', 'heure_debut_matin', 'heure_fin_matin', 
            'heure_debut_apres_midi', 'heure_fin_apres_midi',
            'distance_alerte_metres', 'duree_minimale_hors_bureau_minutes', 'frequence_verification_minutes',
            'lundi_travaille', 'mardi_travaille', 'mercredi_travaille',
            'jeudi_travaille', 'vendredi_travaille', 'samedi_travaille', 'dimanche_travaille',
            'notification_directeurs', 'notification_superieurs', 'notification_push_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class AgentLocationSerializer(serializers.ModelSerializer):
    agent_name = serializers.SerializerMethodField()
    
    class Meta:
        model = AgentLocation
        fields = [
            'id', 'agent', 'agent_name', 'latitude', 'longitude', 'accuracy',
            'timestamp', 'is_background', 'battery_level', 'distance_bureau',
            'dans_zone_autorisee'
        ]
        read_only_fields = ['timestamp', 'distance_bureau', 'dans_zone_autorisee']
    
    def get_agent_name(self, obj):
        return f"{obj.agent.first_name} {obj.agent.last_name}".strip() or obj.agent.username


class PushNotificationTokenSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    platform_display = serializers.CharField(source='get_platform_display', read_only=True)
    
    class Meta:
        model = PushNotificationToken
        fields = [
            'id', 'user', 'user_name', 'token', 'platform', 'platform_display',
            'device_id', 'is_active', 'created_at', 'last_used'
        ]
        read_only_fields = ['created_at', 'last_used']
    
    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username


class LocationUpdateSerializer(serializers.Serializer):
    """Serializer pour les mises à jour de position depuis l'application mobile"""
    latitude = serializers.DecimalField(max_digits=22, decimal_places=17)
    longitude = serializers.DecimalField(max_digits=22, decimal_places=17)
    accuracy = serializers.FloatField(required=False, allow_null=True)
    is_background = serializers.BooleanField(default=False)
    battery_level = serializers.IntegerField(required=False, allow_null=True)
    timestamp = serializers.DateTimeField(required=False)
