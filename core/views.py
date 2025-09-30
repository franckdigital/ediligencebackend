print("VIEWS.PY TOP LEVEL EXECUTED")
import os
print("VIEWS.PY CHARGÉ")
import json
import logging
from django.conf import settings
from django.http import HttpResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets, permissions, status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import TokenAuthentication
from django.contrib.auth.models import User
from django.db.models import Q, Count, Prefetch
from django.db import models
from django.shortcuts import get_object_or_404
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils import timezone
from datetime import datetime, timedelta, date
import mimetypes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from rest_framework.exceptions import PermissionDenied
from .pdf_utils import generate_conge_pdf, generate_absence_pdf, create_pdf_response
from rest_framework.permissions import BasePermission
from rest_framework.pagination import PageNumberPagination
from .models import Direction, Service, Diligence, Courrier, UserProfile, Bureau, Presence, ImputationAccess, CourrierAccess, CourrierImputation, ImputationFile, UserDiligenceComment, UserDiligenceInstruction, DemandeConge, DemandeAbsence
from .serializers import (
    CourrierSerializer, ServiceSerializer, DirectionSerializer, 
    DiligenceSerializer, UserSerializer, UserRegistrationSerializer, ImputationAccessSerializer,
    UserDiligenceCommentSerializer, UserDiligenceInstructionSerializer,
    ImputationFileSerializer, DemandeCongeSerializer, DemandeAbsenceSerializer,
    BureauSerializer, CourrierImputationSerializer
)
from .permissions import IsProfileAdmin
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404

logger = logging.getLogger(__name__)

import logging
logger = logging.getLogger(__name__)

# SetFingerprintView removed - using simple button presence now

class ImputationFileViewSet(viewsets.ModelViewSet):
    queryset = ImputationFile.objects.all()
    serializer_class = ImputationFileSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        queryset = ImputationFile.objects.all()
        diligence_id = self.request.query_params.get('diligence_id')
        if diligence_id:
            queryset = queryset.filter(diligence_id=diligence_id)
        return queryset
    
    def create(self, request, *args, **kwargs):
        print(f"[DEBUG] ImputationFile create - User: {request.user}, Data: {request.data}")
        try:
            response = super().create(request, *args, **kwargs)
            print(f"[DEBUG] ImputationFile created successfully: {response.data}")
            return response
        except Exception as e:
            print(f"[ERROR] ImputationFile creation failed: {str(e)}")
            raise

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        print('UserViewSet: requête reçue, user =', self.request.user, 'is_authenticated =', self.request.user.is_authenticated)
        qs = User.objects.select_related(
            'profile',
            'profile__service',
            'profile__service__direction'
        )
        roles = self.request.query_params.get('roles')
        if roles:
            role_list = [r.strip() for r in roles.split(',') if r.strip()]
            qs = qs.filter(profile__role__in=role_list)
        return qs.order_by('-date_joined')

    def get_serializer_class(self):
        print(f"[DEBUG] UserViewSet using serializer: {UserSerializer}")
        return UserSerializer
    
    serializer_class = UserSerializer
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        print("\nDébut de la mise à jour de l'utilisateur")
        print("Données reçues:", request.data)
        serializer = self.get_serializer(instance, data=request.data, partial=kwargs.get('partial', False))
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        print("Données renvoyées:", serializer.data)
        return Response(serializer.data)
    
    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

class LoginView(APIView):
    authentication_classes = []  # Désactive toute auth préalable
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        print("LOGIN VIEW CALLED", request.data)
        # Fingerprint authentication removed - using username/password only
        username_or_email = request.data.get('username')
        password = request.data.get('password')
        print(f"Tentative de login pour : {username_or_email}")
        from django.contrib.auth import get_user_model, authenticate
        User = get_user_model()
        user = authenticate(username=username_or_email, password=password)
        print("AUTHENTICATE 1:", user)
        if not user:
            # Si username_or_email est un email, essayer de trouver le user correspondant
            try:
                user_obj = User.objects.get(email=username_or_email)
                print("USER OBJ (par email):", user_obj)
                user = authenticate(username=user_obj.username, password=password)
                print("AUTHENTICATE 2:", user)
            except User.DoesNotExist:
                print("NO USER OBJ pour cet email")
                user = None
        if not user:
            print("ECHEC AUTH: credentials invalid")
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        token, _ = Token.objects.get_or_create(user=user)
        try:
            profile = user.profile
        except Exception:
            return Response({'error': 'Profil utilisateur manquant'}, status=500)
        return Response({
            'token': token.key,
            'role': profile.role,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': profile.role,
                'role_display': self.get_role_display(profile.role),
                'service': profile.service.id if profile.service else None,
                'direction': profile.direction.id if profile.direction else None,
                'notifications_count': user.notifications.filter(read=False).count() if hasattr(user, 'notifications') else 0
            }
        })

    def get_role_display(self, role):
        """Retourne une version formatée du rôle pour l'affichage"""
        role_mapping = {
            'ADMIN': 'Administrateur',
            'superadmin': 'Super Administrateur',
            'USER': 'Utilisateur',
            'MANAGER': 'Manager'
        }
        return role_mapping.get(role, role)

import logging

class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        logger = logging.getLogger(__name__)
        logger.info("[ChangePassword] Reçu POST /auth/change-password/ pour user=%s", request.user)
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        logger.info("[ChangePassword] Payload: old_password=%s, new_password_length=%s", bool(old_password), len(new_password) if new_password else None)
        if not old_password or not new_password:
            logger.warning("[ChangePassword] Champs manquants")
            return Response({'detail': "Champs obligatoires manquants."}, status=status.HTTP_400_BAD_REQUEST)
        if not user.check_password(old_password):
            logger.warning("[ChangePassword] Ancien mot de passe incorrect pour user=%s", user)
            return Response({'detail': "Ancien mot de passe incorrect."}, status=status.HTTP_400_BAD_REQUEST)
        from django.contrib.auth.password_validation import validate_password
        try:
            validate_password(new_password, user)
        except Exception as e:
            logger.warning("[ChangePassword] Validation password échouée: %s", str(e))
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(new_password)
        user.save()
        logger.info("[ChangePassword] Mot de passe changé avec succès pour user=%s", user)
        return Response({'detail': "Mot de passe changé avec succès."})


class UserProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]

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
                'role_display': self.get_role_display(profile.role),
                'service': profile.service.id if profile.service else None,
                'direction': profile.direction.id if profile.direction else None,
                'notifications_count': 0  # Par défaut 0 notifications
            }
            # Vérifier si les notifications sont configurées
            if hasattr(user, 'notifications'):
                data['notifications_count'] = user.notifications.filter(read=False).count()
            return Response(data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        from .serializers import UserSerializer
        user = request.user
        print("PATCH DEBUG: request.data =", request.data)
        serializer = UserSerializer(user, data=request.data, partial=True, context={'request': request})
        print("PATCH DEBUG: serializer initial_data =", serializer.initial_data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        print("PATCH DEBUG: serializer.errors =", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_role_display(self, role):
        """Retourne une version formatée du rôle pour l'affichage"""
        role_mapping = {
            'ADMIN': 'Administrateur',
            'superadmin': 'Super Administrateur',
            'USER': 'Utilisateur',
            'MANAGER': 'Manager'
        }
        return role_mapping.get(role, role)

class AdminRegistrationView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []  # Désactiver l'authentification pour cette vue

    def post(self, request, *args, **kwargs):
        try:
            logger.info("Début de la création d'un admin")
            
            # Vérifier s'il existe déjà un administrateur
            admin_exists = User.objects.filter(profile__role__in=['ADMIN', 'superadmin']).exists()
            logger.info(f"Admin existe déjà ? {admin_exists}")

            # Si un admin existe déjà
            if admin_exists:
                logger.info("Vérification des permissions pour la création d'un nouvel admin")
                if not request.user.is_authenticated:
                    logger.warning("Tentative de création d'admin sans authentification")
                    return Response(
                        {"detail": "Vous devez être connecté pour créer un compte administrateur"},
                        status=status.HTTP_403_FORBIDDEN
                    )
                if not request.user.profile.role in ['ADMIN', 'superadmin']:
                    logger.warning(f"Tentative de création d'admin par un utilisateur non-admin: {request.user.username}")
                    return Response(
                        {"detail": "Seuls les administrateurs peuvent créer d'autres administrateurs"},
                        status=status.HTTP_403_FORBIDDEN
                    )

            # Valider les données
            data = request.data
            logger.info(f"Données reçues: {data}")
            
            required_fields = ('username', 'email', 'password', 'password2', 'first_name', 'last_name')
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                logger.warning(f"Champs manquants: {missing_fields}")
                return Response(
                    {"detail": f"Les champs suivants sont requis: {', '.join(missing_fields)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if data['password'] != data['password2']:
                logger.warning("Les mots de passe ne correspondent pas")
                return Response(
                    {"detail": "Les mots de passe ne correspondent pas"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Log la tentative de création d'utilisateur
            logger.info(f"[AdminRegistrationView] Tentative de création: username={data['username']}, email={data['email']}")
            # Créer l'utilisateur
            logger.info(f"Création de l'utilisateur {data['username']}")
            user = User.objects.create_user(
                username=data['username'],
                email=data['email'],
                password=data['password'],
                first_name=data['first_name'],
                last_name=data['last_name']
            )

            # Créer le profil avec le rôle admin
            logger.info(f"Création du profil admin pour {user.username}")
            # On force le rôle ADMIN même si le profil existe déjà
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.role = 'ADMIN'
            profile.save()

            logger.info(f"Admin créé avec succès: {user.username}")
            return Response({
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': 'ADMIN'
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Erreur lors de la création de l'admin: {str(e)}")
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class AgentRegistrationView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        import logging
        import traceback
        logger = logging.getLogger(__name__)
        try:
            serializer = UserRegistrationSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.save()
                return Response({
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'role': user.profile.role
                }, status=status.HTTP_201_CREATED)
            logger.error(f'[AgentRegistrationView] Registration validation errors: {serializer.errors}')
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f'[AgentRegistrationView] Unhandled exception during registration: {str(e)}')
            logger.error(traceback.format_exc())
            return Response({'detail': 'Internal server error. Please contact support.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DirectionViewSet(viewsets.ModelViewSet):
    queryset = Direction.objects.all()
    serializer_class = DirectionSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        queryset = Direction.objects.prefetch_related('services').all().order_by('-created_at')
        for direction in queryset:
            print(f'Direction {direction.nom} services:', [s.nom for s in direction.services.all()])
        return queryset

    def perform_create(self, serializer):
        serializer.save()

    def perform_update(self, serializer):
        instance = serializer.save()
        instance.updated_at = timezone.now()
        instance.save()

    def perform_destroy(self, instance):
        # Vérifier si la direction a des services associés
        if instance.services.exists():
            raise serializers.ValidationError("Cette direction contient des services et ne peut pas être supprimée.")
        instance.delete()

class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.select_related('direction').all()
    serializer_class = ServiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        return Service.objects.select_related('direction').all().order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save()

    def perform_update(self, serializer):
        instance = serializer.save()
        instance.updated_at = timezone.now()
        instance.save()

from .serializers import DirectionSerializer, ServiceSerializer, CourrierSerializer

class DiligenceViewSet(viewsets.ModelViewSet):
    queryset = Diligence.objects.all()
    serializer_class = DiligenceSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def get_queryset(self):
        user = self.request.user
        profile = getattr(user, 'profile', None)
        base_qs = Diligence.objects.select_related(
            'courrier',
            'courrier__service',
            'courrier__service__direction',
            'direction'
        ).prefetch_related(
            Prefetch('agents', queryset=User.objects.select_related('profile', 'profile__service')),
            'services_concernes',
            'services_concernes__direction'
        ).all().order_by('-created_at')

        if not profile:
            print(f"[ERROR] No profile found for user {user.username} (ID: {user.id})")
            return Diligence.objects.none()

        role = profile.role
        print(f"[DEBUG] DiligenceViewSet get_queryset - User: {user.username} (ID: {user.id}), Role: {role}")

        # Filtrage par statut si présent dans la requête
        statut = self.request.query_params.get('statut')
        if statut:
            base_qs = base_qs.filter(statut=statut)

        # Build queryset for diligences accessible by ImputationAccess
        from core.models import ImputationAccess
        imputation_access_qs = base_qs.filter(imputation_access__user=user)
        print(f"[DEBUG] ImputationAccess diligences count: {imputation_access_qs.count()}")

        # Filtrage par rôle
        # 1. Diligences où l'utilisateur est dans les agents assignés
        assigned_qs = base_qs.filter(agents=user)
        print(f"[DEBUG] Assigned diligences count: {assigned_qs.count()}")
        
        if role == 'ADMIN':
            # ADMIN peut voir toutes les diligences du système
            qs = base_qs
            print(f"[DEBUG] ADMIN - Using all diligences")
            # Combine with ImputationAccess-based queryset (union, remove duplicates)
            final_qs = (qs | imputation_access_qs).distinct()
        elif role == 'DIRECTEUR':
            # DIRECTEUR peut voir toutes les diligences de sa direction ET des services rattachés
            user_direction = profile.service.direction if profile.service else None
            if user_direction:
                # Diligences directement liées à la direction
                direction_qs = base_qs.filter(
                    models.Q(direction=user_direction) |
                    models.Q(services_concernes__direction=user_direction) |
                    models.Q(courrier__service__direction=user_direction)
                ).distinct()
                
                # Diligences des agents de tous les services de cette direction
                from core.models import Service
                direction_services = Service.objects.filter(direction=user_direction)
                direction_agents = User.objects.filter(profile__service__in=direction_services)
                agents_direction_qs = base_qs.filter(agents__in=direction_agents).distinct()
                
                print(f"[DEBUG] DIRECTEUR - Direction diligences count: {direction_qs.count()}")
                print(f"[DEBUG] DIRECTEUR - Direction agents diligences count: {agents_direction_qs.count()}")
                
                # Combiner les querysets sans utiliser l'union pour éviter l'erreur "unique query"
                diligence_ids = set()
                diligence_ids.update(assigned_qs.values_list('id', flat=True))
                diligence_ids.update(direction_qs.values_list('id', flat=True))
                diligence_ids.update(agents_direction_qs.values_list('id', flat=True))
                diligence_ids.update(imputation_access_qs.values_list('id', flat=True))
                
                final_qs = base_qs.filter(id__in=diligence_ids)
            else:
                final_qs = (assigned_qs | imputation_access_qs).distinct()
        elif role == 'SUPERIEUR':
            # SUPERIEUR peut voir ses propres diligences ET celles de ses agents
            user_service = profile.service if profile.service else None
            if user_service:
                # Diligences du service du supérieur
                service_qs = base_qs.filter(
                    models.Q(services_concernes=user_service) |
                    models.Q(courrier__service=user_service)
                ).distinct()
                
                # Diligences des agents du même service
                service_agents = User.objects.filter(profile__service=user_service)
                agents_qs = base_qs.filter(agents__in=service_agents).distinct()
                
                print(f"[DEBUG] SUPERIEUR - Service diligences count: {service_qs.count()}")
                print(f"[DEBUG] SUPERIEUR - Agents diligences count: {agents_qs.count()}")
                
                # Combiner les querysets sans utiliser l'union pour éviter l'erreur "unique query"
                diligence_ids = set()
                diligence_ids.update(assigned_qs.values_list('id', flat=True))
                diligence_ids.update(service_qs.values_list('id', flat=True))
                diligence_ids.update(agents_qs.values_list('id', flat=True))
                diligence_ids.update(imputation_access_qs.values_list('id', flat=True))
                
                final_qs = base_qs.filter(id__in=diligence_ids)
            else:
                final_qs = (assigned_qs | imputation_access_qs).distinct()
        else:
            # Autres rôles (SECRETAIRE, AGENT) ne voient que leurs diligences assignées
            final_qs = (assigned_qs | imputation_access_qs).distinct()
            print(f"[DEBUG] {role} - Using assigned + imputation diligences")

        print(f"[DEBUG] Final queryset count: {final_qs.count()}")
        
        return final_qs

        # Note: If you want to be more restrictive and only add ImputationAccess for non-admins, adjust logic above.


    def create(self, request, *args, **kwargs):
        # Vérifier les permissions de création
        user = request.user
        profile = getattr(user, 'profile', None)
        
        if not profile:
            return Response({'error': 'Profil utilisateur non trouvé'}, status=status.HTTP_403_FORBIDDEN)
        
        role = profile.role
        allowed_roles = ['ADMIN', 'DIRECTEUR', 'SUPERIEUR', 'SECRETAIRE']
        
        if role not in allowed_roles:
            return Response({
                'error': f'Vous n\'avez pas les permissions pour créer une diligence. Rôles autorisés: {", ".join(allowed_roles)}'
            }, status=status.HTTP_403_FORBIDDEN)
        
        print(f"\nCréation diligence autorisée pour {user.username} (rôle: {role})")
        print("Données reçues pour création diligence:", request.data)
        print("Type de request.data:", type(request.data))
        
        # Si un courrier est sélectionné, pré-remplir la direction et le service
        courrier_id = request.data.get('courrier_id')
        print("Courrier ID reçu:", courrier_id)
        
        if courrier_id:
            try:
                courrier = Courrier.objects.select_related('service__direction').get(id=courrier_id)
                print("Courrier trouvé:", {
                    'id': courrier.id,
                    'reference': courrier.reference,
                    'service_id': courrier.service.id if courrier.service else None,
                    'service_nom': courrier.service.nom if courrier.service else None,
                    'direction_id': courrier.service.direction.id if courrier.service and courrier.service.direction else None,
                    'direction_nom': courrier.service.direction.nom if courrier.service and courrier.service.direction else None
                })
                
                if courrier.service and courrier.service.direction:
                    print(f"Courrier trouvé avec service {courrier.service.id} et direction {courrier.service.direction.id}")
                    
                    # Vérifier si request.data est mutable
                    print("request.data est mutable:", getattr(request.data, '_mutable', True))
                    
                    # Convertir en MutableDict si nécessaire
                    if hasattr(request.data, '_mutable'):
                        request.data._mutable = True
                        print("request.data est maintenant mutable")

                    if not request.data.get('direction'):
                        request.data['direction'] = courrier.service.direction.id
                        print(f"Direction définie à: {courrier.service.direction.id}")

                    if not request.data.get('services_concernes_ids'):
                        request.data['services_concernes_ids'] = [courrier.service.id]
                        print(f"Services concernés définis à: {[courrier.service.id]}")

                    # Remettre à non mutable si nécessaire
                    if hasattr(request.data, '_mutable'):
                        request.data._mutable = False
                        print("request.data est maintenant non mutable")
                else:
                    print("Le courrier n'a pas de service ou de direction associé")
                    if not courrier.service:
                        print("Le courrier n'a pas de service")
                    elif not courrier.service.direction:
                        print("Le service du courrier n'a pas de direction")
            except Courrier.DoesNotExist:
                print(f"Courrier {courrier_id} non trouvé")
            except Exception as e:
                print(f"Erreur lors de la récupération du courrier: {str(e)}")
                import traceback
                print("Traceback:", traceback.format_exc())

        print("\nDonnées finales avant création:", {'direction': request.data.get('direction')})
        
        # Call parent create method
        response = super().create(request, *args, **kwargs)
        
        # Créer des notifications pour les agents assignés
        if response.status_code == 201:
            diligence_id = response.data.get('id')
            if diligence_id:
                try:
                    from .models import DiligenceNotification
                    diligence = Diligence.objects.get(id=diligence_id)
                    
                    # Créer une notification pour chaque agent assigné
                    for agent in diligence.agents.all():
                        DiligenceNotification.objects.create(
                            user=agent,
                            diligence=diligence,
                            type_notification='nouvelle_diligence',
                            message=f'Nouvelle diligence assignée: {diligence.reference_courrier}'
                        )
                        print(f"Notification créée pour {agent.username} - Diligence {diligence.reference_courrier}")
                except Exception as e:
                    print(f"Erreur lors de la création des notifications: {e}")
        
        return response



class CourrierViewSet(viewsets.ModelViewSet):
    queryset = Courrier.objects.all()
    serializer_class = CourrierSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def get_queryset(self):
        user = self.request.user
        queryset = Courrier.objects.select_related(
            'service',
            'service__direction'
        ).all()
        
        # Filtrage selon le type de courrier et les permissions
        if hasattr(user, 'profile'):
            # Les ADMIN peuvent voir tous les courriers
            if user.profile.role in ['ADMIN']:
                return queryset.order_by('-created_at')
            
            # Pour les courriers confidentiels, vérifier les permissions d'accès ET les imputations
            accessible_confidential_ids = CourrierAccess.objects.filter(
                user=user
            ).values_list('courrier_id', flat=True)
            
            # Ajouter les courriers confidentiels avec imputation
            imputation_confidential_ids = CourrierImputation.objects.filter(
                user=user
            ).values_list('courrier_id', flat=True)
            
            # Combiner les deux listes d'IDs
            all_accessible_ids = list(accessible_confidential_ids) + list(imputation_confidential_ids)
            
            # Filtrer : courriers ordinaires + courriers confidentiels avec accès ou imputation
            queryset = queryset.filter(
                models.Q(type_courrier='ordinaire') |
                models.Q(type_courrier='confidentiel', id__in=all_accessible_ids)
            )
        else:
            # Si pas de profil, seulement les courriers ordinaires
            queryset = queryset.filter(type_courrier='ordinaire')
            
        return queryset.order_by('-created_at')

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        
        # Ajout des informations détaillées sur le service et la direction
        if instance.service:
            data['service'] = {
                'id': instance.service.id,
                'nom': instance.service.nom,
                'direction': {
                    'id': instance.service.direction.id,
                    'nom': instance.service.direction.nom
                } if instance.service.direction else None
            }
        
        return Response(data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def create_diligence(self, request, pk=None):
        """Créer une diligence à partir d'un courrier"""
        courrier = self.get_object()
        
        # Données pour la nouvelle diligence
        diligence_data = {
            'reference_courrier': courrier.reference,
            'courrier': courrier.id,
            'categorie': request.data.get('categorie', 'NORMAL'),
            'expediteur': courrier.expediteur,
            'objet': courrier.objet,
            'date_reception': courrier.date_reception,
            'instructions': request.data.get('instructions', ''),
            'date_limite': request.data.get('date_limite'),
            'agents': request.data.get('agents', []),
            'services_concernes': request.data.get('services_concernes', []),
            'direction': request.data.get('direction')
        }
        
        from .serializers import DiligenceSerializer
        serializer = DiligenceSerializer(data=diligence_data, context={'request': request})
        
        if serializer.is_valid():
            diligence = serializer.save()
            return Response({
                'message': 'Diligence créée avec succès',
                'diligence_id': diligence.id
            }, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def imputer_courrier(self, request, pk=None):
        """Imputer un courrier confidentiel à un utilisateur - seuls ADMIN et DIRECTEUR"""
        user = request.user
        
        # Vérifier les permissions
        if not (hasattr(user, 'profile') and user.profile.role in ['ADMIN', 'DIRECTEUR']):
            return Response(
                {'error': 'Seuls les administrateurs et directeurs peuvent imputer des courriers'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        courrier = self.get_object()
        
        # Vérifier que c'est un courrier confidentiel
        if courrier.type_courrier != 'confidentiel':
            return Response(
                {'error': 'Seuls les courriers confidentiels peuvent être imputés'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user_id = request.data.get('user_id')
        access_type = request.data.get('access_type', 'view')
        
        if not user_id:
            return Response(
                {'error': 'user_id est requis'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            target_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'Utilisateur non trouvé'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Créer ou mettre à jour l'imputation
        imputation, created = CourrierImputation.objects.get_or_create(
            courrier=courrier,
            user=target_user,
            access_type=access_type,
            defaults={'granted_by': user}
        )
        
        if not created:
            imputation.granted_by = user
            imputation.save()
        
        return Response({
            'message': f'Courrier imputé avec succès à {target_user.get_full_name() or target_user.username}',
            'imputation_id': imputation.id
        }, status=status.HTTP_201_CREATED)

    def create(self, request, *args, **kwargs):
        print('\nRequest data:', dict(request.data))
        print('Files:', dict(request.FILES))
        try:
            serializer = self.get_serializer(data=request.data)
            if not serializer.is_valid():
                print('\nValidation errors:', serializer.errors)
                return Response({
                    'error': 'Validation failed',
                    'details': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except serializers.ValidationError as e:
            print('\nValidation error:', e.detail)
            return Response({
                'error': 'Validation error',
                'details': e.detail
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print('\nUnexpected error:', str(e))
            print('Type:', type(e))
            return Response({
                'error': 'Une erreur inattendue est survenue',
                'details': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        print('\nAPI Response data:')
        for item in response.data:
            print(f'\nCourrier {item["reference"]}:')
            print('- Full data:', item)
            if 'service' in item:
                print('- Service:', item['service'])
        return response

    def get_serializer_context(self):
        context = super().get_serializer_context()
        print('Request data:', self.request.data)
        return context

    def perform_create(self, serializer):
        serializer.save()

    def perform_update(self, serializer):
        instance = serializer.save()
        instance.updated_at = timezone.now()
        instance.save()

    @action(detail=True, methods=['get'])
    def services(self, request, pk=None):
        direction = self.get_object()
        services = direction.services.all()
        serializer = ServiceSerializer(services, many=True)
        return Response(serializer.data)

from django.http import FileResponse, Http404
from rest_framework.views import APIView

class DiligenceDownloadFichierView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    def get(self, request, pk):
        from .models import Diligence, ImputationAccess
        try:
            diligence = Diligence.objects.get(pk=pk)
            # Vérification d'accès ImputationAccess
            if not ImputationAccess.objects.filter(diligence=diligence, user=request.user).exists():
                return Response({'detail': 'Accès refusé : vous n\'avez pas l\'autorisation pour ce document.'}, status=403)
            if not diligence.fichier_joint:
                raise Http404("Aucun fichier joint")
            response = FileResponse(diligence.fichier_joint.open('rb'), as_attachment=True, filename=diligence.fichier_joint.name.split('/')[-1])
            return response
        except Diligence.DoesNotExist:
            raise Http404("Diligence non trouvée")

from rest_framework import viewsets, permissions
from .models import ImputationAccess
from .serializers import ImputationAccessSerializer

class ImputationAccessViewSet(viewsets.ModelViewSet):
    queryset = ImputationAccess.objects.all()
    serializer_class = ImputationAccessSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    def get_queryset(self):
        queryset = ImputationAccess.objects.all()
        user_id = self.request.query_params.get('user', None)
        diligence_id = self.request.query_params.get('diligence', None)
        
        if user_id is not None:
            queryset = queryset.filter(user=user_id)
        if diligence_id is not None:
            queryset = queryset.filter(diligence=diligence_id)
            
        return queryset
    
    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        
        # Créer une notification pour l'utilisateur imputé
        if response.status_code == 201:
            try:
                from .models import DiligenceNotification
                imputation_access = ImputationAccess.objects.get(id=response.data['id'])
                
                DiligenceNotification.objects.create(
                    user=imputation_access.user,
                    diligence=imputation_access.diligence,
                    type_notification='nouvelle_diligence',
                    message=f'Vous avez été imputé sur la diligence: {imputation_access.diligence.reference_courrier}'
                )
                print(f"Notification d'imputation créée pour {imputation_access.user.username}")
            except Exception as e:
                print(f"Erreur lors de la création de la notification d'imputation: {e}")
        
        return response

class BureauViewSet(viewsets.ModelViewSet):
    queryset = Bureau.objects.all()
    serializer_class = BureauSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    @action(detail=True, methods=['get'])
    def notifications(self, request, pk=None):
        bureau = self.get_object()
        notifications = Notification.objects.filter(bureau=bureau)
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data)

class CustomTokenObtainPairView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request, *args, **kwargs):
        print("CUSTOM JWT VIEW: appelée !")
        print("CUSTOM JWT VIEW: avant instanciation serializer")
        print("MyTokenObtainPairSerializer =", MyTokenObtainPairSerializer, "from", MyTokenObtainPairSerializer.__module__)
        serializer = MyTokenObtainPairSerializer(data=request.data)
        print("CUSTOM JWT VIEW: après instanciation serializer")
        print("CUSTOM JWT VIEW: juste avant serializer.is_valid()")
        print("CUSTOM JWT VIEW: request.data =", request.data)
        try:
            is_valid = serializer.is_valid()
            print("CUSTOM JWT VIEW: juste après serializer.is_valid(), résultat:", is_valid)
        except Exception as e:
            print("CUSTOM JWT VIEW: EXCEPTION lors de serializer.is_valid():", repr(e))
            import traceback; traceback.print_exc()
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        if is_valid:
            print("CUSTOM JWT VIEW: serializer OK")
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        else:
            print("CUSTOM JWT VIEW: serializer NON valide")
            print("CUSTOM JWT VIEW: erreurs serializer:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)


    def get_queryset(self):
        queryset = super().get_queryset()
        diligence_id = self.request.query_params.get('diligence')
        user_id = self.request.query_params.get('user')
        if diligence_id:
            queryset = queryset.filter(diligence_id=diligence_id)
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        return queryset

    def perform_create(self, serializer):
        # Optionnel : associe l'utilisateur créateur si utile
        serializer.save()

# --- Presence CRUD API ---

from rest_framework.permissions import IsAdminUser

class ListUsersView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        users = User.objects.select_related('profile', 'profile__service', 'profile__service__direction').all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

class RetrieveUserView(APIView):
    permission_classes = [IsAdminUser]
    authentication_classes = [JWTAuthentication]

    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_active': user.is_active,
                'date_joined': user.date_joined,
            }
            return Response(data)
        except User.DoesNotExist:
            return Response({'error': 'Utilisateur non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

class DeleteUserView(APIView):
    permission_classes = [IsAdminUser]
    authentication_classes = [JWTAuthentication]

    def delete(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            user.delete()
            return Response({'detail': 'Utilisateur supprimé.'}, status=status.HTTP_204_NO_CONTENT)
        except User.DoesNotExist:
            return Response({'error': 'Utilisateur non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

class MaPresenceDuJourView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        user = request.user
        try:
            agent = Agent.objects.get(user=user)
        except Agent.DoesNotExist:
            return Response(None, status=status.HTTP_404_NOT_FOUND)
        
        today = date.today()
        
        # Chercher la présence du jour
        try:
            presence = Presence.objects.get(agent=agent, date_presence=today)
            serializer = PresenceSerializer(presence)
            return Response(serializer.data)
        except Presence.DoesNotExist:
            # Aucune présence trouvée pour aujourd'hui
            return Response(None, status=status.HTTP_404_NOT_FOUND)

# Imports déjà présents en haut du fichier - suppression des doublons

# PresenceFingerprintView removed - using simple button presence now

class SimplePresenceView(APIView):
    """API simplifiée pour pointage par bouton mobile"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, TokenAuthentication]

    def post(self, request):
        import logging
        from datetime import date, datetime
        from .models import Agent, Presence
        
        logger = logging.getLogger(__name__)
        user = request.user
        action = request.data.get('action')  # 'arrivee' ou 'depart'
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        
        logger.info(f'[SimplePresenceView] User: {user}, Action: {action}')
        
        if not action or action not in ['arrivee', 'depart']:
            return Response({'error': 'Action requise: arrivee ou depart'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not latitude or not longitude:
            return Response({'error': 'Position GPS requise'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Récupérer ou créer l'agent automatiquement
            agent, created = Agent.objects.get_or_create(
                user=user,
                defaults={
                    'nom': user.last_name or 'Nom',
                    'prenom': user.first_name or 'Prénom',
                    'matricule': f'A{user.id:04d}',
                    'poste': getattr(user.profile, 'role', 'AGENT') if hasattr(user, 'profile') else 'AGENT'
                }
            )
            
            if created:
                logger.info(f'[SimplePresenceView] Agent créé automatiquement pour {user.username}')
            
            today = date.today()
            current_time = datetime.now().time()
            
            # Récupérer ou créer la présence du jour
            presence, created = Presence.objects.get_or_create(
                agent=agent,
                date_presence=today,
                defaults={
                    'statut': 'présent',
                    'latitude': latitude,
                    'longitude': longitude,
                    'localisation_valide': True,
                }
            )
            
            if action == 'arrivee':
                if presence.heure_arrivee:
                    return Response({'error': 'Arrivée déjà enregistrée aujourd\'hui'}, status=status.HTTP_400_BAD_REQUEST)
                presence.heure_arrivee = current_time
                message = 'Arrivée enregistrée avec succès'
            
            elif action == 'depart':
                if not presence.heure_arrivee:
                    return Response({'error': 'Vous devez d\'abord pointer votre arrivée'}, status=status.HTTP_400_BAD_REQUEST)
                if presence.heure_depart:
                    return Response({'error': 'Départ déjà enregistré aujourd\'hui'}, status=status.HTTP_400_BAD_REQUEST)
                presence.heure_depart = current_time
                message = 'Départ enregistré avec succès'
            
            presence.save()
            
            return Response({
                'success': True,
                'message': message,
                'presence': {
                    'date': presence.date_presence,
                    'heure_arrivee': presence.heure_arrivee,
                    'heure_depart': presence.heure_depart,
                    'statut': presence.statut
                }
            }, status=status.HTTP_200_OK)
            
        except Agent.DoesNotExist:
            return Response({'error': 'Profil agent non trouvé'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f'[SimplePresenceView] Erreur: {str(e)}')
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class PresenceViewSet(viewsets.ModelViewSet):
    queryset = Presence.objects.all()
    serializer_class = PresenceSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def perform_create(self, serializer):
        import logging
        logger = logging.getLogger(__name__)
        from rest_framework.exceptions import ValidationError
        from math import radians, cos, sin, asin, sqrt
        from .models import Agent
        logger.warning('[PresenceViewSet] Données reçues: %s', self.request.data)
        user = self.request.user
        statut = 'présent'
        user_id = self.request.data.get('user_id')
        if user_id:
            try:
                agent_user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                agent_user = self.request.user
        else:
            agent_user = self.request.user

        # Récupérer le profil Agent
        try:
            agent_obj = Agent.objects.get(user=agent_user)
        except Agent.DoesNotExist:
            logger.error('[PresenceViewSet] Aucun profil Agent associé à cet utilisateur.')
            raise ValidationError('Aucun profil Agent associé à cet utilisateur.')

        latitude = self.request.data.get('latitude')
        longitude = self.request.data.get('longitude')
        commentaire = self.request.data.get('commentaire')
        device_fingerprint = self.request.data.get('device_fingerprint')

        localisation_valide = False
        commentaire_final = commentaire or ''

        # Validation GPS si config présente
        if agent_obj.latitude_centre and agent_obj.longitude_centre and agent_obj.rayon_metres:
            try:
                lat1 = float(latitude)
                lon1 = float(longitude)
                lat2 = float(agent_obj.latitude_centre)
                lon2 = float(agent_obj.longitude_centre)
                rayon = 50.0  # Rayon fixe de 50 mètres

                # Haversine
                def haversine(lat1, lon1, lat2, lon2):
                    R = 6371000  # m
                    phi1 = radians(lat1)
                    phi2 = radians(lat2)
                    dphi = radians(lat2 - lat1)
                    dlambda = radians(lon2 - lon1)
                    a = sin(dphi/2)**2 + cos(phi1)*cos(phi2)*sin(dlambda/2)**2
                    c = 2*asin(sqrt(a))
                    return R * c

                distance = haversine(lat1, lon1, lat2, lon2)
                if distance > rayon:
                    logger.warning('[PresenceViewSet] Hors zone autorisée: %.1f m > %.1f m', distance, rayon)
                    raise ValidationError({'error': f'Vous êtes hors de la zone autorisée pour l’enregistrement de présence ({distance:.1f} m > {rayon:.1f} m). Veuillez vous rapprocher de votre bureau.'})
                logger.warning('[PresenceViewSet] Distance calculée: %s m', distance)
                if distance > rayon:
                    logger.warning('[PresenceViewSet] Hors zone autorisée: %.1f m > %.1f m', distance, rayon)
                    raise ValidationError(f"Vous êtes hors de la zone autorisée ({distance:.1f} m > {rayon:.1f} m)")
                localisation_valide = True
            except Exception as e:
                logger.error('[PresenceViewSet] Erreur lors de la validation GPS: %s', str(e))
                raise ValidationError(f"Erreur lors de la validation GPS : {str(e)}")
        else:
            commentaire_final += " [Avertissement : aucune configuration GPS de zone autorisée sur votre profil Agent.]"

        # Vérification de l'empreinte du téléphone
        logger.info('[PresenceViewSet] Device fingerprint reçu: %s', device_fingerprint)
        if device_fingerprint:
            from .models import DeviceRegistration
            
            logger.info('[PresenceViewSet] Vérification device fingerprint: %s pour utilisateur: %s', device_fingerprint[:8], agent_user.username)
            
            # Vérifier si cet appareil est déjà utilisé par un autre utilisateur
            existing_device = DeviceRegistration.objects.filter(
                device_fingerprint=device_fingerprint,
                is_active=True
            ).exclude(user=agent_user).first()
            
            if existing_device:
                logger.warning('[PresenceViewSet] 🚫 RESTRICTION ACTIVÉE - Appareil %s déjà utilisé par %s, refus pour %s', 
                             device_fingerprint[:8], existing_device.user.username, agent_user.username)
                raise ValidationError({
                    'error': f'Cet appareil est déjà enregistré pour {existing_device.user.username}. Chaque téléphone ne peut être utilisé que par un seul agent.'
                })
            
            # Enregistrer ou mettre à jour l'appareil pour cet utilisateur
            device_reg, created = DeviceRegistration.objects.get_or_create(
                user=agent_user,
                device_fingerprint=device_fingerprint,
                defaults={
                    'device_name': f'Mobile {Platform.OS}' if 'Platform' in globals() else 'Mobile',
                    'is_active': True
                }
            )
            
            if not created:
                # Mettre à jour la date de dernière utilisation
                device_reg.last_used = timezone.now()
                device_reg.save()
                logger.info('[PresenceViewSet] ✅ Appareil existant mis à jour: %s pour %s', device_fingerprint[:8], agent_user.username)
            else:
                logger.info('[PresenceViewSet] ✅ Nouvel appareil enregistré: %s pour %s', device_fingerprint[:8], agent_user.username)
        else:
            logger.warning('[PresenceViewSet] ⚠️ Aucune empreinte device reçue - restriction non appliquée')

        logger.info('[PresenceViewSet] Création de la présence pour agent=%s', agent_user)
        serializer.save(
            agent=agent_user,
            statut=statut,
            localisation_valide=localisation_valide,
            latitude=latitude,
            longitude=longitude,
            device_fingerprint=device_fingerprint,
            commentaire=commentaire_final
        )

    def partial_update(self, request, *args, **kwargs):
        # Multi-sites désactivé : gestion entreprise supprimée pour le départ
        return super().partial_update(request, *args, **kwargs)




class RolePermissionViewSet(viewsets.ModelViewSet):
    queryset = RolePermission.objects.all()
    serializer_class = RolePermissionSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]


class UserDiligenceCommentViewSet(viewsets.ModelViewSet):
    serializer_class = UserDiligenceCommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        queryset = UserDiligenceComment.objects.all()
        diligence_id = self.request.query_params.get('diligence', None)
        user_id = self.request.query_params.get('user', None)
        
        if diligence_id is not None:
            queryset = queryset.filter(diligence=diligence_id)
        if user_id is not None:
            queryset = queryset.filter(user=user_id)
            
        return queryset

    def perform_create(self, serializer):
        # Mettre à jour ou créer le commentaire
        diligence = serializer.validated_data['diligence']
        user = serializer.validated_data['user']
        comment = serializer.validated_data['comment']
        
        obj, created = UserDiligenceComment.objects.update_or_create(
            diligence=diligence,
            user=user,
            defaults={'comment': comment}
        )
        return obj


class UserDiligenceInstructionViewSet(viewsets.ModelViewSet):
    serializer_class = UserDiligenceInstructionSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        queryset = UserDiligenceInstruction.objects.all()
        diligence_id = self.request.query_params.get('diligence', None)
        user_id = self.request.query_params.get('user', None)
        
        if diligence_id is not None:
            queryset = queryset.filter(diligence=diligence_id)
        if user_id is not None:
            queryset = queryset.filter(user=user_id)
            
        return queryset

    def perform_create(self, serializer):
        # Mettre à jour ou créer l'instruction
        diligence = serializer.validated_data['diligence']
        user = serializer.validated_data['user']
        instruction = serializer.validated_data['instruction']
        
        obj, created = UserDiligenceInstruction.objects.update_or_create(
            diligence=diligence,
            user=user,
            defaults={'instruction': instruction}
        )
        return obj


class DemandeCongeViewSet(viewsets.ModelViewSet):
    serializer_class = DemandeCongeSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    def envoyer_notification(self, utilisateur, type_notification, titre, message, lien=''):
        """
        Envoie une notification à un utilisateur via le système de notification
        
        Args:
            utilisateur: L'utilisateur destinataire
            type_notification: Type de notification (ex: 'conges_validation', 'conges_rejet')
            titre: Titre de la notification
            message: Contenu détaillé de la notification
            lien: Lien optionnel vers la ressource concernée
        """
        try:
            from .models import DiligenceNotification
            
            # Création de la notification dans la base de données
            notification = DiligenceNotification.objects.create(
                user=utilisateur,
                type_notification=type_notification,
                message=message,
                lien=lien
            )
            
            # Ici, vous pourriez ajouter l'envoi de notification en temps réel
            # via des WebSockets ou un autre système de messagerie
            
            return True
            
        except Exception as e:
            print(f"Erreur lors de l'envoi de la notification à {utilisateur.username}: {str(e)}")
            return False
    
    def get_queryset(self):
        user = self.request.user
        profile = getattr(user, 'profile', None)
        
        if not profile:
            return DemandeConge.objects.none()
        
        # ADMIN peut voir toutes les demandes
        if profile.role == 'ADMIN':
            return DemandeConge.objects.all().order_by('-date_creation')
        
        # DIRECTEUR peut voir les demandes de toute sa direction
        elif profile.role == 'DIRECTEUR':
            if profile.service and profile.service.direction:
                direction_users = User.objects.filter(
                    profile__service__direction=profile.service.direction
                )
                return DemandeConge.objects.filter(
                    models.Q(demandeur=user) | 
                    models.Q(demandeur__in=direction_users) |
                    models.Q(superieur_hierarchique=user)
                ).order_by('-date_creation')
        
        # SUPERIEUR peut voir les demandes de son service uniquement
        elif profile.role == 'SUPERIEUR':
            if profile.service:
                service_users = User.objects.filter(profile__service=profile.service)
                return DemandeConge.objects.filter(
                    models.Q(demandeur=user) | 
                    models.Q(demandeur__in=service_users) |
                    models.Q(superieur_hierarchique=user)
                ).order_by('-date_creation')
        
        # SECRETAIRE peut voir les demandes de son service + ses propres demandes
        elif profile.role == 'SECRETAIRE':
            if profile.service:
                service_users = User.objects.filter(profile__service=profile.service)
                return DemandeConge.objects.filter(
                    models.Q(demandeur=user) | 
                    models.Q(demandeur__in=service_users) |
                    models.Q(superieur_hierarchique=user)
                ).order_by('-date_creation')
        
        # AGENT ne peut voir que ses propres demandes
        return DemandeConge.objects.filter(demandeur=user).order_by('-date_creation')
    
    def perform_create(self, serializer):
        # Déterminer le supérieur hiérarchique automatiquement
        user = self.request.user
        profile = getattr(user, 'profile', None)
        superieur = None
        
        if profile and profile.service:
            # Chercher un supérieur dans le même service
            superieur_profiles = UserProfile.objects.filter(
                service=profile.service,
                role__in=['SUPERIEUR', 'DIRECTEUR', 'SECRETAIRE']
            ).exclude(user=user).first()
            
            if superieur_profiles:
                superieur = superieur_profiles.user
        
        # Sauvegarder la demande
        demande = serializer.save(demandeur=user, superieur_hierarchique=superieur)
        
        # Créer une notification pour le supérieur hiérarchique
        if superieur:
            try:
                from .models import DiligenceNotification
                DiligenceNotification.objects.create(
                    user=superieur,
                    diligence=None,
                    type_notification='nouvelle_diligence',
                    message=f'{user.first_name} {user.last_name} a soumis une demande de congé {demande.get_type_conge_display()} du {demande.date_debut} au {demande.date_fin} nécessitant votre validation'
                )
            except Exception as e:
                print(f"Erreur notification supérieur congé: {e}")
        
        # Lier automatiquement les agents de la même direction et service
        if profile and profile.service:
            # Récupérer tous les agents du même service
            agents_meme_service = User.objects.filter(
                profile__service=profile.service
            ).exclude(id=user.id)
            
            # Si pas assez d'agents dans le service, inclure ceux de la même direction
            if agents_meme_service.count() < 3 and profile.service.direction:
                agents_meme_direction = User.objects.filter(
                    profile__service__direction=profile.service.direction
                ).exclude(id=user.id)
                
                # Combiner les agents du service et de la direction
                agents_concernes = agents_meme_service.union(agents_meme_direction)
            else:
                agents_concernes = agents_meme_service
            
            # Ajouter les agents concernés
            demande.agents_concernes.set(agents_concernes)
            
            # Créer des notifications pour les agents concernés
            try:
                from .models import DiligenceNotification
                for agent in agents_concernes:
                    DiligenceNotification.objects.create(
                        user=agent,
                        diligence=None,
                        type_notification='nouvelle_diligence',
                        message=f'{user.first_name} {user.last_name} a demandé un congé {demande.get_type_conge_display()} du {demande.date_debut} au {demande.date_fin}'
                    )
            except Exception as e:
                print(f"Erreur notification agents concernés congé: {e}")
    
    @action(detail=True, methods=['post'])
    def approuver(self, request, pk=None):
        demande = self.get_object()
        
        # Vérifier que l'utilisateur peut approuver cette demande
        if demande.superieur_hierarchique != request.user:
            profile = getattr(request.user, 'profile', None)
            if not profile or profile.role not in ['ADMIN', 'SUPERIEUR', 'DIRECTEUR']:
                return Response({'error': 'Non autorisé'}, status=403)
        
        demande.statut = 'approuve'
        demande.date_validation = timezone.now()
        demande.commentaire_validation = request.data.get('commentaire', '')
        demande.save()
        
        # Créer une notification pour le demandeur
        try:
            notification = Notification(
                user=demande.demandeur,
                type_notif='demande_approuvee',
                contenu=f'Votre demande de congé du {demande.date_debut} au {demande.date_fin} a été approuvée',
                lien=f'/conges/{demande.id}'
            )
            notification.save()
            
            # Envoyer une notification à l'utilisateur concerné
            self.envoyer_notification(
                utilisateur=demande.demandeur,
                type_notification='conges_validation',
                titre='Demande de congé approuvée',
                message=f'Votre demande de congé du {demande.date_debut} au {demande.date_fin} a été approuvée par {request.user.get_full_name() or request.user.username}.',
                lien=f'/conges/{demande.id}'
            )
        except Exception as e:
            print(f"Erreur notification congé approuvé: {e}")
        
        return Response({'message': 'Demande approuvée'})
    
    @action(detail=True, methods=['post'])
    def rejeter(self, request, pk=None):
        demande = self.get_object()
        
        # Vérifier que l'utilisateur peut rejeter cette demande
        if demande.superieur_hierarchique != request.user:
            profile = getattr(request.user, 'profile', None)
            if not profile or profile.role not in ['ADMIN', 'SUPERIEUR', 'DIRECTEUR']:
                return Response({'error': 'Non autorisé'}, status=403)
        
        demande.statut = 'rejete'
        demande.date_validation = timezone.now()
        demande.commentaire_validation = request.data.get('commentaire', '')
        demande.save()
        
        # Créer une notification pour le demandeur
        try:
            # Notification via le système existant
            from .models import Notification
            notification = Notification(
                user=demande.demandeur,
                type_notif='demande_rejetee',
                contenu=f'Votre demande de congé {demande.type_conge} du {demande.date_debut} au {demande.date_fin} a été rejetée',
                lien=f'/conges/{demande.id}'
            )
            notification.save()
            
            # Notification via le système de diligence
            self.envoyer_notification(
                utilisateur=demande.demandeur,
                type_notification='conges_rejet',
                titre='Demande de congé rejetée',
                message=f'Votre demande de congé du {demande.date_debut} au {demande.date_fin} a été rejetée par {request.user.get_full_name() or request.user.username}. Motif: {request.data.get("commentaire", "Aucun motif fourni")}',
                lien=f'/conges/{demande.id}'
            )
        except Exception as e:
            print(f"Erreur notification congé rejeté: {e}")
        
        return Response({'message': 'Demande rejetée'})
    
    @action(detail=True, methods=['get'])
    def telecharger_pdf(self, request, pk=None):
        """Télécharge la demande de congé en PDF"""
        demande = self.get_object()
        
        # Générer le PDF
        buffer = generate_conge_pdf(demande)
        filename = f"demande_conge_{demande.demandeur.username}_{demande.date_creation.strftime('%Y%m%d')}.pdf"
        
        return create_pdf_response(buffer, filename)


class DemandeAbsenceViewSet(viewsets.ModelViewSet):
    serializer_class = DemandeAbsenceSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    def envoyer_notification(self, utilisateur, type_notification, titre, message, lien=''):
        """
        Envoie une notification à un utilisateur via le système de notification
        
        Args:
            utilisateur: L'utilisateur destinataire
            type_notification: Type de notification (ex: 'conges_validation', 'absences_rejet')
            titre: Titre de la notification
            message: Contenu détaillé de la notification
            lien: Lien optionnel vers la ressource concernée
        """
        try:
            from .models import DiligenceNotification
            
            # Création de la notification dans la base de données
            notification = DiligenceNotification.objects.create(
                user=utilisateur,
                type_notification=type_notification,
                message=message,
                lien=lien
            )
            
            # Ici, vous pourriez ajouter l'envoi de notification en temps réel
            # via des WebSockets ou un autre système de messagerie
            
            return True
            
        except Exception as e:
            print(f"Erreur lors de l'envoi de la notification à {utilisateur.username}: {str(e)}")
            return False
    
    def get_queryset(self):
        user = self.request.user
        profile = getattr(user, 'profile', None)
        
        if not profile:
            return DemandeAbsence.objects.none()
        
        # ADMIN peut voir toutes les demandes
        if profile.role == 'ADMIN':
            return DemandeAbsence.objects.all().order_by('-created_at')
        
        # DIRECTEUR peut voir les demandes de toute sa direction
        elif profile.role == 'DIRECTEUR':
            if profile.service and profile.service.direction:
                direction_users = User.objects.filter(
                    profile__service__direction=profile.service.direction
                )
                return DemandeAbsence.objects.filter(
                    models.Q(demandeur=user) | 
                    models.Q(demandeur__in=direction_users) |
                    models.Q(superieur_hierarchique=user)
                ).order_by('-created_at')
        
        # SUPERIEUR peut voir les demandes de son service uniquement
        elif profile.role == 'SUPERIEUR':
            if profile.service:
                service_users = User.objects.filter(profile__service=profile.service)
                return DemandeAbsence.objects.filter(
                    models.Q(demandeur=user) | 
                    models.Q(demandeur__in=service_users) |
                    models.Q(superieur_hierarchique=user)
                ).order_by('-created_at')
        
        # SECRETAIRE peut voir les demandes de son service + ses propres demandes
        elif profile.role == 'SECRETAIRE':
            if profile.service:
                service_users = User.objects.filter(profile__service=profile.service)
                return DemandeAbsence.objects.filter(
                    models.Q(demandeur=user) | 
                    models.Q(demandeur__in=service_users) |
                    models.Q(superieur_hierarchique=user)
                ).order_by('-created_at')
        
        # AGENT ne peut voir que ses propres demandes
        return DemandeAbsence.objects.filter(demandeur=user).order_by('-created_at')
    
    def perform_create(self, serializer):
        # Déterminer le supérieur hiérarchique automatiquement
        user = self.request.user
        profile = getattr(user, 'profile', None)
        superieur = None
        
        if profile and profile.service:
            # Chercher un supérieur dans le même service
            superieur_profiles = UserProfile.objects.filter(
                service=profile.service,
                role__in=['SUPERIEUR', 'DIRECTEUR', 'SECRETAIRE']
            ).exclude(user=user).first()
            
            if superieur_profiles:
                superieur = superieur_profiles.user
        
        # Sauvegarder la demande
        demande = serializer.save(demandeur=user, superieur_hierarchique=superieur)
        
        # Créer une notification pour le supérieur hiérarchique
        if superieur:
            try:
                from .models import DiligenceNotification
                DiligenceNotification.objects.create(
                    user=superieur,
                    diligence=None,
                    type_notification='nouvelle_diligence',
                    message=f'{user.first_name} {user.last_name} a soumis une demande d\'absence {demande.get_type_absence_display()} du {demande.date_debut} au {demande.date_fin} nécessitant votre validation'
                )
            except Exception as e:
                print(f"Erreur notification supérieur absence: {e}")
        
        # Lier automatiquement les agents de la même direction et service
        if profile and profile.service:
            # Récupérer tous les agents du même service
            agents_meme_service = User.objects.filter(
                profile__service=profile.service
            ).exclude(id=user.id)
            
            # Si pas assez d'agents dans le service, inclure ceux de la même direction
            if agents_meme_service.count() < 3 and profile.service.direction:
                agents_meme_direction = User.objects.filter(
                    profile__service__direction=profile.service.direction
                ).exclude(id=user.id)
                
                # Combiner les agents du service et de la direction
                agents_concernes = agents_meme_service.union(agents_meme_direction)
            else:
                agents_concernes = agents_meme_service
            
            # Ajouter les agents concernés
            demande.agents_concernes.set(agents_concernes)
            
            # Créer des notifications pour les agents concernés
            try:
                from .models import DiligenceNotification
                for agent in agents_concernes:
                    DiligenceNotification.objects.create(
                        user=agent,
                        diligence=None,
                        type_notification='nouvelle_diligence',
                        message=f'{user.first_name} {user.last_name} a demandé une absence {demande.get_type_absence_display()} du {demande.date_debut} au {demande.date_fin}'
                    )
            except Exception as e:
                print(f"Erreur notification agents concernés absence: {e}")
    
    @action(detail=True, methods=['post'])
    def approuver(self, request, pk=None):
        demande = self.get_object()
        
        # Vérifier que l'utilisateur peut approuver cette demande
        if demande.superieur_hierarchique != request.user:
            profile = getattr(request.user, 'profile', None)
            if not profile or profile.role not in ['ADMIN', 'SUPERIEUR', 'DIRECTEUR']:
                return Response({'error': 'Non autorisé'}, status=403)
        
        demande.statut = 'approuve'
        demande.date_validation = timezone.now()
        demande.commentaire_validation = request.data.get('commentaire', '')
        demande.save()
        
        # Créer une notification pour le demandeur
        try:
            # Notification via le système existant
            from .models import Notification
            notification = Notification(
                user=demande.demandeur,
                type_notif='demande_approuvee',
                contenu=f'Votre demande d\'absence {demande.type_absence} du {demande.date_debut.strftime("%d/%m/%Y %H:%M")} a été approuvée',
                message=f'Votre demande d\'absence {demande.type_absence} du {demande.date_debut.strftime("%d/%m/%Y %H:%M")} a été approuvée par {request.user.get_full_name() or request.user.username}.',
                lien=f'/absences/{demande.id}'
            )
            notification.save()
            print(f"Notification standard créée avec succès pour {demande.demandeur.username}")
            
            # Notification via le système de diligence
            if hasattr(self, 'envoyer_notification'):
                success = self.envoyer_notification(
                    utilisateur=demande.demandeur,
                    type_notification='absences_validation',
                    titre='Demande d\'absence approuvée',
                    message=f'Votre demande d\'absence du {demande.date_debut.strftime("%d/%m/%Y %H:%M")} a été approuvée par {request.user.get_full_name() or request.user.username}.',
                    lien=f'/absences/{demande.id}'
                )
                print(f"Notification de diligence envoyée avec succès: {success}")
            else:
                print("Méthode envoyer_notification non trouvée dans la vue")
        except Exception as e:
            print(f"Erreur lors de la création des notifications: {str(e)}")
            import traceback
            traceback.print_exc()
        
        return Response({'message': 'Demande approuvée'})
    
    @action(detail=True, methods=['post'])
    def rejeter(self, request, pk=None):
        demande = self.get_object()
        
        # Vérifier que l'utilisateur peut rejeter cette demande
        if demande.superieur_hierarchique != request.user:
            profile = getattr(request.user, 'profile', None)
            if not profile or profile.role not in ['ADMIN', 'SUPERIEUR', 'DIRECTEUR']:
                return Response({'error': 'Non autorisé'}, status=403)
        
        demande.statut = 'rejete'
        demande.date_validation = timezone.now()
        demande.commentaire_validation = request.data.get('commentaire', '')
        demande.save()
        
        # Créer une notification pour le demandeur
        try:
            # Notification via le système existant
            from .models import Notification
            notification = Notification(
                user=demande.demandeur,
                type_notif='demande_rejetee',
                contenu=f'Votre demande d\'absence {demande.type_absence} du {demande.date_debut.strftime("%d/%m/%Y %H:%M")} a été rejetée',
                lien=f'/absences/{demande.id}'
            )
            notification.save()
            
            # Notification via le système de diligence
            self.envoyer_notification(
                utilisateur=demande.demandeur,
                type_notification='absences_rejet',
                titre='Demande d\'absence rejetée',
                message=f'Votre demande d\'absence du {demande.date_debut.strftime("%d/%m/%Y %H:%M")} a été rejetée par {request.user.get_full_name() or request.user.username}. Motif: {request.data.get("commentaire", "Aucun motif fourni")}',
                lien=f'/absences/{demande.id}'
            )
        except Exception as e:
            print(f"Erreur notification absence rejetée: {e}")
        
        return Response({'message': 'Demande rejetée'})
    
    @action(detail=True, methods=['get'])
    def telecharger_pdf(self, request, pk=None):
        """Télécharge la demande d'absence en PDF"""
        demande = self.get_object()
        
        # Générer le PDF
        buffer = generate_absence_pdf(demande)
        filename = f"demande_absence_{demande.demandeur.username}_{demande.created_at.strftime('%Y%m%d')}.pdf"
        
        return create_pdf_response(buffer, filename)


class CourrierImputationViewSet(viewsets.ModelViewSet):
    """ViewSet pour gérer les imputations des courriers confidentiels"""
    serializer_class = CourrierImputationSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        user = self.request.user
        
        # Seuls les ADMIN et DIRECTEUR peuvent voir les imputations
        if hasattr(user, 'profile') and user.profile.role in ['ADMIN', 'DIRECTEUR']:
            return CourrierImputation.objects.select_related('courrier', 'user', 'granted_by').all()
        
        # Les autres utilisateurs ne voient que leurs propres imputations
        return CourrierImputation.objects.filter(user=user).select_related('courrier', 'user', 'granted_by')

    def create(self, request, *args, **kwargs):
        """Créer une imputation - seuls ADMIN et DIRECTEUR peuvent le faire"""
        user = request.user
        
        # Vérifier les permissions
        if not (hasattr(user, 'profile') and user.profile.role in ['ADMIN', 'DIRECTEUR']):
            return Response(
                {'error': 'Seuls les administrateurs et directeurs peuvent créer des imputations'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Ajouter l'utilisateur qui accorde l'imputation
        data = request.data.copy()
        data['granted_by'] = user.id
        
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        """Supprimer une imputation - seuls ADMIN et DIRECTEUR peuvent le faire"""
        user = request.user
        
        # Vérifier les permissions
        if not (hasattr(user, 'profile') and user.profile.role in ['ADMIN', 'DIRECTEUR']):
            return Response(
                {'error': 'Seuls les administrateurs et directeurs peuvent supprimer des imputations'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().destroy(request, *args, **kwargs)

