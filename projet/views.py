from datetime import timedelta

from django.contrib.auth.models import User
from django.db.models import Q, Count, Avg, F
from django.utils import timezone
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import (
    Projet, Tache, SousTache, CommentaireTache, PieceJointe,
    NotificationProjet, Livrable, ValidationTache, HistoriqueAction,
    ReunionProjet,
)
from .serializers import (
    ProjetListSerializer, ProjetDetailSerializer, ProjetCreateSerializer,
    TacheListSerializer, TacheDetailSerializer, TacheCreateSerializer,
    TacheGanttSerializer,
    SousTacheSerializer, CommentaireTacheSerializer, PieceJointeSerializer,
    NotificationProjetSerializer, LivrableSerializer,
    ValidationTacheSerializer, HistoriqueActionSerializer,
    ReunionProjetSerializer,
)
from .permissions import (
    ProjetPermission, TachePermission,
    CommentairePieceJointePermission, ValidationPermission,
    ROLES_MANAGER,
)


# =============================================================================
# HELPERS
# =============================================================================

def _get_role(user):
    profile = getattr(user, 'profile', None)
    return getattr(profile, 'role', None)


def _log_action(user, action, projet=None, tache=None, details=None):
    """Crée une entrée dans l'historique des actions."""
    HistoriqueAction.objects.create(
        utilisateur=user,
        projet=projet,
        tache=tache,
        action=action,
        details=details or {},
    )


def _notifier(users, type_notification, titre, message, projet=None, tache=None, metadata=None):
    """Crée des notifications pour une liste d'utilisateurs."""
    notifs = []
    for user in users:
        notifs.append(NotificationProjet(
            user=user,
            projet=projet,
            tache=tache,
            type_notification=type_notification,
            titre=titre,
            message=message,
            metadata=metadata or {},
        ))
    NotificationProjet.objects.bulk_create(notifs)


def _destinataires_tache_terminee(tache, executeur):
    """
    Retourne la liste des utilisateurs à notifier quand une tâche est terminée.
    Notifie : responsable de la tâche + responsable du projet + managers de l'équipe.
    Exclut l'exécuteur lui-même.
    """
    destinataires = set()
    # Responsable direct de la tâche
    if tache.responsable and tache.responsable != executeur:
        destinataires.add(tache.responsable)
    # Responsable du projet
    if tache.projet.responsable and tache.projet.responsable != executeur:
        destinataires.add(tache.projet.responsable)
    # Managers membres de l'équipe projet
    for membre in tache.projet.equipe.all():
        if membre != executeur:
            role_m = _get_role(membre)
            if role_m in ROLES_MANAGER:
                destinataires.add(membre)
    return list(destinataires)


# =============================================================================
# A. PROJETS VIEWSET
# =============================================================================

class ProjetViewSet(viewsets.ModelViewSet):
    """
    CRUD complet pour les projets + actions personnalisées :
    - dashboard/ : tableau de bord du projet
    - equipe/ : gestion de l'équipe
    - gantt/ : données Gantt
    - recalculer/ : recalculer l'avancement
    """
    permission_classes = [IsAuthenticated, ProjetPermission]

    def get_queryset(self):
        user = self.request.user
        role = _get_role(user)
        qs = Projet.objects.select_related(
            'responsable', 'responsable__profile', 'responsable__profile__service',
            'direction', 'service', 'created_by',
        )

        # Filtres par rôle
        if role == 'ADMIN':
            pass  # Tout voir
        elif role in ('DIRECTEUR', 'SOUS_DIRECTEUR'):
            profile = getattr(user, 'profile', None)
            if profile and profile.service:
                direction = profile.service.get_direction
                if direction:
                    qs = qs.filter(
                        Q(direction=direction) | Q(responsable=user) | Q(equipe=user)
                    ).distinct()
                else:
                    qs = qs.filter(Q(responsable=user) | Q(equipe=user)).distinct()
            else:
                qs = qs.filter(Q(responsable=user) | Q(equipe=user)).distinct()
        elif role == 'PRESTATAIRE':
            qs = qs.filter(equipe=user).distinct()
        else:
            qs = qs.filter(
                Q(responsable=user) | Q(equipe=user) | Q(created_by=user)
            ).distinct()

        # Filtres query params
        statut = self.request.query_params.get('statut')
        if statut:
            qs = qs.filter(statut=statut)

        responsable_id = self.request.query_params.get('responsable')
        if responsable_id:
            qs = qs.filter(responsable_id=responsable_id)

        direction_id = self.request.query_params.get('direction')
        if direction_id:
            qs = qs.filter(direction_id=direction_id)

        service_id = self.request.query_params.get('service')
        if service_id:
            qs = qs.filter(service_id=service_id)

        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(Q(titre__icontains=search) | Q(description__icontains=search))

        return qs

    def get_serializer_class(self):
        if self.action == 'list':
            return ProjetListSerializer
        if self.action in ('create', 'update', 'partial_update'):
            return ProjetCreateSerializer
        return ProjetDetailSerializer

    def perform_create(self, serializer):
        projet = serializer.save(created_by=self.request.user)
        _log_action(self.request.user, 'creation', projet=projet, details={
            'titre': projet.titre,
        })
        # Notifier l'équipe
        equipe = projet.equipe.all()
        if equipe.exists():
            _notifier(
                equipe, 'assignation',
                f"Nouveau projet : {projet.titre}",
                f"Vous avez été ajouté à l'équipe du projet « {projet.titre} ».",
                projet=projet,
            )

    def perform_update(self, serializer):
        old_statut = self.get_object().statut
        projet = serializer.save()
        _log_action(self.request.user, 'modification', projet=projet, details={
            'old_statut': old_statut,
            'new_statut': projet.statut,
        })
        if old_statut != projet.statut:
            _log_action(self.request.user, 'changement_statut', projet=projet, details={
                'ancien': old_statut, 'nouveau': projet.statut,
            })

    # --- Actions personnalisées ---

    @action(detail=True, methods=['get'])
    def dashboard(self, request, pk=None):
        """Tableau de bord d'un projet."""
        projet = self.get_object()
        taches = projet.taches.all()

        data = {
            'projet': ProjetDetailSerializer(projet).data,
            'statistiques': {
                'avancement_global': float(projet.pourcentage_avancement),
                'total_taches': taches.count(),
                'taches_a_faire': taches.filter(statut='a_faire').count(),
                'taches_en_cours': taches.filter(statut='en_cours').count(),
                'taches_terminees': taches.filter(statut='termine').count(),
                'taches_en_retard': sum(1 for t in taches if t.est_en_retard),
                'budget_prevu': float(projet.budget_prevu) if projet.budget_prevu else None,
                'budget_consomme': float(projet.budget_consomme),
            },
            'courbe_avancement': self._courbe_avancement(projet),
        }
        return Response(data)

    @action(detail=True, methods=['post'])
    def recalculer(self, request, pk=None):
        """Recalculer l'avancement du projet."""
        projet = self.get_object()
        projet.mettre_a_jour_avancement()
        return Response({
            'avancement': float(projet.pourcentage_avancement),
            'statut': projet.statut,
        })

    @action(detail=True, methods=['get'])
    def gantt(self, request, pk=None):
        """Données Gantt pour un projet."""
        projet = self.get_object()
        taches = projet.taches.select_related('responsable', 'tache_dependante').order_by('date_debut', 'ordre')
        return Response(TacheGanttSerializer(taches, many=True).data)

    @action(detail=True, methods=['get'])
    def historique(self, request, pk=None):
        """Historique des actions sur un projet."""
        projet = self.get_object()
        historique = HistoriqueAction.objects.filter(
            Q(projet=projet) | Q(tache__projet=projet)
        ).select_related('utilisateur').order_by('-created_at')[:100]
        return Response(HistoriqueActionSerializer(historique, many=True).data)

    def _courbe_avancement(self, projet):
        """Génère les points de la courbe d'avancement."""
        historique = HistoriqueAction.objects.filter(
            projet=projet, action='changement_statut'
        ).order_by('created_at')

        points = []
        for entry in historique:
            points.append({
                'date': entry.created_at.strftime('%Y-%m-%d'),
                'avancement': entry.details.get('avancement', 0),
            })
        # Ajouter le point actuel
        points.append({
            'date': timezone.now().strftime('%Y-%m-%d'),
            'avancement': float(projet.pourcentage_avancement),
        })
        return points


