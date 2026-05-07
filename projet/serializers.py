from rest_framework import serializers
from django.contrib.auth.models import User

from .models import (
    Projet, Tache, SousTache, CommentaireTache, PieceJointe,
    NotificationProjet, Livrable, ValidationTache, HistoriqueAction,
    ReunionProjet,
)


# =============================================================================
# DILIGENCE / COURRIER (minimal, from core app)
# =============================================================================

class DiligenceMinimalSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    titre = serializers.SerializerMethodField()
    objet = serializers.SerializerMethodField()
    statut = serializers.SerializerMethodField()

    def get_titre(self, obj):
        return getattr(obj, 'titre', '') or getattr(obj, 'objet', '') or ''

    def get_objet(self, obj):
        return getattr(obj, 'objet', '') or ''

    def get_statut(self, obj):
        return getattr(obj, 'statut', '') or ''


class CourrierMinimalSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    objet = serializers.SerializerMethodField()
    reference = serializers.SerializerMethodField()

    def get_objet(self, obj):
        return getattr(obj, 'objet', '') or ''

    def get_reference(self, obj):
        return getattr(obj, 'reference', '') or ''


# =============================================================================
# UTILISATEUR (lecture seule, imbriqué)
# =============================================================================

class UserMinimalSerializer(serializers.ModelSerializer):
    nom_complet = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'nom_complet', 'role']
        read_only_fields = fields

    def get_nom_complet(self, obj):
        full = f"{obj.first_name} {obj.last_name}".strip()
        return full or obj.username

    def get_role(self, obj):
        profile = getattr(obj, 'profile', None)
        return profile.role if profile else None


# =============================================================================
# SOUS-TÂCHES
# =============================================================================

