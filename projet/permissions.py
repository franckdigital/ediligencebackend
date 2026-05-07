from rest_framework.permissions import BasePermission

# ─────────────────────────────────────────────────────────────────
# Matrice des droits — Gestion de Projets
#
# ADMIN              : tout voir / tout modifier / supprimer
# DIRECTEUR
# SOUS_DIRECTEUR
# CHEF_SERVICE
# SUPERIEUR          : créer projets, créer/assigner tâches, valider
# SECRETAIRE         : droits AGENT + suivi (voir toutes tâches du projet)
# AGENT              : exécuter ses tâches (statut, commentaires, fichiers)
# ─────────────────────────────────────────────────────────────────

ROLES_MANAGER = frozenset(['ADMIN', 'DIRECTEUR', 'SOUS_DIRECTEUR', 'CHEF_SERVICE', 'SUPERIEUR'])
ROLES_EXECUTANT = frozenset(['AGENT', 'SECRETAIRE'])


def _get_role(user):
    profile = getattr(user, 'profile', None)
    return getattr(profile, 'role', None)


def _is_manager(user):
    return _get_role(user) in ROLES_MANAGER


def _is_executant(user):
    return _get_role(user) in ROLES_EXECUTANT


class ProjetPermission(BasePermission):
    """
    Permissions basées sur les rôles pour les projets.

    Droits :
    - ADMIN              : CRUD complet
    - DIRECTEUR/SOUS_DIRECTEUR/CHEF_SERVICE/SUPERIEUR : créer, modifier, lire
    - SECRETAIRE         : lire + modifier (suivi/mise à jour)
    - AGENT              : lecture seule (projets auxquels il est rattaché)
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        role = _get_role(request.user)
        if not role:
            return False

        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True

        # Création d'un projet : managers uniquement
        if request.method == 'POST':
            return role in ROLES_MANAGER

        # Mise à jour : managers + secrétaire (suivi)
        if request.method in ('PUT', 'PATCH'):
            return role in ROLES_MANAGER or role == 'SECRETAIRE'

        # Suppression : admin et directeurs uniquement
        if request.method == 'DELETE':
            return role in ('ADMIN', 'DIRECTEUR')

        return False

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        role = _get_role(request.user)

        # Admin voit et modifie tout
        if role == 'ADMIN':
            return True

        # Lecture autorisée pour tous les rôles authentifiés
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True

        # Suppression : admin + directeur
        if request.method == 'DELETE':
            return role in ('ADMIN', 'DIRECTEUR')

        # Modification : responsable du projet, membre de l'équipe, ou manager
        if obj.responsable == request.user:
            return True
        if obj.equipe.filter(id=request.user.id).exists():
            # Secrétaire peut mettre à jour un projet dont il est membre
            if role == 'SECRETAIRE':
                return True
            # Agent ne peut pas modifier un projet, même membre
            if role == 'AGENT':
                return False

        return role in ROLES_MANAGER


class TachePermission(BasePermission):
    """
    Permissions spécifiques aux tâches.

    Droits :
    - ADMIN              : CRUD complet
    - DIRECTEUR/SOUS_DIRECTEUR/CHEF_SERVICE/SUPERIEUR : CRUD complet
    - SECRETAIRE         : lire + PUT/PATCH ses propres tâches + suivi
    - AGENT              : lire + PUT/PATCH ses propres tâches uniquement
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        role = _get_role(request.user)
        if not role:
            return False

        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True

        # Mise à jour autorisée pour tous (limitée par has_object_permission)
        if request.method in ('PUT', 'PATCH'):
            return True

        # Création de tâche : managers uniquement
        # Les actions POST custom (changer-statut, soumettre, etc.) sont accessibles à tous
        if request.method == 'POST':
            action = getattr(view, 'action', None)
            if action == 'create':
                return role in ROLES_MANAGER
            return True  # actions custom gérées par has_object_permission + la vue elle-même

        # Suppression : managers uniquement
        if request.method == 'DELETE':
            return role in ROLES_MANAGER

        return False

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        role = _get_role(request.user)

        # Admin : tout
        if role == 'ADMIN':
            return True

        # Lecture : tous
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True

        # Suppression : managers uniquement
        if request.method == 'DELETE':
            return role in ROLES_MANAGER

        # Modification (PUT/PATCH) :
        user = request.user

        # Managers : accès complet si membre du projet
        if role in ROLES_MANAGER:
            if obj.projet.responsable == user:
                return True
            if obj.projet.equipe.filter(id=user.id).exists():
                return True
            # Les managers voient quand même leurs propres tâches
            if obj.responsable == user or obj.agents_assignes.filter(id=user.id).exists():
                return True
            return role in ('DIRECTEUR', 'SUPERIEUR')

        # Agent : uniquement ses tâches assignées
        if role == 'AGENT':
            return (
                obj.responsable == user
                or obj.agents_assignes.filter(id=user.id).exists()
            )

        # Secrétaire : ses tâches assignées + tâches du projet (suivi)
        if role == 'SECRETAIRE':
            if obj.responsable == user or obj.agents_assignes.filter(id=user.id).exists():
                return True
            # Suivi : peut mettre à jour les tâches des projets dont il est membre
            if obj.projet.equipe.filter(id=user.id).exists():
                return True
            return False

        return False


class CommentairePieceJointePermission(BasePermission):
    """
    Commentaires et pièces jointes :
    - Tous les rôles peuvent créer/lire des commentaires et uploader des fichiers
      sur les tâches auxquelles ils ont accès (vérification côté queryset).
    - Modification/suppression : auteur uniquement ou manager.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        role = _get_role(request.user)

        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True

        # L'auteur peut modifier/supprimer
        auteur_field = getattr(obj, 'auteur', None) or getattr(obj, 'uploaded_by', None)
        if auteur_field == request.user:
            return True

        # Managers peuvent modérer
        return role in ROLES_MANAGER


class ValidationPermission(BasePermission):
    """
    Validation des tâches : réservé aux managers.
    Les agents/secrétaires peuvent soumettre une tâche mais pas la valider.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        # Lecture : tout le monde
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        # Écriture (soumettre) : tout le monde
        if request.method == 'POST':
            return True
        return False

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        role = _get_role(request.user)
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        return role in ROLES_MANAGER


class IsAuthenticated(BasePermission):
    """Simple vérification d'authentification."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)
