"""
ViewSets pour le module Agenda (Rendez-vous et Réunions)
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, timedelta

from core.models import RendezVous, RendezVousDocument, Reunion, ReunionPresence, UserProfile, Notification
from core.agenda_serializers import (
    RendezVousSerializer, RendezVousDocumentSerializer,
    ReunionSerializer, ReunionPresenceSerializer
)


class RendezVousViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les rendez-vous
    
    Permissions:
    - ADMIN, DIRECTEUR, SOUS_DIRECTEUR, CHEF_SERVICE, SUPERIEUR: Peuvent créer des rendez-vous
    - SECRETAIRE: Peut créer pour son supérieur
    - AGENT: Peut consulter ses rendez-vous
    """
    queryset = RendezVous.objects.all()
    serializer_class = RendezVousSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['objet', 'lieu', 'visiteur_nom', 'visiteur_prenoms', 'visiteur_structure']
    ordering_fields = ['date_debut', 'date_fin', 'created_at']
    ordering = ['-date_debut']
    
    def get_queryset(self):
        """
        Filtrer les rendez-vous selon le rôle de l'utilisateur
        """
        user = self.request.user
        profile = getattr(user, 'profile', None)
        
        if not profile:
            return RendezVous.objects.none()
        
        role = profile.role
        
        # ADMIN voit tous les rendez-vous
        if role == 'ADMIN':
            queryset = RendezVous.objects.all()
        # DIRECTEUR, SOUS_DIRECTEUR, CHEF_SERVICE, SUPERIEUR voient leurs rendez-vous organisés et ceux où ils sont responsables
        elif role in ['DIRECTEUR', 'SOUS_DIRECTEUR', 'CHEF_SERVICE', 'SUPERIEUR']:
            queryset = RendezVous.objects.filter(
                Q(organisateur=user) | Q(responsable=user)
            )
        # SECRETAIRE voit les rendez-vous qu'il organise ou dont il est responsable
        elif role == 'SECRETAIRE':
            queryset = RendezVous.objects.filter(
                Q(organisateur=user) | Q(responsable=user)
            )
        # AGENT ne voit que ceux dont il est organisateur (ou responsable si assigné)
        else:
            queryset = RendezVous.objects.filter(Q(organisateur=user) | Q(responsable=user))
        
        # Filtres optionnels
        statut = self.request.query_params.get('statut')
        if statut:
            queryset = queryset.filter(statut=statut)
        
        date_debut = self.request.query_params.get('date_debut')
        date_fin = self.request.query_params.get('date_fin')
        if date_debut and date_fin:
            queryset = queryset.filter(
                date_debut__gte=date_debut,
                date_fin__lte=date_fin
            )
        
        return queryset.distinct()
    
    def perform_create(self, serializer):
        """Enregistrer l'organisateur et notifier le responsable si présent"""
        rendezvous = serializer.save(organisateur=self.request.user)
        # Envoyer une notification au responsable si défini
        if rendezvous.responsable:
            try:
                Notification.objects.create(
                    user=rendezvous.responsable,
                    type_notif='nouvelle_demande',
                    contenu=f"Nouveau rendez-vous assigné: {rendezvous.visiteur_nom} {rendezvous.visiteur_prenoms} ({rendezvous.objet[:80]})",
                    lien=f"/agenda"
                )
            except Exception:
                pass
    
    @action(detail=True, methods=['post'])
    def changer_statut(self, request, pk=None):
        """
        Changer le statut d'un rendez-vous
        """
        rendezvous = self.get_object()
        nouveau_statut = request.data.get('statut')
        
        if nouveau_statut not in dict(RendezVous.STATUT_CHOICES):
            return Response(
                {'error': 'Statut invalide'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        rendezvous.statut = nouveau_statut
        rendezvous.save()
        
        serializer = self.get_serializer(rendezvous)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def mes_rendezvous(self, request):
        """
        Récupérer les rendez-vous de l'utilisateur connecté
        """
        user = request.user
        rendezvous = RendezVous.objects.filter(
            Q(organisateur=user) | Q(responsable=user)
        ).order_by('-date_debut')
        
        serializer = self.get_serializer(rendezvous, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def a_venir(self, request):
        """
        Récupérer les rendez-vous à venir
        """
        user = request.user
        now = timezone.now()
        
        rendezvous = RendezVous.objects.filter(
            Q(organisateur=user) | Q(responsable=user),
            date_debut__gte=now,
            statut='prevu'
        ).order_by('date_debut')

    @action(detail=False, methods=['get'])
    def superieurs(self, request):
        """Retourne la liste des utilisateurs ayant un rôle supérieur (DIRECTEUR, SOUS_DIRECTEUR, CHEF_SERVICE, SUPERIEUR)"""
        roles = ['DIRECTEUR', 'SOUS_DIRECTEUR', 'CHEF_SERVICE', 'SUPERIEUR']
        users = UserProfile.objects.filter(role__in=roles).select_related('user')
        data = [
            {
                'id': up.user.id,
                'username': up.user.username,
                'first_name': up.user.first_name,
                'last_name': up.user.last_name,
                'email': up.user.email,
                'role': up.role,
            }
            for up in users
        ]
        return Response(data)
        
        serializer = self.get_serializer(rendezvous, many=True)
        return Response(serializer.data)


class RendezVousDocumentViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les documents associés aux rendez-vous
    """
    queryset = RendezVousDocument.objects.all()
    serializer_class = RendezVousDocumentSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)


class ReunionViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les réunions
    
    Permissions:
    - ADMIN, DIRECTEUR, SOUS_DIRECTEUR, CHEF_SERVICE: Peuvent créer des réunions
    - SUPERIEUR, SECRETAIRE: Peuvent créer pour leur service
    - AGENT: Peut consulter les réunions auxquelles il participe
    """
    queryset = Reunion.objects.all()
    serializer_class = ReunionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['intitule', 'description', 'lieu']
    ordering_fields = ['date_debut', 'date_fin', 'created_at']
    ordering = ['-date_debut']
    
    def get_queryset(self):
        """
        Filtrer les réunions selon le rôle de l'utilisateur
        """
        user = self.request.user
        profile = getattr(user, 'profile', None)
        
        if not profile:
            return Reunion.objects.none()
        
        role = profile.role
        
        # ADMIN voit toutes les réunions
        if role == 'ADMIN':
            queryset = Reunion.objects.all()
        # DIRECTEUR, SOUS_DIRECTEUR, CHEF_SERVICE voient leurs réunions et celles de leur périmètre
        elif role in ['DIRECTEUR', 'SOUS_DIRECTEUR', 'CHEF_SERVICE', 'SUPERIEUR']:
            queryset = Reunion.objects.filter(
                Q(organisateur=user) | Q(participants=user)
            )
        # SECRETAIRE voit les réunions de son service
        elif role == 'SECRETAIRE':
            queryset = Reunion.objects.filter(
                Q(organisateur=user) | Q(participants=user)
            )
        # AGENT voit uniquement les réunions où il participe
        else:
            queryset = Reunion.objects.filter(participants=user)
        
        # Filtres optionnels
        statut = self.request.query_params.get('statut')
        if statut:
            queryset = queryset.filter(statut=statut)
        
        date_debut = self.request.query_params.get('date_debut')
        date_fin = self.request.query_params.get('date_fin')
        if date_debut and date_fin:
            queryset = queryset.filter(
                date_debut__gte=date_debut,
                date_fin__lte=date_fin
            )
        
        return queryset.distinct()
    
    def perform_create(self, serializer):
        """
        Enregistrer l'organisateur lors de la création
        """
        serializer.save(organisateur=self.request.user)
    
    @action(detail=True, methods=['post'])
    def changer_statut(self, request, pk=None):
        """
        Changer le statut d'une réunion
        """
        reunion = self.get_object()
        nouveau_statut = request.data.get('statut')
        
        if nouveau_statut not in dict(Reunion.STATUT_CHOICES):
            return Response(
                {'error': 'Statut invalide'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reunion.statut = nouveau_statut
        reunion.save()
        
        serializer = self.get_serializer(reunion)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def marquer_presence(self, request, pk=None):
        """
        Marquer la présence d'un participant
        """
        reunion = self.get_object()
        participant_id = request.data.get('participant_id')
        present = request.data.get('present', True)
        heure_arrivee = request.data.get('heure_arrivee')
        commentaire = request.data.get('commentaire', '')
        
        if not participant_id:
            return Response(
                {'error': 'participant_id requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        presence, created = ReunionPresence.objects.get_or_create(
            reunion=reunion,
            participant_id=participant_id,
            defaults={
                'present': present,
                'heure_arrivee': heure_arrivee,
                'commentaire': commentaire
            }
        )
        
        if not created:
            presence.present = present
            if heure_arrivee:
                presence.heure_arrivee = heure_arrivee
            if commentaire:
                presence.commentaire = commentaire
            presence.save()
        
        serializer = ReunionPresenceSerializer(presence)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def mes_reunions(self, request):
        """
        Récupérer les réunions de l'utilisateur connecté
        """
        user = request.user
        reunions = Reunion.objects.filter(
            Q(organisateur=user) | Q(participants=user)
        ).order_by('-date_debut')
        
        serializer = self.get_serializer(reunions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def a_venir(self, request):
        """
        Récupérer les réunions à venir
        """
        user = request.user
        now = timezone.now()
        
        reunions = Reunion.objects.filter(
            Q(organisateur=user) | Q(participants=user),
            date_debut__gte=now,
            statut='prevu'
        ).order_by('date_debut')
        
        serializer = self.get_serializer(reunions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def rapport_presence(self, request, pk=None):
        """
        Générer un rapport de présence pour une réunion
        """
        reunion = self.get_object()
        presences = reunion.presences.all()
        
        rapport = {
            'reunion': self.get_serializer(reunion).data,
            'total_participants': reunion.participants.count(),
            'presents': presences.filter(present=True).count(),
            'absents': presences.filter(present=False).count(),
            'non_marques': reunion.participants.count() - presences.count(),
            'details': ReunionPresenceSerializer(presences, many=True).data
        }
        
        return Response(rapport)


class ReunionPresenceViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les présences aux réunions
    """
    queryset = ReunionPresence.objects.all()
    serializer_class = ReunionPresenceSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Filtrer les présences selon la réunion
        """
        reunion_id = self.request.query_params.get('reunion')
        if reunion_id:
            return ReunionPresence.objects.filter(reunion_id=reunion_id)
        return ReunionPresence.objects.all()