class SousTacheSerializer(serializers.ModelSerializer):
    responsable_detail = UserMinimalSerializer(source='responsable', read_only=True)
    est_en_retard = serializers.BooleanField(read_only=True)

    class Meta:
        model = SousTache
        fields = [
            'id', 'titre', 'tache', 'responsable', 'responsable_detail',
            'date_echeance', 'statut', 'est_en_retard',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


# =============================================================================
# COMMENTAIRES
# =============================================================================

class CommentaireTacheSerializer(serializers.ModelSerializer):
    auteur_detail = UserMinimalSerializer(source='auteur', read_only=True)

    class Meta:
        model = CommentaireTache
        fields = [
            'id', 'tache', 'auteur', 'auteur_detail', 'contenu',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['auteur', 'created_at', 'updated_at']


# =============================================================================
# PIÈCES JOINTES
# =============================================================================

class PieceJointeSerializer(serializers.ModelSerializer):
    uploaded_by_detail = UserMinimalSerializer(source='uploaded_by', read_only=True)

    class Meta:
        model = PieceJointe
        fields = [
            'id', 'tache', 'projet', 'fichier', 'nom', 'type_fichier',
            'taille', 'uploaded_by', 'uploaded_by_detail', 'created_at',
        ]
        read_only_fields = ['uploaded_by', 'created_at']


# =============================================================================
# TÂCHES
# =============================================================================

class TacheListSerializer(serializers.ModelSerializer):
    """Serializer léger pour les listes."""
    responsable_detail = UserMinimalSerializer(source='responsable', read_only=True)
    est_en_retard = serializers.BooleanField(read_only=True)
    nombre_sous_taches = serializers.IntegerField(read_only=True)
    sous_taches_terminees = serializers.IntegerField(read_only=True)
    nombre_commentaires = serializers.SerializerMethodField()
    nombre_pieces_jointes = serializers.SerializerMethodField()

    class Meta:
        model = Tache
        fields = [
            'id', 'titre', 'projet', 'responsable', 'responsable_detail',
            'agents_assignes',
            'date_debut', 'date_fin_prevue', 'priorite', 'statut',
            'pourcentage_avancement', 'poids', 'ordre',
            'est_en_retard', 'nombre_sous_taches', 'sous_taches_terminees',
            'nombre_commentaires', 'nombre_pieces_jointes',
            'tache_dependante', 'created_at',
        ]

    def get_nombre_commentaires(self, obj):
        return obj.commentaires.count()

    def get_nombre_pieces_jointes(self, obj):
        return obj.pieces_jointes.count()


class TacheDetailSerializer(serializers.ModelSerializer):
    """Serializer complet avec sous-tâches, commentaires, pièces jointes."""
    responsable_detail = UserMinimalSerializer(source='responsable', read_only=True)
    agents_assignes_detail = UserMinimalSerializer(source='agents_assignes', many=True, read_only=True)
    created_by_detail = UserMinimalSerializer(source='created_by', read_only=True)
    sous_taches = SousTacheSerializer(many=True, read_only=True)
    commentaires = CommentaireTacheSerializer(many=True, read_only=True)
    pieces_jointes = PieceJointeSerializer(many=True, read_only=True)
    diligence_detail = DiligenceMinimalSerializer(source='diligence', read_only=True)
    courrier_detail = CourrierMinimalSerializer(source='courrier', read_only=True)
    est_en_retard = serializers.BooleanField(read_only=True)
    nombre_sous_taches = serializers.IntegerField(read_only=True)
    sous_taches_terminees = serializers.IntegerField(read_only=True)
    nombre_commentaires = serializers.SerializerMethodField()

    class Meta:
        model = Tache
        fields = [
            'id', 'titre', 'description', 'projet',
            'responsable', 'responsable_detail',
            'agents_assignes', 'agents_assignes_detail',
            'date_debut', 'date_fin_prevue', 'date_fin_effective',
            'priorite', 'statut', 'pourcentage_avancement', 'poids', 'ordre',
            'tache_dependante', 'diligence', 'courrier',
            'diligence_detail', 'courrier_detail',
            'est_en_retard', 'nombre_sous_taches', 'sous_taches_terminees',
            'nombre_commentaires',
            'sous_taches', 'commentaires', 'pieces_jointes',
            'created_by', 'created_by_detail', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']

    def get_nombre_commentaires(self, obj):
        return obj.commentaires.count()


class TacheCreateSerializer(serializers.ModelSerializer):
    """Serializer pour création / mise à jour."""

    class Meta:
        model = Tache
        fields = [
            'id', 'titre', 'description', 'projet',
            'responsable', 'agents_assignes',
            'date_debut', 'date_fin_prevue', 'date_fin_effective',
            'priorite', 'statut', 'pourcentage_avancement', 'poids', 'ordre',
            'tache_dependante', 'diligence', 'courrier',
        ]


# =============================================================================
# GANTT (vue spéciale)
# =============================================================================

class TacheGanttSerializer(serializers.ModelSerializer):
    """Serializer pour la vue Gantt."""
    responsable_nom = serializers.SerializerMethodField()
    est_en_retard = serializers.BooleanField(read_only=True)

    class Meta:
        model = Tache
        fields = [
            'id', 'titre', 'date_debut', 'date_fin_prevue', 'date_fin_effective',
            'statut', 'priorite', 'pourcentage_avancement',
            'tache_dependante', 'responsable', 'responsable_nom',
            'est_en_retard', 'ordre',
        ]

    def get_responsable_nom(self, obj):
        if obj.responsable:
            full = f"{obj.responsable.first_name} {obj.responsable.last_name}".strip()
            return full or obj.responsable.username
        return None


# =============================================================================
# PROJETS
# =============================================================================

class ProjetListSerializer(serializers.ModelSerializer):
    """Serializer léger pour les listes de projets."""
    responsable_detail = UserMinimalSerializer(source='responsable', read_only=True)
    service_nom = serializers.SerializerMethodField()
    est_en_retard = serializers.BooleanField(read_only=True)
    nombre_taches = serializers.IntegerField(read_only=True)
    taches_terminees = serializers.IntegerField(read_only=True)
    taches_en_cours = serializers.IntegerField(read_only=True)
    taches_a_faire = serializers.IntegerField(read_only=True)

    class Meta:
        model = Projet
        fields = [
            'id', 'titre', 'date_debut', 'date_fin_prevue',
            'statut', 'pourcentage_avancement',
            'responsable', 'responsable_detail',
            'service', 'service_nom',
            'est_en_retard', 'nombre_taches',
            'taches_terminees', 'taches_en_cours', 'taches_a_faire',
            'budget_prevu', 'budget_consomme',
            'created_at',
        ]

    def get_service_nom(self, obj):
        if obj.service:
            return obj.service.nom
        # Fallback : service du responsable
        profile = getattr(getattr(obj, 'responsable', None), 'profile', None)
        if profile and profile.service:
            return profile.service.nom
        return None


class ProjetDetailSerializer(serializers.ModelSerializer):
    """Serializer complet pour le détail d'un projet."""
    responsable_detail = UserMinimalSerializer(source='responsable', read_only=True)
    equipe_detail = UserMinimalSerializer(source='equipe', many=True, read_only=True)
    created_by_detail = UserMinimalSerializer(source='created_by', read_only=True)
    taches = TacheDetailSerializer(many=True, read_only=True)
    livrables = serializers.SerializerMethodField()
    est_en_retard = serializers.BooleanField(read_only=True)
    nombre_taches = serializers.IntegerField(read_only=True)
    taches_terminees = serializers.IntegerField(read_only=True)
    taches_en_cours = serializers.IntegerField(read_only=True)
    taches_a_faire = serializers.IntegerField(read_only=True)

    class Meta:
        model = Projet
        fields = [
            'id', 'titre', 'description', 'objectifs',
            'date_debut', 'date_fin_prevue', 'date_fin_effective',
            'budget_prevu', 'budget_consomme',
            'statut', 'pourcentage_avancement',
            'responsable', 'responsable_detail',
            'equipe', 'equipe_detail',
            'direction', 'service',
            'diligence', 'courrier',
            'est_en_retard', 'nombre_taches',
            'taches_terminees', 'taches_en_cours', 'taches_a_faire',
            'taches', 'livrables',
            'created_by', 'created_by_detail', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at', 'pourcentage_avancement']

    def get_livrables(self, obj):
        return LivrableSerializer(obj.livrables.all(), many=True).data


class ProjetCreateSerializer(serializers.ModelSerializer):
    """Serializer pour création / mise à jour de projet."""

    class Meta:
        model = Projet
        fields = [
            'id', 'titre', 'description', 'objectifs',
            'date_debut', 'date_fin_prevue', 'date_fin_effective',
            'budget_prevu', 'budget_consomme',
            'statut', 'responsable', 'equipe',
            'direction', 'service', 'diligence', 'courrier',
        ]


# =============================================================================
# LIVRABLES
# =============================================================================

class LivrableSerializer(serializers.ModelSerializer):
    soumis_par_detail = UserMinimalSerializer(source='soumis_par', read_only=True)
    valide_par_detail = UserMinimalSerializer(source='valide_par', read_only=True)

    class Meta:
        model = Livrable
        fields = [
            'id', 'projet', 'tache', 'titre', 'description',
            'fichier', 'version', 'statut',
            'soumis_par', 'soumis_par_detail',
            'valide_par', 'valide_par_detail',
            'commentaire_validation', 'date_validation',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['soumis_par', 'created_at', 'updated_at']


# =============================================================================
# VALIDATION WORKFLOW
# =============================================================================

class ValidationTacheSerializer(serializers.ModelSerializer):
    soumis_par_detail = UserMinimalSerializer(source='soumis_par', read_only=True)
    valide_par_detail = UserMinimalSerializer(source='valide_par', read_only=True)

    class Meta:
        model = ValidationTache
        fields = [
            'id', 'tache', 'soumis_par', 'soumis_par_detail',
            'valide_par', 'valide_par_detail',
            'statut', 'commentaire',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['soumis_par', 'created_at', 'updated_at']


# =============================================================================
# NOTIFICATIONS
# =============================================================================

class NotificationProjetSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationProjet
        fields = [
            'id', 'user', 'projet', 'tache',
            'type_notification', 'titre', 'message',
            'lue', 'date_lecture', 'metadata', 'created_at',
        ]
        read_only_fields = ['user', 'created_at']


# =============================================================================
# HISTORIQUE
# =============================================================================

class HistoriqueActionSerializer(serializers.ModelSerializer):
    utilisateur_detail = UserMinimalSerializer(source='utilisateur', read_only=True)

    class Meta:
        model = HistoriqueAction
        fields = [
            'id', 'projet', 'tache', 'utilisateur', 'utilisateur_detail',
            'action', 'details', 'created_at',
        ]
        read_only_fields = fields


# =============================================================================
# RÉUNIONS & RENDEZ-VOUS
# =============================================================================

class ReunionProjetSerializer(serializers.ModelSerializer):
    organisateur_detail = UserMinimalSerializer(source='organisateur', read_only=True)
    participants_detail = UserMinimalSerializer(source='participants', many=True, read_only=True)

    class Meta:
        model = ReunionProjet
        fields = [
            'id', 'titre', 'type_reunion', 'description', 'lieu', 'lien_visio',
            'date', 'heure_debut', 'heure_fin',
            'projet', 'tache',
            'organisateur', 'organisateur_detail',
            'participants', 'participants_detail',
            'statut', 'compte_rendu',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['organisateur', 'created_at', 'updated_at']
