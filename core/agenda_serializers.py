"""
Serializers pour le module Agenda (Rendez-vous et Réunions)
"""
from rest_framework import serializers
from core.models import RendezVous, RendezVousDocument, Reunion, ReunionPresence


# --- SERIALIZERS AGENDA : RENDEZ-VOUS ---
class RendezVousDocumentSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = RendezVousDocument
        fields = ['id', 'rendezvous', 'fichier', 'nom', 'uploaded_at', 'uploaded_by', 'uploaded_by_name']
        read_only_fields = ['uploaded_at', 'uploaded_by']
    
    def get_uploaded_by_name(self, obj):
        if obj.uploaded_by:
            return f"{obj.uploaded_by.first_name} {obj.uploaded_by.last_name}".strip() or obj.uploaded_by.username
        return None


class RendezVousSerializer(serializers.ModelSerializer):
    organisateur_name = serializers.SerializerMethodField()
    participant_name = serializers.SerializerMethodField()
    organisateur_email = serializers.SerializerMethodField()
    participant_email = serializers.SerializerMethodField()
    documents = RendezVousDocumentSerializer(many=True, read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    mode_display = serializers.CharField(source='get_mode_display', read_only=True)
    
    class Meta:
        model = RendezVous
        fields = [
            'id', 'titre', 'description', 'date_debut', 'date_fin', 'lieu',
            'organisateur', 'organisateur_name', 'organisateur_email',
            'participant', 'participant_name', 'participant_email',
            'statut', 'statut_display', 'mode', 'mode_display',
            'lien_visio', 'commentaires', 'documents',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_organisateur_name(self, obj):
        return f"{obj.organisateur.first_name} {obj.organisateur.last_name}".strip() or obj.organisateur.username
    
    def get_participant_name(self, obj):
        return f"{obj.participant.first_name} {obj.participant.last_name}".strip() or obj.participant.username
    
    def get_organisateur_email(self, obj):
        return obj.organisateur.email
    
    def get_participant_email(self, obj):
        return obj.participant.email


# --- SERIALIZERS AGENDA : RÉUNIONS ---
class ReunionPresenceSerializer(serializers.ModelSerializer):
    participant_name = serializers.SerializerMethodField()
    participant_email = serializers.SerializerMethodField()
    
    class Meta:
        model = ReunionPresence
        fields = ['id', 'reunion', 'participant', 'participant_name', 'participant_email', 
                  'present', 'heure_arrivee', 'commentaire']
    
    def get_participant_name(self, obj):
        return f"{obj.participant.first_name} {obj.participant.last_name}".strip() or obj.participant.username
    
    def get_participant_email(self, obj):
        return obj.participant.email


class ReunionSerializer(serializers.ModelSerializer):
    organisateur_name = serializers.SerializerMethodField()
    organisateur_email = serializers.SerializerMethodField()
    participants_details = serializers.SerializerMethodField()
    presences = ReunionPresenceSerializer(many=True, read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    type_reunion_display = serializers.CharField(source='get_type_reunion_display', read_only=True)
    nb_participants = serializers.SerializerMethodField()
    nb_presents = serializers.SerializerMethodField()
    
    class Meta:
        model = Reunion
        fields = [
            'id', 'intitule', 'description', 'type_reunion', 'type_reunion_display',
            'date_debut', 'date_fin', 'lieu', 'lien_zoom',
            'organisateur', 'organisateur_name', 'organisateur_email',
            'participants', 'participants_details', 'nb_participants', 'nb_presents',
            'statut', 'statut_display', 'compte_rendu', 'pv_fichier',
            'presences', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_organisateur_name(self, obj):
        return f"{obj.organisateur.first_name} {obj.organisateur.last_name}".strip() or obj.organisateur.username
    
    def get_organisateur_email(self, obj):
        return obj.organisateur.email
    
    def get_participants_details(self, obj):
        return [
            {
                'id': p.id,
                'username': p.username,
                'name': f"{p.first_name} {p.last_name}".strip() or p.username,
                'email': p.email
            }
            for p in obj.participants.all()
        ]
    
    def get_nb_participants(self, obj):
        return obj.participants.count()
    
    def get_nb_presents(self, obj):
        return obj.presences.filter(present=True).count()
