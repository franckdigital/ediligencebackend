from rest_framework import serializers
from .models import CourrierStatut, CourrierRappel, CourrierNotification
from django.contrib.auth.models import User


class CourrierStatutSerializer(serializers.ModelSerializer):
    """Serializer pour le statut des courriers"""
    modifie_par_details = serializers.SerializerMethodField()
    courrier_reference = serializers.CharField(source='courrier.reference', read_only=True)
    
    class Meta:
        model = CourrierStatut
        fields = [
            'id', 'courrier', 'courrier_reference', 'statut', 
            'commentaire', 'modifie_par', 'modifie_par_details', 
            'date_modification'
        ]
        read_only_fields = ['date_modification']
    
    def get_modifie_par_details(self, obj):
        if obj.modifie_par:
            return {
                'id': obj.modifie_par.id,
                'username': obj.modifie_par.username,
                'first_name': obj.modifie_par.first_name,
                'last_name': obj.modifie_par.last_name
            }
        return None


class CourrierRappelSerializer(serializers.ModelSerializer):
    """Serializer pour les rappels de courriers"""
    courrier_reference = serializers.CharField(source='courrier.reference', read_only=True)
    utilisateur_details = serializers.SerializerMethodField()
    cree_par_details = serializers.SerializerMethodField()
    
    class Meta:
        model = CourrierRappel
        fields = [
            'id', 'courrier', 'courrier_reference', 'utilisateur', 
            'utilisateur_details', 'date_rappel', 'message', 
            'envoye', 'date_envoi', 'cree_par', 'cree_par_details', 
            'created_at'
        ]
        read_only_fields = ['envoye', 'date_envoi', 'created_at']
    
    def get_utilisateur_details(self, obj):
        return {
            'id': obj.utilisateur.id,
            'username': obj.utilisateur.username,
            'first_name': obj.utilisateur.first_name,
            'last_name': obj.utilisateur.last_name,
            'email': obj.utilisateur.email
        }
    
    def get_cree_par_details(self, obj):
        return {
            'id': obj.cree_par.id,
            'username': obj.cree_par.username,
            'first_name': obj.cree_par.first_name,
            'last_name': obj.cree_par.last_name
        }


class CourrierNotificationSerializer(serializers.ModelSerializer):
    """Serializer pour les notifications de courriers"""
    utilisateur_details = serializers.SerializerMethodField()
    courrier_details = serializers.SerializerMethodField()
    cree_par_details = serializers.SerializerMethodField()
    type_notification_display = serializers.CharField(source='get_type_notification_display', read_only=True)
    priorite_display = serializers.CharField(source='get_priorite_display', read_only=True)
    temps_ecoule = serializers.SerializerMethodField()
    
    class Meta:
        model = CourrierNotification
        fields = [
            'id', 'utilisateur', 'utilisateur_details', 'courrier', 
            'courrier_details', 'type_notification', 'type_notification_display',
            'titre', 'message', 'priorite', 'priorite_display', 'lue', 
            'date_lecture', 'cree_par', 'cree_par_details', 'created_at',
            'metadata', 'temps_ecoule'
        ]
        read_only_fields = ['created_at', 'date_lecture']
    
    def get_utilisateur_details(self, obj):
        return {
            'id': obj.utilisateur.id,
            'username': obj.utilisateur.username,
            'first_name': obj.utilisateur.first_name,
            'last_name': obj.utilisateur.last_name,
            'email': obj.utilisateur.email
        }
    
    def get_courrier_details(self, obj):
        if obj.courrier:
            return {
                'id': obj.courrier.id,
                'reference': obj.courrier.reference,
                'objet': obj.courrier.objet,
                'type_courrier': obj.courrier.type_courrier,
                'sens': obj.courrier.sens,
                'date_reception': obj.courrier.date_reception
            }
        return None
    
    def get_cree_par_details(self, obj):
        if obj.cree_par:
            return {
                'id': obj.cree_par.id,
                'username': obj.cree_par.username,
                'first_name': obj.cree_par.first_name,
                'last_name': obj.cree_par.last_name
            }
        return None
    
    def get_temps_ecoule(self, obj):
        """Calculer le temps écoulé depuis la création"""
        from django.utils import timezone
        delta = timezone.now() - obj.created_at
        
        if delta.days > 0:
            return f"il y a {delta.days} jour{'s' if delta.days > 1 else ''}"
        elif delta.seconds >= 3600:
            heures = delta.seconds // 3600
            return f"il y a {heures} heure{'s' if heures > 1 else ''}"
        elif delta.seconds >= 60:
            minutes = delta.seconds // 60
            return f"il y a {minutes} minute{'s' if minutes > 1 else ''}"
        else:
            return "à l'instant"
