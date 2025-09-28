from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Diligence, DiligenceDocument, DiligenceNotification, Courrier
from .serializers import DiligenceSerializer, DiligenceDocumentSerializer, DiligenceNotificationSerializer

class DiligenceDocumentViewSet(viewsets.ModelViewSet):
    queryset = DiligenceDocument.objects.all().order_by('-created_at')
    serializer_class = DiligenceDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def validate_document(self, request, pk=None):
        """Valider un document par un administrateur"""
        document = self.get_object()
        
        # Vérifier les permissions (seuls les admins peuvent valider)
        if not hasattr(request.user, 'profile') or request.user.profile.role != 'ADMIN':
            return Response(
                {'error': 'Seuls les administrateurs peuvent valider les documents'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        document.statut = 'valide'
        document.validated_by = request.user
        document.validated_at = timezone.now()
        document.save()
        
        # Créer notification pour l'auteur du document
        DiligenceNotification.objects.create(
            user=document.created_by,
            diligence=document.diligence,
            type_notification='document_valide',
            message=f'Votre document "{document.titre}" a été validé et archivé.'
        )
        
        return Response({'message': 'Document validé avec succès'})

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def archive_document(self, request, pk=None):
        """Archiver un document validé"""
        document = self.get_object()
        
        if document.statut != 'valide':
            return Response(
                {'error': 'Seuls les documents validés peuvent être archivés'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        document.statut = 'archive'
        document.save()
        
        return Response({'message': 'Document archivé avec succès'})

class DiligenceNotificationViewSet(viewsets.ModelViewSet):
    serializer_class = DiligenceNotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return DiligenceNotification.objects.filter(user=self.request.user).order_by('-created_at')

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """Marquer une notification comme lue"""
        notification = self.get_object()
        notification.read = True
        notification.save()
        return Response({'message': 'Notification marquée comme lue'})

    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        """Marquer toutes les notifications comme lues"""
        self.get_queryset().update(read=True)
        return Response({'message': 'Toutes les notifications marquées comme lues'})

class EnhancedDiligenceViewSet(viewsets.ModelViewSet):
    queryset = Diligence.objects.all().order_by('-created_at')
    serializer_class = DiligenceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        profile = getattr(user, 'profile', None)
        base_qs = Diligence.objects.select_related(
            'courrier',
            'courrier__service',
            'courrier__service__direction',
            'direction'
        ).prefetch_related(
            'agents',
            'services_concernes',
            'services_concernes__direction'
        ).all().order_by('-created_at')

        if not profile:
            return Diligence.objects.none()

        role = profile.role
        print(f"[DEBUG] EnhancedDiligenceViewSet get_queryset - User: {user.username} (ID: {user.id}), Role: {role}")

        # Build queryset for diligences accessible by ImputationAccess
        from core.models import ImputationAccess
        imputation_access_qs = base_qs.filter(imputation_access__user=user)
        print(f"[DEBUG] EnhancedDiligenceViewSet ImputationAccess diligences count: {imputation_access_qs.count()}")

        # Diligences où l'utilisateur est dans les agents assignés
        assigned_qs = base_qs.filter(agents=user)
        print(f"[DEBUG] EnhancedDiligenceViewSet Assigned diligences count: {assigned_qs.count()}")
        
        # Filtrage par rôle
        if role == 'AGENT':
            qs = assigned_qs
            print(f"[DEBUG] EnhancedDiligenceViewSet AGENT - Using only assigned diligences")
        elif role in ['SUPERIEUR', 'SECRETAIRE']:
            qs = assigned_qs
            print(f"[DEBUG] EnhancedDiligenceViewSet SUPERIEUR/SECRETAIRE - Using only assigned diligences")
        elif role == 'DIRECTEUR':
            if profile.direction:
                direction_assigned_qs = base_qs.filter(
                    agents__profile__service__direction=profile.direction
                )
                qs = assigned_qs | direction_assigned_qs
                print(f"[DEBUG] EnhancedDiligenceViewSet DIRECTEUR - Using assigned + direction diligences")
            else:
                qs = assigned_qs
                print(f"[DEBUG] EnhancedDiligenceViewSet DIRECTEUR - Using only assigned diligences (no direction)")
        elif role == 'ADMIN':
            qs = base_qs
            print(f"[DEBUG] EnhancedDiligenceViewSet ADMIN - Using all diligences")
        else:
            qs = assigned_qs
            print(f"[DEBUG] EnhancedDiligenceViewSet OTHER ROLE - Using only assigned diligences")

        # Combine with ImputationAccess-based queryset
        final_qs = (qs | imputation_access_qs).distinct()
        print(f"[DEBUG] EnhancedDiligenceViewSet Final queryset count: {final_qs.count()}")
        
        return final_qs
    
    def update(self, request, *args, **kwargs):
        print(f"[DEBUG] EnhancedDiligenceViewSet update - User: {request.user}, Data: {request.data}")
        try:
            response = super().update(request, *args, **kwargs)
            print(f"[DEBUG] Diligence updated successfully: {response.data}")
            return response
        except Exception as e:
            print(f"[ERROR] Diligence update failed: {str(e)}")
            raise
    
    def partial_update(self, request, *args, **kwargs):
        print(f"[DEBUG] EnhancedDiligenceViewSet partial_update - User: {request.user}, Data: {request.data}")
        try:
            response = super().partial_update(request, *args, **kwargs)
            print(f"[DEBUG] Diligence partially updated successfully: {response.data}")
            return response
        except Exception as e:
            print(f"[ERROR] Diligence partial update failed: {str(e)}")
            raise

    @action(detail=False, methods=['post'])
    def create_from_courrier(self, request):
        """Créer une diligence à partir d'un courrier"""
        courrier_id = request.data.get('courrier_id')
        
        if not courrier_id:
            return Response(
                {'error': 'ID du courrier requis'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            courrier = Courrier.objects.get(id=courrier_id)
        except Courrier.DoesNotExist:
            return Response(
                {'error': 'Courrier introuvable'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Créer la diligence avec les données du courrier
        diligence_data = {
            'type_diligence': 'courrier',
            'reference_courrier': courrier.reference,
            'courrier': courrier.id,
            'objet': courrier.objet,
            'expediteur': courrier.expediteur,
            'date_reception': courrier.date_reception,
            'domaine': request.data.get('domaine', 'autre'),
            'categorie': request.data.get('categorie', 'NORMAL'),
            'instructions': request.data.get('instructions', ''),
            'date_limite': request.data.get('date_limite'),
            'agents_ids': request.data.get('agents_ids', []),
            'services_concernes_ids': request.data.get('services_concernes_ids', [])
        }
        
        serializer = self.get_serializer(data=diligence_data)
        if serializer.is_valid():
            diligence = serializer.save()
            
            # Créer notifications pour les agents assignés
            for agent in diligence.agents.all():
                DiligenceNotification.objects.create(
                    user=agent,
                    diligence=diligence,
                    type_notification='nouvelle_diligence',
                    message=f'Nouvelle diligence assignée: {diligence.reference_courrier}'
                )
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def create_spontaneous(self, request):
        """Créer une diligence spontanée (non basée sur un courrier)"""
        diligence_data = {
            'type_diligence': 'spontanee',
            'reference_courrier': f"SPONT-{timezone.now().strftime('%Y%m%d%H%M%S')}",
            'objet': request.data.get('objet', ''),
            'domaine': request.data.get('domaine', 'autre'),
            'categorie': request.data.get('categorie', 'NORMAL'),
            'instructions': request.data.get('instructions', ''),
            'date_limite': request.data.get('date_limite'),
            'agents_ids': request.data.get('agents_ids', []),
            'services_concernes_ids': request.data.get('services_concernes_ids', [])
        }
        
        serializer = self.get_serializer(data=diligence_data)
        if serializer.is_valid():
            diligence = serializer.save()
            
            # Créer notifications pour les agents assignés
            for agent in diligence.agents.all():
                DiligenceNotification.objects.create(
                    user=agent,
                    diligence=diligence,
                    type_notification='nouvelle_diligence',
                    message=f'Nouvelle diligence spontanée assignée: {diligence.objet}'
                )
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def request_validation(self, request, pk=None):
        """Demander la validation d'une diligence"""
        diligence = self.get_object()
        diligence.statut = 'demande_validation'
        diligence.save()
        
        # Notifier les administrateurs
        from django.contrib.auth import get_user_model
        User = get_user_model()
        admins = User.objects.filter(profile__role='ADMIN')
        
        for admin in admins:
            DiligenceNotification.objects.create(
                user=admin,
                diligence=diligence,
                type_notification='validation_requise',
                message=f'Validation requise pour la diligence: {diligence.reference_courrier}'
            )
        
        return Response({'message': 'Demande de validation envoyée'})

    @action(detail=True, methods=['post'])
    def validate_diligence(self, request, pk=None):
        """Valider une diligence (admin seulement)"""
        diligence = self.get_object()
        
        # Vérifier les permissions
        if not hasattr(request.user, 'profile') or request.user.profile.role != 'ADMIN':
            return Response(
                {'error': 'Seuls les administrateurs peuvent valider les diligences'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        diligence.statut = 'termine'
        diligence.validated_by = request.user
        diligence.validated_at = timezone.now()
        diligence.save()
        
        # Notifier les agents
        for agent in diligence.agents.all():
            DiligenceNotification.objects.create(
                user=agent,
                diligence=diligence,
                type_notification='document_valide',
                message=f'Diligence validée: {diligence.reference_courrier}'
            )
        
        return Response({'message': 'Diligence validée avec succès'})

    @action(detail=True, methods=['post'])
    def archive_diligence(self, request, pk=None):
        """Archiver une diligence"""
        diligence = self.get_object()
        
        if diligence.statut != 'termine':
            return Response(
                {'error': 'Seules les diligences terminées peuvent être archivées'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        diligence.statut = 'archivee'
        diligence.archived_by = request.user
        diligence.archived_at = timezone.now()
        diligence.save()
        
        # Notifier les agents
        for agent in diligence.agents.all():
            DiligenceNotification.objects.create(
                user=agent,
                diligence=diligence,
                type_notification='diligence_archivee',
                message=f'Diligence archivée: {diligence.reference_courrier}'
            )
        
        return Response({'message': 'Diligence archivée avec succès'})

    @action(detail=False, methods=['get'])
    def by_domain(self, request):
        """Récupérer les diligences par domaine pour archivage organisé"""
        domain = request.query_params.get('domain')
        if not domain:
            return Response(
                {'error': 'Paramètre domain requis'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        diligences = self.get_queryset().filter(domaine=domain, statut='archivee').order_by('-archived_at')
        serializer = self.get_serializer(diligences, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def deadline_reminders(self, request):
        """Obtenir les diligences nécessitant des rappels de délai"""
        today = timezone.now().date()
        
        # Diligences avec rappel 1 (7 jours avant échéance)
        rappel_1_date = today + timedelta(days=7)
        diligences_rappel_1 = self.get_queryset().filter(
            date_limite=rappel_1_date,
            statut__in=['en_attente', 'en_cours']
        )
        
        # Diligences avec rappel 2 (3 jours avant échéance)
        rappel_2_date = today + timedelta(days=3)
        diligences_rappel_2 = self.get_queryset().filter(
            date_limite=rappel_2_date,
            statut__in=['en_attente', 'en_cours']
        )
        
        # Créer les notifications de rappel
        for diligence in diligences_rappel_1:
            for agent in diligence.agents.all():
                DiligenceNotification.objects.get_or_create(
                    user=agent,
                    diligence=diligence,
                    type_notification='rappel_delai',
                    defaults={
                        'message': f'Rappel: Échéance dans 7 jours pour {diligence.reference_courrier}'
                    }
                )
        
        for diligence in diligences_rappel_2:
            for agent in diligence.agents.all():
                DiligenceNotification.objects.get_or_create(
                    user=agent,
                    diligence=diligence,
                    type_notification='rappel_delai',
                    defaults={
                        'message': f'URGENT: Échéance dans 3 jours pour {diligence.reference_courrier}'
                    }
                )
        
        return Response({
            'rappel_1_count': diligences_rappel_1.count(),
            'rappel_2_count': diligences_rappel_2.count(),
            'message': 'Rappels de délai traités'
        })