# =============================================================================
# B. TÂCHES VIEWSET
# =============================================================================

class TacheViewSet(viewsets.ModelViewSet):
    """
    CRUD pour les tâches + actions : kanban/, soumettre/, valider/.
    """
    permission_classes = [IsAuthenticated, TachePermission]

    def get_queryset(self):
        user = self.request.user
        role = _get_role(user)
        qs = Tache.objects.select_related('projet', 'responsable', 'created_by', 'tache_dependante')

        if role == 'ADMIN':
            pass
        elif role == 'PRESTATAIRE':
            qs = qs.filter(Q(responsable=user) | Q(agents_assignes=user)).distinct()
        else:
            qs = qs.filter(
                Q(responsable=user) |
                Q(agents_assignes=user) |
                Q(projet__responsable=user) |
                Q(projet__equipe=user) |
                Q(created_by=user)
            ).distinct()

        # Filtres query params
        projet_id = self.request.query_params.get('projet')
        if projet_id:
            qs = qs.filter(projet_id=projet_id)

        statut = self.request.query_params.get('statut')
        if statut:
            qs = qs.filter(statut=statut)

        priorite = self.request.query_params.get('priorite')
        if priorite:
            qs = qs.filter(priorite=priorite)

        responsable_id = self.request.query_params.get('responsable')
        if responsable_id:
            qs = qs.filter(responsable_id=responsable_id)

        en_retard = self.request.query_params.get('en_retard')
        if en_retard == 'true':
            today = timezone.now().date()
            qs = qs.filter(date_fin_prevue__lt=today).exclude(statut='termine')

        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(Q(titre__icontains=search) | Q(description__icontains=search))

        return qs

    def get_serializer_class(self):
        if self.action == 'list':
            return TacheListSerializer
        if self.action in ('create', 'update', 'partial_update'):
            return TacheCreateSerializer
        return TacheDetailSerializer

    def create(self, request, *args, **kwargs):
        role = _get_role(request.user)
        if role not in ROLES_MANAGER:
            return Response(
                {'detail': "Vous n'avez pas les droits pour créer une tâche. Seuls les managers peuvent créer des tâches."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        tache = serializer.save(created_by=self.request.user)
        _log_action(self.request.user, 'creation', projet=tache.projet, tache=tache, details={
            'titre': tache.titre,
        })
        # Notifier le responsable et les agents
        destinataires = set()
        if tache.responsable and tache.responsable != self.request.user:
            destinataires.add(tache.responsable)
        for agent in tache.agents_assignes.exclude(id=self.request.user.id):
            destinataires.add(agent)
        if destinataires:
            _notifier(
                list(destinataires), 'creation_tache',
                f"Nouvelle tâche : {tache.titre}",
                f"La tâche « {tache.titre} » vous a été assignée dans le projet « {tache.projet.titre} ».",
                projet=tache.projet, tache=tache,
            )

    def perform_update(self, serializer):
        old = self.get_object()
        old_statut = old.statut
        old_responsable = old.responsable
        old_titre = old.titre
        old_date_fin = old.date_fin_prevue
        old_priorite = old.priorite
        tache = serializer.save()

        auteur = self.request.user.get_full_name() or self.request.user.username
        _log_action(self.request.user, 'modification', projet=tache.projet, tache=tache)

        # --- Notification de modification (champs significatifs) ---
        champs = []
        if old_titre != tache.titre:
            champs.append('titre')
        if old_date_fin != tache.date_fin_prevue:
            champs.append('échéance')
        if old_priorite != tache.priorite:
            champs.append('priorité')

        if champs:
            destinataires = set()
            if tache.responsable and tache.responsable != self.request.user:
                destinataires.add(tache.responsable)
            for agent in tache.agents_assignes.exclude(id=self.request.user.id):
                destinataires.add(agent)
            if destinataires:
                _notifier(
                    list(destinataires), 'modification_tache',
                    f"Tâche modifiée : {tache.titre}",
                    f"{auteur} a modifié la tâche « {tache.titre} » — champs : {', '.join(champs)}.",
                    projet=tache.projet, tache=tache,
                    metadata={'champs': champs},
                )

        # --- Détection de délégation (changement de responsable) ---
        if old_responsable != tache.responsable and tache.responsable:
            ancien_nom = f"{old_responsable.first_name} {old_responsable.last_name}".strip() if old_responsable else "Non assigné"
            nouveau_nom = f"{tache.responsable.first_name} {tache.responsable.last_name}".strip()
            _log_action(self.request.user, 'assignation', projet=tache.projet, tache=tache, details={
                'ancien_responsable': ancien_nom,
                'nouveau_responsable': nouveau_nom,
                'agent': nouveau_nom,
            })
            if tache.responsable != self.request.user:
                _notifier(
                    [tache.responsable], 'assignation',
                    f"Tâche déléguée : {tache.titre}",
                    f"La tâche « {tache.titre} » vous a été déléguée par {auteur}.",
                    projet=tache.projet, tache=tache,
                )

        if old_statut != tache.statut:
            _log_action(self.request.user, 'changement_statut', projet=tache.projet, tache=tache, details={
                'ancien_statut': old_statut, 'nouveau_statut': tache.statut,
            })
            if tache.statut == 'termine':
                tache.date_fin_effective = timezone.now().date()
                tache.pourcentage_avancement = 100
                tache.save(update_fields=['date_fin_effective', 'pourcentage_avancement'])
                dests = _destinataires_tache_terminee(tache, self.request.user)
                if dests:
                    _notifier(
                        dests, 'tache_terminee',
                        f"Tâche terminée : {tache.titre}",
                        f"{auteur} a terminé la tâche « {tache.titre} » dans le projet « {tache.projet.titre} ».",
                        projet=tache.projet, tache=tache,
                    )
            tache.projet.mettre_a_jour_avancement()

    # --- Kanban ---

    @action(detail=False, methods=['get'])
    def kanban(self, request):
        """Vue Kanban : tâches groupées par statut."""
        projet_id = request.query_params.get('projet')
        qs = self.get_queryset()
        if projet_id:
            qs = qs.filter(projet_id=projet_id)

        data = {
            'a_faire': TacheListSerializer(qs.filter(statut='a_faire'), many=True).data,
            'en_cours': TacheListSerializer(qs.filter(statut='en_cours'), many=True).data,
            'termine': TacheListSerializer(qs.filter(statut='termine'), many=True).data,
        }
        return Response(data)

    @action(detail=True, methods=['post'], url_path='changer-statut')
    def changer_statut(self, request, pk=None):
        """Changer le statut d'une tâche (drag & drop Kanban)."""
        tache = self.get_object()
        role = _get_role(request.user)
        # Agent et secrétaire : uniquement leurs propres tâches
        if role not in ROLES_MANAGER:
            is_assigned = (
                tache.responsable == request.user
                or tache.agents_assignes.filter(id=request.user.id).exists()
            )
            if not is_assigned:
                return Response(
                    {'detail': "Vous ne pouvez changer le statut que de vos propres tâches."},
                    status=status.HTTP_403_FORBIDDEN,
                )
        nouveau_statut = request.data.get('statut')
        if nouveau_statut not in dict(Tache.STATUT_CHOICES):
            return Response({'error': 'Statut invalide.'}, status=status.HTTP_400_BAD_REQUEST)

        ancien_statut = tache.statut
        tache.statut = nouveau_statut
        if nouveau_statut == 'termine':
            tache.date_fin_effective = timezone.now().date()
            tache.pourcentage_avancement = 100
        elif nouveau_statut == 'en_cours' and ancien_statut == 'a_faire':
            if not tache.date_debut:
                tache.date_debut = timezone.now().date()
        tache.save()

        _log_action(request.user, 'changement_statut', projet=tache.projet, tache=tache, details={
            'ancien': ancien_statut, 'nouveau': nouveau_statut,
        })

        # Notifier les supérieurs quand une tâche est terminée
        if nouveau_statut == 'termine':
            auteur = request.user.get_full_name() or request.user.username
            dests = _destinataires_tache_terminee(tache, request.user)
            if dests:
                _notifier(
                    dests, 'tache_terminee',
                    f"Tâche terminée : {tache.titre}",
                    f"{auteur} a terminé la tâche « {tache.titre} » dans le projet « {tache.projet.titre} ».",
                    projet=tache.projet, tache=tache,
                )

        tache.projet.mettre_a_jour_avancement()

        return Response(TacheDetailSerializer(tache).data)

    @action(detail=True, methods=['post'])
    def soumettre(self, request, pk=None):
        """Soumettre une tâche pour validation."""
        tache = self.get_object()
        ValidationTache.objects.create(
            tache=tache,
            soumis_par=request.user,
            statut='soumise',
        )
        dests = _destinataires_tache_terminee(tache, request.user)
        if dests:
            _notifier(
                dests, 'validation_requise',
                f"Validation requise : {tache.titre}",
                f"{request.user.get_full_name() or request.user.username} a soumis la tâche « {tache.titre} » pour validation.",
                projet=tache.projet, tache=tache,
            )
        return Response({'message': 'Tâche soumise pour validation.'})

    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        """Valider ou rejeter une tâche soumise. Réservé aux managers."""
        role = _get_role(request.user)
        if role not in ROLES_MANAGER:
            return Response(
                {'detail': "Seuls les managers (Directeur, Supérieur, Admin…) peuvent valider des tâches."},
                status=status.HTTP_403_FORBIDDEN,
            )
        tache = self.get_object()
        decision = request.data.get('decision')  # 'validee' ou 'rejetee'
        commentaire = request.data.get('commentaire', '')

        if decision not in ('validee', 'rejetee'):
            return Response({'error': "Decision doit être 'validee' ou 'rejetee'."}, status=status.HTTP_400_BAD_REQUEST)

        validation = tache.validations.filter(statut='soumise').last()
        if not validation:
            return Response({'error': 'Aucune validation en attente.'}, status=status.HTTP_400_BAD_REQUEST)

        validation.statut = decision
        validation.valide_par = request.user
        validation.commentaire = commentaire
        validation.save()

        if decision == 'validee':
            tache.statut = 'termine'
            tache.date_fin_effective = timezone.now().date()
            tache.pourcentage_avancement = 100
            tache.save()
            tache.projet.mettre_a_jour_avancement()

        # Notifier le soumetteur
        _notifier(
            [validation.soumis_par],
            'livrable_valide' if decision == 'validee' else 'livrable_rejete',
            f"Tâche {'validée' if decision == 'validee' else 'rejetée'} : {tache.titre}",
            f"Votre tâche « {tache.titre} » a été {'validée' if decision == 'validee' else 'rejetée'}. {commentaire}",
            projet=tache.projet, tache=tache,
        )
        return Response({'message': f'Tâche {decision}.', 'validation': ValidationTacheSerializer(validation).data})

    @action(detail=False, methods=['get'], url_path='mes-taches')
    def mes_taches(self, request):
        """Tâches assignées à l'utilisateur courant."""
        qs = self.get_queryset().filter(
            Q(responsable=request.user) | Q(agents_assignes=request.user)
        ).distinct()
        return Response(TacheListSerializer(qs, many=True).data)


# =============================================================================
# C. SOUS-TÂCHES
# =============================================================================

class SousTacheViewSet(viewsets.ModelViewSet):
    serializer_class = SousTacheSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = SousTache.objects.select_related('tache', 'responsable')
        tache_id = self.request.query_params.get('tache')
        if tache_id:
            qs = qs.filter(tache_id=tache_id)
        return qs

    def perform_create(self, serializer):
        st = serializer.save()
        _log_action(self.request.user, 'creation', projet=st.tache.projet, tache=st.tache, details={
            'sous_tache': st.titre,
        })

    def perform_update(self, serializer):
        st = serializer.save()
        if st.statut == 'termine':
            # Recalculer l'avancement de la tâche parent
            tache = st.tache
            tache.pourcentage_avancement = tache.calculer_avancement()
            tache.save(update_fields=['pourcentage_avancement', 'updated_at'])
            tache.projet.mettre_a_jour_avancement()


# =============================================================================
# D. COMMENTAIRES
# =============================================================================

class CommentaireTacheViewSet(viewsets.ModelViewSet):
    serializer_class = CommentaireTacheSerializer
    permission_classes = [IsAuthenticated, CommentairePieceJointePermission]

    def get_queryset(self):
        qs = CommentaireTache.objects.select_related('auteur', 'tache')
        tache_id = self.request.query_params.get('tache')
        if tache_id:
            qs = qs.filter(tache_id=tache_id)
        return qs

    def perform_create(self, serializer):
        comment = serializer.save(auteur=self.request.user)
        tache = comment.tache
        _log_action(self.request.user, 'commentaire', projet=tache.projet, tache=tache, details={
            'extrait': comment.contenu[:100],
        })
        # Notifier les participants de la tâche
        destinataires = set()
        if tache.responsable and tache.responsable != self.request.user:
            destinataires.add(tache.responsable)
        for agent in tache.agents_assignes.exclude(id=self.request.user.id):
            destinataires.add(agent)
        if destinataires:
            _notifier(
                list(destinataires), 'commentaire_ajoute',
                f"Nouveau commentaire sur : {tache.titre}",
                f"{self.request.user.get_full_name() or self.request.user.username} a commenté : {comment.contenu[:100]}",
                projet=tache.projet, tache=tache,
            )


# =============================================================================
# E. PIÈCES JOINTES
# =============================================================================

class PieceJointeViewSet(viewsets.ModelViewSet):
    serializer_class = PieceJointeSerializer
    permission_classes = [IsAuthenticated, CommentairePieceJointePermission]

    def get_queryset(self):
        qs = PieceJointe.objects.select_related('uploaded_by')
        tache_id = self.request.query_params.get('tache')
        if tache_id:
            qs = qs.filter(tache_id=tache_id)
        projet_id = self.request.query_params.get('projet')
        if projet_id:
            qs = qs.filter(projet_id=projet_id)
        return qs

    def perform_create(self, serializer):
        pj = serializer.save(uploaded_by=self.request.user)
        projet = pj.projet or (pj.tache.projet if pj.tache else None)
        tache = pj.tache
        _log_action(self.request.user, 'upload', projet=projet, tache=tache, details={
            'fichier': pj.nom,
        })


# =============================================================================
# F. LIVRABLES
# =============================================================================

class LivrableViewSet(viewsets.ModelViewSet):
    serializer_class = LivrableSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Livrable.objects.select_related('projet', 'tache', 'soumis_par', 'valide_par')
        projet_id = self.request.query_params.get('projet')
        if projet_id:
            qs = qs.filter(projet_id=projet_id)
        return qs

    def perform_create(self, serializer):
        # Auto-increment version si même titre existe dans le même projet
        projet = serializer.validated_data.get('projet')
        titre = serializer.validated_data.get('titre', '')
        existing = Livrable.objects.filter(projet=projet, titre=titre).order_by('-version').first()
        version = (existing.version + 1) if existing else 1

        livrable = serializer.save(
            soumis_par=self.request.user,
            version=version,
            statut='soumis',
        )
        _log_action(self.request.user, 'livrable', projet=livrable.projet, details={
            'titre': livrable.titre, 'version': livrable.version, 'action': 'creation',
        })
        # Notifier le responsable du projet
        if livrable.projet.responsable and livrable.projet.responsable != self.request.user:
            _notifier(
                [livrable.projet.responsable], 'livrable_soumis',
                f"Nouveau livrable : {livrable.titre} v{livrable.version}",
                f"{self.request.user.get_full_name() or self.request.user.username} a soumis le livrable « {livrable.titre} » (v{livrable.version}) pour le projet « {livrable.projet.titre} ».",
                projet=livrable.projet,
            )

    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        """Valider ou rejeter un livrable."""
        livrable = self.get_object()
        decision = request.data.get('decision')  # 'valide' ou 'rejete'
        commentaire = request.data.get('commentaire', '')

        if decision not in ('valide', 'rejete'):
            return Response({'error': "Decision doit être 'valide' ou 'rejete'."}, status=status.HTTP_400_BAD_REQUEST)

        livrable.statut = decision
        livrable.valide_par = request.user
        livrable.commentaire_validation = commentaire
        livrable.date_validation = timezone.now()
        livrable.save()

        _log_action(request.user, 'validation', projet=livrable.projet, details={
            'livrable': livrable.titre, 'decision': decision,
        })

        # Notifier le soumetteur
        if livrable.soumis_par:
            _notifier(
                [livrable.soumis_par],
                'livrable_valide' if decision == 'valide' else 'livrable_rejete',
                f"Livrable {'validé' if decision == 'valide' else 'rejeté'} : {livrable.titre}",
                f"Votre livrable « {livrable.titre} » a été {'validé' if decision == 'valide' else 'rejeté'}. {commentaire}",
                projet=livrable.projet,
            )
        return Response(LivrableSerializer(livrable).data)


# =============================================================================
# G. NOTIFICATIONS
# =============================================================================

class NotificationProjetViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationProjetSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return NotificationProjet.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post'], url_path='marquer-lue')
    def marquer_lue(self, request, pk=None):
        notif = self.get_object()
        notif.marquer_comme_lue()
        return Response({'message': 'Notification marquée comme lue.'})

    @action(detail=False, methods=['post'], url_path='tout-lire')
    def tout_lire(self, request):
        self.get_queryset().filter(lue=False).update(lue=True, date_lecture=timezone.now())
        return Response({'message': 'Toutes les notifications marquées comme lues.'})

    @action(detail=False, methods=['get'], url_path='non-lues')
    def non_lues(self, request):
        qs = self.get_queryset().filter(lue=False)
        return Response({
            'count': qs.count(),
            'notifications': NotificationProjetSerializer(qs[:20], many=True).data,
        })


# =============================================================================
# H. VALIDATION WORKFLOW
# =============================================================================

class ValidationTacheViewSet(viewsets.ModelViewSet):
    serializer_class = ValidationTacheSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = ValidationTache.objects.select_related('tache', 'soumis_par', 'valide_par')
        tache_id = self.request.query_params.get('tache')
        if tache_id:
            qs = qs.filter(tache_id=tache_id)
        statut = self.request.query_params.get('statut')
        if statut:
            qs = qs.filter(statut=statut)
        return qs

    def perform_create(self, serializer):
        serializer.save(soumis_par=self.request.user)


# =============================================================================
# I. HISTORIQUE
# =============================================================================

class HistoriqueActionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = HistoriqueActionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = HistoriqueAction.objects.select_related('utilisateur', 'projet', 'tache')
        projet_id = self.request.query_params.get('projet')
        if projet_id:
            qs = qs.filter(Q(projet_id=projet_id) | Q(tache__projet_id=projet_id))
        return qs


# =============================================================================
# J. DASHBOARD GLOBAL
# =============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_global(request):
    """Tableau de bord global de tous les projets."""
    user = request.user
    role = _get_role(user)

    if role == 'ADMIN':
        projets = Projet.objects.all()
        taches = Tache.objects.all()
    else:
        projets = Projet.objects.filter(
            Q(responsable=user) | Q(equipe=user) | Q(created_by=user)
        ).distinct()
        taches = Tache.objects.filter(
            Q(responsable=user) | Q(agents_assignes=user) |
            Q(projet__responsable=user) | Q(projet__equipe=user)
        ).distinct()

    today = timezone.now().date()

    # Statistiques projets
    stats_projets = {
        'total': projets.count(),
        'planifies': projets.filter(statut='planifie').count(),
        'en_cours': projets.filter(statut='en_cours').count(),
        'termines': projets.filter(statut='termine').count(),
        'en_retard': projets.filter(statut='en_retard').count(),
        'suspendus': projets.filter(statut='suspendu').count(),
    }

    # Statistiques tâches
    stats_taches = {
        'total': taches.count(),
        'a_faire': taches.filter(statut='a_faire').count(),
        'en_cours': taches.filter(statut='en_cours').count(),
        'terminees': taches.filter(statut='termine').count(),
        'en_retard': taches.filter(
            date_fin_prevue__lt=today
        ).exclude(statut='termine').count(),
    }

    # Tâches urgentes (haute priorité, pas terminées, proches de l'échéance)
    taches_urgentes = taches.filter(
        priorite='haute',
        date_fin_prevue__lte=today + timedelta(days=3),
    ).exclude(statut='termine').order_by('date_fin_prevue')[:10]

    # Dernières notifications non lues
    notifs = NotificationProjet.objects.filter(user=user, lue=False).order_by('-created_at')[:5]

    data = {
        'projets': stats_projets,
        'taches': stats_taches,
        'taches_urgentes': TacheListSerializer(taches_urgentes, many=True).data,
        'notifications_non_lues': NotificationProjetSerializer(notifs, many=True).data,
    }
    return Response(data)


# =============================================================================
# K. REPORTING
# =============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def rapport_projet(request, projet_id):
    """Rapport détaillé d'un projet."""
    try:
        projet = Projet.objects.get(id=projet_id)
    except Projet.DoesNotExist:
        return Response({'error': 'Projet introuvable.'}, status=status.HTTP_404_NOT_FOUND)

    taches = projet.taches.all()
    today = timezone.now().date()

    # Performance par agent
    agents_performance = []
    equipe = set()
    if projet.responsable:
        equipe.add(projet.responsable)
    for t in taches:
        if t.responsable:
            equipe.add(t.responsable)
    for agent in equipe:
        taches_agent = taches.filter(responsable=agent)
        total = taches_agent.count()
        terminees = taches_agent.filter(statut='termine').count()
        en_retard = sum(1 for t in taches_agent if t.est_en_retard)
        agents_performance.append({
            'agent': {
                'id': agent.id,
                'nom': agent.get_full_name() or agent.username,
            },
            'total_taches': total,
            'terminees': terminees,
            'en_retard': en_retard,
            'taux_completion': round((terminees / total) * 100, 1) if total > 0 else 0,
        })

    data = {
        'projet': ProjetDetailSerializer(projet).data,
        'indicateurs': {
            'taux_avancement': float(projet.pourcentage_avancement),
            'taux_retard': round(
                (sum(1 for t in taches if t.est_en_retard) / taches.count() * 100)
                if taches.count() > 0 else 0, 1
            ),
            'taches_terminees': taches.filter(statut='termine').count(),
            'total_taches': taches.count(),
            'jours_restants': (projet.date_fin_prevue - today).days if projet.date_fin_prevue else None,
        },
        'performance_agents': agents_performance,
        'livrables': LivrableSerializer(projet.livrables.all(), many=True).data,
    }
    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def rapport_agent(request, user_id=None):
    """Score de performance d'un agent."""
    target_user = User.objects.get(id=user_id) if user_id else request.user

    taches = Tache.objects.filter(
        Q(responsable=target_user) | Q(agents_assignes=target_user)
    ).distinct()

    total = taches.count()
    terminees = taches.filter(statut='termine').count()
    en_retard = sum(1 for t in taches if t.est_en_retard)
    dans_les_temps = taches.filter(
        statut='termine', date_fin_effective__lte=F('date_fin_prevue')
    ).count()

    score = 0
    if total > 0:
        score = round(
            (terminees / total * 50) +
            (dans_les_temps / max(terminees, 1) * 50),
            1
        )

    data = {
        'agent': {
            'id': target_user.id,
            'nom': target_user.get_full_name() or target_user.username,
        },
        'statistiques': {
            'total_taches': total,
            'terminees': terminees,
            'en_cours': taches.filter(statut='en_cours').count(),
            'a_faire': taches.filter(statut='a_faire').count(),
            'en_retard': en_retard,
            'dans_les_temps': dans_les_temps,
        },
        'score_performance': score,
        'detail_score': {
            'taux_completion': round((terminees / total * 100), 1) if total > 0 else 0,
            'taux_respect_delais': round((dans_les_temps / max(terminees, 1) * 100), 1) if terminees > 0 else 0,
        },
    }
    return Response(data)


# =============================================================================
# L. DÉTECTION DES RETARDS (appelé par Celery ou cron)
# =============================================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def detecter_retards(request):
    """
    Détecte les retards et envoie les notifications.
    Accessible à tous les utilisateurs authentifiés (filtrés par leur scope).
    Déduplique : 1 seule notification retard/rappel par tâche et par destinataire par jour.
    """
    today = timezone.now().date()
    user = request.user
    role = _get_role(user)

    # Scope : ADMIN voit tout, les autres voient leurs projets/tâches
    if role == 'ADMIN':
        taches_base = Tache.objects.select_related('projet', 'responsable').all()
    else:
        taches_base = Tache.objects.select_related('projet', 'responsable').filter(
            Q(responsable=user) | Q(agents_assignes=user) |
            Q(projet__responsable=user) | Q(projet__equipe=user)
        ).distinct()

    # ── Retards ──────────────────────────────────────────────────────────────
    taches_retard = taches_base.filter(
        date_fin_prevue__lt=today
    ).exclude(statut='termine')

    count_retard = 0
    for tache in taches_retard:
        destinataires = set()
        if tache.responsable:
            destinataires.add(tache.responsable)
        if tache.projet.responsable:
            destinataires.add(tache.projet.responsable)

        for dest in destinataires:
            # Déduplication : 1 notif retard par tâche/destinataire/jour
            already = NotificationProjet.objects.filter(
                user=dest, tache=tache,
                type_notification='retard_detecte',
                created_at__date=today,
            ).exists()
            if not already:
                jours = (today - tache.date_fin_prevue).days
                _notifier(
                    [dest], 'retard_detecte',
                    f"Retard : {tache.titre}",
                    f"La tâche « {tache.titre} » est en retard de {jours} jour(s). "
                    f"Échéance : {tache.date_fin_prevue.strftime('%d/%m/%Y')}.",
                    projet=tache.projet, tache=tache,
                    metadata={'jours_retard': jours},
                )
                count_retard += 1

    # ── Rappels J-7 / J-3 / J-1 ─────────────────────────────────────────────
    count_rappels = 0
    DELAIS = {7: 'dans 7 jours', 3: 'dans 3 jours', 1: 'demain'}
    for jours_avant, label in DELAIS.items():
        cible = today + timedelta(days=jours_avant)
        rappels = taches_base.filter(
            date_fin_prevue=cible
        ).exclude(statut='termine')

        for tache in rappels:
            if not tache.responsable:
                continue
            already = NotificationProjet.objects.filter(
                user=tache.responsable, tache=tache,
                type_notification='rappel_echeance',
                created_at__date=today,
                metadata__jours_restants=jours_avant,
            ).exists()
            if not already:
                _notifier(
                    [tache.responsable], 'rappel_echeance',
                    f"Rappel J-{jours_avant} : {tache.titre}",
                    f"La tâche « {tache.titre} » arrive à échéance {label} "
                    f"({cible.strftime('%d/%m/%Y')}).",
                    projet=tache.projet, tache=tache,
                    metadata={'jours_restants': jours_avant},
                )
                count_rappels += 1

    # ── Mettre à jour le statut des projets en retard ────────────────────────
    if role == 'ADMIN':
        projets_retard = Projet.objects.filter(
            date_fin_prevue__lt=today
        ).exclude(statut__in=['termine', 'suspendu', 'en_retard'])
        projets_retard.update(statut='en_retard')
        nb_projets = projets_retard.count()
    else:
        nb_projets = 0

    return Response({
        'taches_en_retard': taches_retard.count(),
        'notifications_retard': count_retard,
        'rappels_envoyes': count_rappels,
        'projets_mis_a_jour': nb_projets,
    })


# =============================================================================
# M. AGENDA / CALENDRIER
# =============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def agenda_calendrier(request):
    """
    Retourne les événements calendrier de l'utilisateur:
    - Tâches (début/fin)
    - Échéances proches (rappels)
    - Projets (dates clés)
    """
    user = request.user
    mois = request.query_params.get('mois')  # format YYYY-MM
    today = timezone.now().date()

    # Tâches de l'utilisateur
    taches = Tache.objects.filter(
        Q(responsable=user) | Q(agents_assignes=user)
    ).distinct().select_related('projet', 'responsable')

    # Filtrer par mois si spécifié
    if mois:
        try:
            year, month = map(int, mois.split('-'))
            from calendar import monthrange
            debut_mois = timezone.datetime(year, month, 1).date()
            fin_mois = timezone.datetime(year, month, monthrange(year, month)[1]).date()
            taches = taches.filter(
                Q(date_debut__range=[debut_mois, fin_mois]) |
                Q(date_fin_prevue__range=[debut_mois, fin_mois]) |
                Q(date_debut__lte=debut_mois, date_fin_prevue__gte=debut_mois)
            )
        except (ValueError, TypeError):
            pass

    events = []

    for t in taches:
        # Tâche comme événement
        events.append({
            'id': f'tache-{t.id}',
            'type': 'tache',
            'titre': t.titre,
            'description': t.description[:100] if t.description else '',
            'date_debut': str(t.date_debut) if t.date_debut else None,
            'date_fin': str(t.date_fin_prevue) if t.date_fin_prevue else None,
            'statut': t.statut,
            'priorite': t.priorite,
            'est_en_retard': t.est_en_retard,
            'projet_id': t.projet_id,
            'projet_titre': t.projet.titre,
            'responsable': t.responsable.get_full_name() if t.responsable else None,
            'color': '#ef4444' if t.est_en_retard else (
                '#f97316' if t.priorite == 'haute' else (
                    '#3b82f6' if t.statut == 'en_cours' else (
                        '#22c55e' if t.statut == 'termine' else '#6b7280'
                    )
                )
            ),
        })

        # Rappel d'échéance (J-2)
        if t.date_fin_prevue and t.statut != 'termine':
            rappel_date = t.date_fin_prevue - timedelta(days=2)
            if rappel_date >= today:
                events.append({
                    'id': f'rappel-{t.id}',
                    'type': 'rappel',
                    'titre': f'⏰ Rappel: {t.titre}',
                    'description': f'Échéance dans 2 jours',
                    'date_debut': str(rappel_date),
                    'date_fin': str(rappel_date),
                    'statut': 'rappel',
                    'priorite': t.priorite,
                    'est_en_retard': False,
                    'projet_id': t.projet_id,
                    'projet_titre': t.projet.titre,
                    'responsable': None,
                    'color': '#eab308',
                })

    # Projets (dates clés: début et fin)
    projets = Projet.objects.filter(
        Q(responsable=user) | Q(equipe=user)
    ).distinct()

    for p in projets:
        events.append({
            'id': f'projet-debut-{p.id}',
            'type': 'projet',
            'titre': f'🚀 Début: {p.titre}',
            'description': '',
            'date_debut': str(p.date_debut),
            'date_fin': str(p.date_debut),
            'statut': p.statut,
            'priorite': None,
            'est_en_retard': False,
            'projet_id': p.id,
            'projet_titre': p.titre,
            'responsable': None,
            'color': '#8b5cf6',
        })
        if p.date_fin_prevue:
            events.append({
                'id': f'projet-fin-{p.id}',
                'type': 'echeance_projet',
                'titre': f'🏁 Fin prévue: {p.titre}',
                'description': '',
                'date_debut': str(p.date_fin_prevue),
                'date_fin': str(p.date_fin_prevue),
                'statut': p.statut,
                'priorite': None,
                'est_en_retard': p.est_en_retard,
                'projet_id': p.id,
                'projet_titre': p.titre,
                'responsable': None,
                'color': '#ef4444' if p.est_en_retard else '#8b5cf6',
            })

    return Response({
        'events': events,
        'stats': {
            'total_events': len(events),
            'taches_en_retard': sum(1 for e in events if e['est_en_retard'] and e['type'] == 'tache'),
            'rappels': sum(1 for e in events if e['type'] == 'rappel'),
        }
    })


# =============================================================================
# N. REPORTING AVANCÉ
# =============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def rapport_global(request):
    """Rapport global avec KPIs, filtrage par période, données pour export."""
    user = request.user
    role = _get_role(user)
    periode = request.query_params.get('periode', 'mensuel')  # hebdo, mensuel, tout
    today = timezone.now().date()

    # Filtrage par période
    if periode == 'hebdo':
        date_debut = today - timedelta(days=today.weekday())
        date_fin = date_debut + timedelta(days=6)
    elif periode == 'mensuel':
        date_debut = today.replace(day=1)
        next_month = (date_debut.replace(day=28) + timedelta(days=4))
        date_fin = next_month.replace(day=1) - timedelta(days=1)
    else:
        date_debut = None
        date_fin = None

    # Base querysets
    if role == 'ADMIN':
        projets = Projet.objects.all()
        taches = Tache.objects.all()
    else:
        projets = Projet.objects.filter(
            Q(responsable=user) | Q(equipe=user) | Q(created_by=user)
        ).distinct()
        taches = Tache.objects.filter(
            Q(responsable=user) | Q(agents_assignes=user) |
            Q(projet__responsable=user) | Q(projet__equipe=user)
        ).distinct()

    # Filtrer par période
    taches_periode = taches
    if date_debut and date_fin:
        taches_periode = taches.filter(
            Q(created_at__date__range=[date_debut, date_fin]) |
            Q(date_fin_prevue__range=[date_debut, date_fin])
        )

    # KPIs
    total_taches = taches.count()
    terminees = taches.filter(statut='termine').count()
    en_retard = sum(1 for t in taches if t.est_en_retard)
    dans_les_temps = taches.filter(
        statut='termine', date_fin_effective__lte=F('date_fin_prevue')
    ).count()

    kpis = {
        'taux_avancement': round((terminees / total_taches * 100), 1) if total_taches > 0 else 0,
        'taux_retard': round((en_retard / total_taches * 100), 1) if total_taches > 0 else 0,
        'taux_respect_delais': round((dans_les_temps / max(terminees, 1) * 100), 1) if terminees > 0 else 0,
        'total_taches': total_taches,
        'taches_terminees': terminees,
        'taches_en_retard': en_retard,
        'taches_dans_les_temps': dans_les_temps,
        'taches_en_cours': taches.filter(statut='en_cours').count(),
        'taches_a_faire': taches.filter(statut='a_faire').count(),
        'projets_total': projets.count(),
        'projets_termines': projets.filter(statut='termine').count(),
        'projets_en_retard': projets.filter(statut='en_retard').count(),
    }

    # Tâches période courante (pour export)
    taches_export = []
    for t in taches_periode.select_related('projet', 'responsable')[:200]:
        taches_export.append({
            'id': t.id,
            'titre': t.titre,
            'projet': t.projet.titre,
            'responsable': t.responsable.get_full_name() if t.responsable else '-',
            'statut': t.get_statut_display(),
            'priorite': t.get_priorite_display(),
            'date_debut': str(t.date_debut) if t.date_debut else '-',
            'date_fin_prevue': str(t.date_fin_prevue) if t.date_fin_prevue else '-',
            'en_retard': t.est_en_retard,
            'avancement': float(t.pourcentage_avancement),
        })

    # Performance agents (top 20)
    agents_perf = []
    agents_set = set()
    for t in taches.select_related('responsable'):
        if t.responsable:
            agents_set.add(t.responsable)
    for agent in list(agents_set)[:20]:
        t_agent = taches.filter(responsable=agent)
        total_a = t_agent.count()
        term_a = t_agent.filter(statut='termine').count()
        retard_a = sum(1 for ta in t_agent if ta.est_en_retard)
        agents_perf.append({
            'id': agent.id,
            'nom': agent.get_full_name() or agent.username,
            'total': total_a,
            'terminees': term_a,
            'en_retard': retard_a,
            'taux': round((term_a / total_a * 100), 1) if total_a > 0 else 0,
        })
    agents_perf.sort(key=lambda x: x['taux'], reverse=True)

    # Projets résumé
    projets_resume = []
    for p in projets.select_related('responsable')[:50]:
        projets_resume.append({
            'id': p.id,
            'titre': p.titre,
            'statut': p.statut,
            'avancement': float(p.pourcentage_avancement),
            'responsable': p.responsable.get_full_name() if p.responsable else '-',
            'date_fin_prevue': str(p.date_fin_prevue) if p.date_fin_prevue else '-',
            'en_retard': p.est_en_retard,
            'taches_total': p.nombre_taches,
            'taches_terminees': p.taches_terminees,
        })

    return Response({
        'periode': {
            'type': periode,
            'debut': str(date_debut) if date_debut else None,
            'fin': str(date_fin) if date_fin else None,
        },
        'kpis': kpis,
        'taches': taches_export,
        'agents_performance': agents_perf,
        'projets': projets_resume,
    })
