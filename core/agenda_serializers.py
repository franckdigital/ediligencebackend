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
    organisateur_email = serializers.SerializerMethodField()
    responsable_name = serializers.SerializerMethodField()
    responsable_email = serializers.SerializerMethodField()
    documents = RendezVousDocumentSerializer(many=True, read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    visiteur_type_display = serializers.CharField(source='get_visiteur_type_display', read_only=True)
    
    class Meta:
        model = RendezVous
        fields = [
            'id', 'objet', 'date_debut', 'date_fin', 'lieu',
            'organisateur', 'organisateur_name', 'organisateur_email',
            'responsable', 'responsable_name', 'responsable_email',
            'visiteur_nom', 'visiteur_prenoms', 'visiteur_fonction', 
            'visiteur_telephone', 'visiteur_type', 'visiteur_type_display', 
            'visiteur_structure',
            'statut', 'statut_display', 'documents',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'organisateur']
        extra_kwargs = {
            'organisateur': {'required': False, 'allow_null': True}
        }
    
    def get_organisateur_name(self, obj):
        return f"{obj.organisateur.first_name} {obj.organisateur.last_name}".strip() or obj.organisateur.username
    
    def get_organisateur_email(self, obj):
        return obj.organisateur.email

    def get_responsable_name(self, obj):
        if obj.responsable:
            return f"{obj.responsable.first_name} {obj.responsable.last_name}".strip() or obj.responsable.username
        return None

    def get_responsable_email(self, obj):
        return obj.responsable.email if obj.responsable else None


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
        read_only_fields = ['created_at', 'updated_at', 'organisateur']
        extra_kwargs = {
            'organisateur': {'required': False, 'allow_null': True}
        }
    
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
