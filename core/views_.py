import os
import json
from django.conf import settings
from django.http import HttpResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.models import User
from django.db.models import Q, Count, Prefetch
from django.shortcuts import get_object_or_404
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils import timezone
from datetime import datetime, timedelta
import mimetypes

class BinaryFileRenderer:
    media_type = '*/*'
    format = None
    charset = None
    render_style = 'binary'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        return data

from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import *
from .serializers import *

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

class UserProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        try:
            profile = user.profile
            data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': profile.role,
                'service': profile.service.id if profile.service else None,
                'direction': profile.direction.id if profile.direction else None,
                'notifications_count': user.notifications.filter(read=False).count()
            }
            return Response(data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

from rest_framework.exceptions import PermissionDenied

class UserRegistrationView(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

class AdminRegistrationView(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer

    def create(self, request, *args, **kwargs):
        # Forcer le rôle ADMIN
        data = request.data.copy()
        data['role'] = 'ADMIN'
        
        # Vérifier s'il existe déjà un administrateur
        admin_exists = User.objects.filter(profile__role__in=['ADMIN', 'superadmin']).exists()
        
        if admin_exists and (not request.user.is_authenticated or not request.user.profile.role in ['ADMIN', 'superadmin']):
            raise PermissionDenied("Seuls les administrateurs peuvent créer d'autres administrateurs")
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

from rest_framework.permissions import BasePermission

class IsAdminOrSecretary(BasePermission):
    def has_permission(self, request, view):
        return request.user.profile.role in ['ADMIN', 'superadmin', 'SECRETAIRE']

class DirectionViewSet(viewsets.ModelViewSet):
    queryset = Direction.objects.all().order_by('nom')
    serializer_class = DirectionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.profile.role in ['ADMIN', 'superadmin']:
            return Direction.objects.all()
        elif user.profile.direction:
            return Direction.objects.filter(id=user.profile.direction.id)
        return Direction.objects.none()

from rest_framework.pagination import PageNumberPagination

class DiligencePagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'per_page'
    max_page_size = 100

class DiligenceViewSet(viewsets.ModelViewSet):
    queryset = Diligence.objects.all().order_by('-created_at')
    serializer_class = DiligenceSerializer
    pagination_class = DiligencePagination
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()

        # Filtre par statut
        status = self.request.query_params.get('status', None)
        if status is not None:
            queryset = queryset.filter(status=status)

        # Filtre par service
        service = self.request.query_params.get('service', None)
        if service is not None:
            queryset = queryset.filter(service=service)

        # Filtre par direction
        direction = self.request.query_params.get('direction', None)
        if direction is not None:
            queryset = queryset.filter(service__direction=direction)

        # Recherche
        search = self.request.query_params.get('search', None)
        if search is not None:
            queryset = queryset.filter(
                Q(objet__icontains=search) |
                Q(reference__icontains=search) |
                Q(service__nom__icontains=search) |
                Q(agent__username__icontains=search)
            )

        # Filtre selon le rôle de l'utilisateur
        if user.profile.role == 'AGENT':
            queryset = queryset.filter(agent=user)
        elif user.profile.role == 'SUPERIEUR':
            queryset = queryset.filter(service__direction=user.profile.direction)
        elif user.profile.role == 'SECRETAIRE':
            queryset = queryset.filter(service=user.profile.service)

        return queryset

    @action(detail=False, methods=['get'])
    def to_validate(self, request):
        user = request.user
        if user.profile.role not in ['SUPERIEUR', 'ADMIN', 'superadmin']:
            return Response({"detail": "Non autorisé"}, status=status.HTTP_403_FORBIDDEN)

        queryset = self.get_queryset().filter(status='EN_ATTENTE')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def validate(self, request, pk=None):
        diligence = self.get_object()
        user = request.user

        if user.profile.role not in ['SUPERIEUR', 'ADMIN', 'superadmin']:
            return Response({"detail": "Non autorisé"}, status=status.HTTP_403_FORBIDDEN)

        diligence.status = 'VALIDEE'
        diligence.validated_at = timezone.now()
        diligence.validator = user
        diligence.save()

        # Créer une notification
        Notification.objects.create(
            user=diligence.agent,
            message=f"Votre diligence {diligence.reference} a été validée",
            diligence=diligence
        )

        return Response({"status": "validée"})

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        diligence = self.get_object()
        diligence.archived = True
        diligence.save()
        return Response({"status": "archivée"})

    @action(detail=True, methods=['post'])
    def unarchive(self, request, pk=None):
        diligence = self.get_object()
        diligence.archived = False
        diligence.save()
        return Response({"status": "désarchivée"})

class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

class ObservationViewSet(viewsets.ModelViewSet):
    queryset = Observation.objects.all()
    serializer_class = ObservationSerializer
    permission_classes = [permissions.IsAuthenticated]

class EvenementViewSet(viewsets.ModelViewSet):
    queryset = Evenement.objects.all()
    serializer_class = EvenementSerializer
    permission_classes = [permissions.IsAuthenticated]

class EtapeEvenementViewSet(viewsets.ModelViewSet):
    queryset = EtapeEvenement.objects.all()
    serializer_class = EtapeEvenementSerializer
    permission_classes = [permissions.IsAuthenticated]

class PresenceViewSet(viewsets.ModelViewSet):
    queryset = Presence.objects.all()
    serializer_class = PresenceSerializer
    permission_classes = [permissions.IsAuthenticated]

class PrestataireViewSet(viewsets.ModelViewSet):
    queryset = Prestataire.objects.all()
    serializer_class = PrestataireSerializer
    permission_classes = [permissions.IsAuthenticated]

class PrestataireEtapeViewSet(viewsets.ModelViewSet):
    queryset = PrestataireEtape.objects.all()
    serializer_class = PrestataireEtapeSerializer
    permission_classes = [permissions.IsAuthenticated]

class EvaluationViewSet(viewsets.ModelViewSet):
    queryset = Evaluation.objects.all()
    serializer_class = EvaluationSerializer
    permission_classes = [permissions.IsAuthenticated]

class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.all().order_by('nom')
    serializer_class = ServiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.profile.role in ['ADMIN', 'superadmin']:
            return Service.objects.all()
        elif user.profile.direction:
            return Service.objects.filter(direction=user.profile.direction)
        elif user.profile.service:
            return Service.objects.filter(id=user.profile.service.id)
        return Service.objects.none()

class DirectionViewSet(viewsets.ModelViewSet):
    queryset = Direction.objects.all()
    serializer_class = DirectionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.profile.role in ['ADMIN', 'superadmin']:
            return Direction.objects.all()
        elif user.profile.direction:
            return Direction.objects.filter(id=user.profile.direction.id)
        return Direction.objects.none()

class CourrierViewSet(viewsets.ModelViewSet):
    queryset = Courrier.objects.all()
    serializer_class = CourrierSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.profile.role in ['ADMIN', 'superadmin']:
            return Courrier.objects.all()
        return Courrier.objects.filter(diligence__agent=user)

import logging
logger = logging.getLogger(__name__)

class CourrierDownloadView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    renderer_classes = [BinaryFileRenderer]

    def options(self, request, id):
        response = HttpResponse()
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response

    def get(self, request, id):
        try:
            courrier = get_object_or_404(Courrier, id=id)
            
            # Vérifier les permissions
            user = request.user
            if not (user.profile.role in ['ADMIN', 'superadmin'] or courrier.diligence.agent == user):
                return Response(
                    {"detail": "Vous n'avez pas la permission de télécharger ce fichier"},
                    status=status.HTTP_403_FORBIDDEN
                )

            file_path = courrier.fichier.path
            if not os.path.exists(file_path):
                return Response(
                    {"detail": "Fichier non trouvé"},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Déterminer le type MIME
            content_type, _ = mimetypes.guess_type(file_path)
            if not content_type:
                content_type = 'application/octet-stream'

            # Ouvrir et retourner le fichier
            response = FileResponse(
                open(file_path, 'rb'),
                content_type=content_type,
                as_attachment=True,
                filename=os.path.basename(file_path)
            )

            return response

        except Exception as e:
            logger.error(f"Erreur lors du téléchargement du courrier {id}: {str(e)}")
            return Response(
                {"detail": "Erreur lors du téléchargement du fichier"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def options(self, request, id):
        response = HttpResponse()
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response

from .permissions import IsProfileAdmin

class UserManagementViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('username')
    permission_classes = [permissions.IsAuthenticated, IsProfileAdmin]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return UserRegistrationSerializer
        return UserSerializer

    def get_queryset(self):
        user = self.request.user
        if user.profile.role in ['ADMIN', 'superadmin']:
            return User.objects.all()
        return User.objects.none()

    def perform_create(self, serializer):
        if not self.request.user.profile.role in ['ADMIN', 'superadmin']:
            raise PermissionDenied("Seuls les administrateurs peuvent créer des utilisateurs")
        return super().perform_create(serializer)

    def perform_update(self, serializer):
        if not self.request.user.profile.role in ['ADMIN', 'superadmin']:
            raise PermissionDenied("Seuls les administrateurs peuvent modifier des utilisateurs")
        return super().perform_update(serializer)

    def perform_destroy(self, instance):
        if not self.request.user.profile.role in ['ADMIN', 'superadmin']:
            raise PermissionDenied("Seuls les administrateurs peuvent supprimer des utilisateurs")
        if instance == self.request.user:
            raise PermissionDenied("Vous ne pouvez pas supprimer votre propre compte")
        return super().perform_destroy(instance)

class AgentViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsProfileAdmin]

    def get_queryset(self):
        user = self.request.user
        if user.profile.role == 'SUPERIEUR':
            return User.objects.filter(
                profile__service__direction=user.profile.direction,
                profile__role='AGENT'
            )
        elif user.profile.role in ['ADMIN', 'superadmin']:
            return User.objects.filter(profile__role='AGENT')
        return User.objects.none()
