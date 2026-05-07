from django.contrib import admin
from .models import (
    Projet, Tache, SousTache, CommentaireTache, PieceJointe,
    NotificationProjet, Livrable, ValidationTache, HistoriqueAction,
)


class TacheInline(admin.TabularInline):
    model = Tache
    extra = 0
    fields = ['titre', 'responsable', 'statut', 'priorite', 'date_debut', 'date_fin_prevue']
    show_change_link = True


class SousTacheInline(admin.TabularInline):
    model = SousTache
    extra = 0
    fields = ['titre', 'responsable', 'statut', 'date_echeance']


class LivrableInline(admin.TabularInline):
    model = Livrable
    extra = 0
    fields = ['titre', 'version', 'statut', 'soumis_par', 'valide_par']
    show_change_link = True


@admin.register(Projet)
class ProjetAdmin(admin.ModelAdmin):
    list_display = ['titre', 'statut', 'pourcentage_avancement', 'responsable', 'date_debut', 'date_fin_prevue', 'created_at']
    list_filter = ['statut', 'direction', 'created_at']
    search_fields = ['titre', 'description']
    filter_horizontal = ['equipe']
    inlines = [TacheInline, LivrableInline]
    readonly_fields = ['pourcentage_avancement', 'created_at', 'updated_at']


@admin.register(Tache)
class TacheAdmin(admin.ModelAdmin):
    list_display = ['titre', 'projet', 'responsable', 'statut', 'priorite', 'date_fin_prevue', 'pourcentage_avancement']
    list_filter = ['statut', 'priorite', 'projet']
    search_fields = ['titre', 'description']
    filter_horizontal = ['agents_assignes']
    inlines = [SousTacheInline]
    readonly_fields = ['created_at', 'updated_at']


@admin.register(SousTache)
class SousTacheAdmin(admin.ModelAdmin):
    list_display = ['titre', 'tache', 'responsable', 'statut', 'date_echeance']
    list_filter = ['statut']
    search_fields = ['titre']


@admin.register(CommentaireTache)
class CommentaireTacheAdmin(admin.ModelAdmin):
    list_display = ['auteur', 'tache', 'contenu_court', 'created_at']
    list_filter = ['created_at']
    search_fields = ['contenu']

    def contenu_court(self, obj):
        return obj.contenu[:80] + '...' if len(obj.contenu) > 80 else obj.contenu
    contenu_court.short_description = 'Contenu'


@admin.register(PieceJointe)
class PieceJointeAdmin(admin.ModelAdmin):
    list_display = ['nom', 'tache', 'projet', 'uploaded_by', 'type_fichier', 'taille', 'created_at']
    list_filter = ['type_fichier', 'created_at']
    search_fields = ['nom']


@admin.register(NotificationProjet)
class NotificationProjetAdmin(admin.ModelAdmin):
    list_display = ['titre', 'user', 'type_notification', 'lue', 'created_at']
    list_filter = ['type_notification', 'lue', 'created_at']
    search_fields = ['titre', 'message']


@admin.register(Livrable)
class LivrableAdmin(admin.ModelAdmin):
    list_display = ['titre', 'projet', 'version', 'statut', 'soumis_par', 'valide_par', 'created_at']
    list_filter = ['statut', 'created_at']
    search_fields = ['titre']


@admin.register(ValidationTache)
class ValidationTacheAdmin(admin.ModelAdmin):
    list_display = ['tache', 'soumis_par', 'valide_par', 'statut', 'created_at']
    list_filter = ['statut', 'created_at']


@admin.register(HistoriqueAction)
class HistoriqueActionAdmin(admin.ModelAdmin):
    list_display = ['action', 'utilisateur', 'projet', 'tache', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['details']
    readonly_fields = ['created_at']
