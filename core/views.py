import os
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
from django.contrib.auth.models import User
from django.db.models import Q, Count, Prefetch
from django.shortcuts import get_object_or_404
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils import timezone
from datetime import datetime, timedelta
import mimetypes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission
from rest_framework.pagination import PageNumberPagination
from .models import *
from .serializers import DiligenceSerializer, DirectionSerializer, ServiceSerializer, CourrierSerializer, UserSerializer, UserRegistrationSerializer, BasicUserSerializer, ImputationFileSerializer


logger = logging.getLogger(__name__)

class SetFingerprintView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        fingerprint_hash = request.data.get('fingerprint_hash')
        if not fingerprint_hash:
            return Response({'error': 'Aucun hash fourni'}, status=status.HTTP_400_BAD_REQUEST)
        profile = request.user.profile
        profile.empreinte_hash = fingerprint_hash
        profile.save()
        return Response({'success': True, 'empreinte_hash': fingerprint_hash})

from rest_framework.authentication import TokenAuthentication

class ImputationFileViewSet(viewsets.ModelViewSet):
    queryset = ImputationFile.objects.all()
    serializer_class = ImputationFileSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def get_queryset(self):
        queryset = super().get_queryset()
        diligence_id = self.request.query_params.get('diligence')
        if diligence_id:
            queryset = queryset.filter(diligence_id=diligence_id)
        return queryset

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication]

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
        return qs.all()

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return BasicUserSerializer
        return UserSerializer

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        
        print("\nDébut de la mise à jour de l'utilisateur")
        print("Données reçues:", request.data)
        
        # Extraire les données du profil
        service_id = request.data.get('service_id')
        role_id = request.data.get('role_id') or request.data.get('role')
        superieurs = request.data.get('superieurs')
        
        print("Service reçu:", service_id)
        print("Role ID reçu:", role_id)
        print("Superieurs reçu:", superieurs)

        # Mettre à jour l'utilisateur de base
        serializer = self.get_serializer(instance, data=request.data, partial=kwargs.get('partial', False))
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Mettre à jour ou créer le profil
        if not hasattr(instance, 'profile'):
            print("Création d'un nouveau profil")
            UserProfile.objects.create(
                user=instance,
                service_id=service_id if service_id else None,
                role=role_id if role_id else 'USER'
            )
        else:
            print("Mise à jour du profil existant")
            profile = instance.profile
            print("Profil actuel - Role:", profile.role)
            
            if superieurs is not None:
                print("Tentative de mise à jour du superieur")
                try:
                    superieur_obj = Superieur.objects.get(id=superieurs)
                    print("Superieur trouvé:", superieur_obj)
                    profile.superieur = superieur_obj
                    print("Superieur assigné au profil")
                except Superieur.DoesNotExist:
                    print("Superieur non trouvé!")
                    print("Service assigné au profil")
                except Service.DoesNotExist:
                    print("Service non trouvé!")
                    return Response(
                        {'error': f'Service with id {service} does not exist'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            if service_id is not None:
                try:
                    from core.models import Service
                    service_obj = Service.objects.get(pk=service_id)
                    profile.service = service_obj
                except Service.DoesNotExist:
                    print(f"Service avec id {service_id} introuvable")
            if role_id is not None:
                profile.role = role_id
            
            print("Sauvegarde du profil")
            profile.save()
            print("Profil après sauvegarde - Service:", profile.service_id, "Role:", profile.role)

        # Retourner les données complètes avec le sérialiseur principal
        main_serializer = UserSerializer(instance)
        print("Données renvoyées:", main_serializer.data)
        return Response(main_serializer.data)

class LoginView(APIView):
    authentication_classes = []  # Désactive toute auth préalable
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        print("LOGIN VIEW CALLED", request.data)
        fingerprint_hash = request.data.get('fingerprint_hash')
        if fingerprint_hash:
            from .models import UserProfile
            try:
                profile = UserProfile.objects.get(empreinte_hash=fingerprint_hash)
                user = profile.user
                print("AUTH VIA FINGERPRINT: ", user)
            except UserProfile.DoesNotExist:
                print("ECHEC AUTH: empreinte non reconnue")
                return Response({'error': 'Empreinte non reconnue'}, status=status.HTTP_401_UNAUTHORIZED)
        else:
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
            UserProfile.objects.create(
                user=user,
                role='ADMIN'
            )

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

    def get_queryset(self):
        queryset = Direction.objects.prefetch_related('services').all().order_by('nom')
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

    def get_queryset(self):
        return Service.objects.select_related('direction').all().order_by('direction__nom', 'nom')

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
            return Diligence.objects.none()

        role = profile.role

        # Filtrage par statut si présent dans la requête
        statut = self.request.query_params.get('statut')
        if statut:
            base_qs = base_qs.filter(statut=statut)

        # Build queryset for diligences accessible by ImputationAccess
        from core.models import ImputationAccess
        imputation_access_qs = base_qs.filter(imputation_access__user=user)

        # AGENT : diligences où il est dans agents
        if role == 'AGENT':
            qs = base_qs.filter(agents=user)
        # SUPERIEUR ou SECRETAIRE : diligences des agents de leur service
        elif role in ['SUPERIEUR', 'SECRETAIRE']:
            if profile.service:
                qs = base_qs.filter(services_concernes=profile.service)
            else:
                qs = Diligence.objects.none()
        # DIRECTEUR : diligences de tous les rôles de leur direction
        elif role == 'DIRECTEUR':
            if profile.direction:
                qs = base_qs.filter(direction=profile.direction)
            else:
                qs = Diligence.objects.none()
        # ADMIN, superadmin, etc : tout voir
        else:
            qs = base_qs

        # Combine with ImputationAccess-based queryset (union, remove duplicates)
        return (qs | imputation_access_qs).distinct()  # Union with .distinct() to avoid duplicates

        # Note: If you want to be more restrictive and only add ImputationAccess for non-admins, adjust logic above.


    def create(self, request, *args, **kwargs):
        print("\nDonnées reçues pour création diligence:", request.data)
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

        print("\nDonnées finales avant création:", {
            'direction': request.data.get('direction'),
            'services_concernes_ids': request.data.get('services_concernes_ids'),
            'courrier_id': request.data.get('courrier_id'),
            'agents_ids': request.data.get('agents_ids')
        })
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        print("Appel explicite à serializer.save() (donc à create du serializer)")
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        print("Diligence créée avec succès:", serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        nouvelle_instruction = request.data.get('nouvelle_instruction')
        if nouvelle_instruction is not None:
            instance.instructions = nouvelle_instruction  # Remplace instructions
            instance.save()
        # Laisse DRF gérer les autres champs
        return super().partial_update(request, *args, **kwargs)


class CourrierViewSet(viewsets.ModelViewSet):
    queryset = Courrier.objects.all()
    serializer_class = CourrierSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def get_queryset(self):
        return Courrier.objects.select_related(
            'service',
            'service__direction'
        ).all().order_by('-date_reception')

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
from .serializers import RolePermissionSerializer, PresenceSerializer
from .models import RolePermission, Presence
from math import radians, cos, sin, asin, sqrt

class PresenceViewSet(viewsets.ModelViewSet):
    queryset = Presence.objects.all()
    serializer_class = PresenceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # Multi-sites : vérifie la présence sur n'importe quel lieu de l'entreprise de l'utilisateur
        from .models import LieuEntreprise
        from rest_framework.exceptions import ValidationError
        user = self.request.user
        entreprise = getattr(user.profile, 'entreprise', None)
        if not entreprise:
            raise ValidationError("Aucune entreprise associée à votre profil.")
        lieux = LieuEntreprise.objects.filter(entreprise=entreprise)
        if not lieux.exists():
            raise ValidationError("Aucun lieu défini pour votre entreprise.")
        lat = float(self.request.data.get('latitude', 0))
        lon = float(self.request.data.get('longitude', 0))
        from math import radians, cos, sin, asin, sqrt
        def haversine(lat1, lon1, lat2, lon2):
            R = 6371000
            dlat = radians(lat2 - lat1)
            dlon = radians(lon2 - lon1)
            a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
            c = 2 * asin(sqrt(a))
            return R * c
        localisation_valide = False
        for lieu in lieux:
            if haversine(lat, lon, lieu.latitude, lieu.longitude) <= lieu.seuil_metres:
                localisation_valide = True
                break
        if not localisation_valide:
            raise ValidationError("Merci de vous rendre sur un site autorisé de votre entreprise pour confirmer votre présence")
        statut = 'présent'
        user_id = self.request.data.get('user_id')
        if user_id:
            try:
                agent = User.objects.get(id=user_id)
            except User.DoesNotExist:
                agent = self.request.user
        else:
            agent = self.request.user
        serializer.save(agent=agent, statut=statut, localisation_valide=localisation_valide)

    def partial_update(self, request, *args, **kwargs):
        # Multi-sites : vérifie la présence sur n'importe quel lieu de l'entreprise de l'utilisateur pour le départ
        from .models import LieuEntreprise
        from rest_framework.exceptions import ValidationError
        user = request.user
        entreprise = getattr(user.profile, 'entreprise', None)
        if not entreprise:
            raise ValidationError("Aucune entreprise associée à votre profil.")
        lieux = LieuEntreprise.objects.filter(entreprise=entreprise)
        if not lieux.exists():
            raise ValidationError("Aucun lieu défini pour votre entreprise.")
        lat = float(request.data.get('latitude', 0))
        lon = float(request.data.get('longitude', 0))
        from math import radians, cos, sin, asin, sqrt
        def haversine(lat1, lon1, lat2, lon2):
            R = 6371000
            dlat = radians(lat2 - lat1)
            dlon = radians(lon2 - lon1)
            a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
            c = 2 * asin(sqrt(a))
            return R * c
        localisation_valide = False
        for lieu in lieux:
            if haversine(lat, lon, lieu.latitude, lieu.longitude) <= lieu.seuil_metres:
                localisation_valide = True
                break
        if not localisation_valide:
            raise ValidationError("Merci de vous rendre sur un site autorisé de votre entreprise pour confirmer votre départ")
        return super().partial_update(request, *args, **kwargs)

        # Géofencing dynamique : coordonnées du siège depuis la base
        from .models import LieuEntreprise
        try:
            siege = LieuEntreprise.objects.first()
            if not siege:
                raise Exception("Aucun lieu d'entreprise défini.")
        except Exception as e:
            raise ValidationError(str(e))
        lat = float(self.request.data.get('latitude', 0))
        lon = float(self.request.data.get('longitude', 0))
        from math import radians, cos, sin, asin, sqrt
        def haversine(lat1, lon1, lat2, lon2):
            R = 6371000  # Rayon Terre en mètres
            dlat = radians(lat2 - lat1)
            dlon = radians(lon2 - lon1)
            a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
            c = 2 * asin(sqrt(a))
            return R * c
        distance = haversine(lat, lon, siege.latitude, siege.longitude)
        if distance > siege.seuil_metres:
            from rest_framework.exceptions import ValidationError
            raise ValidationError("Merci de vous rendre au siège pour confirmer votre présence")
        localisation_valide = True
        statut = 'présent'
        user_id = self.request.data.get('user_id')
        if user_id:
            try:
                agent = User.objects.get(id=user_id)
            except User.DoesNotExist:
                agent = self.request.user
        else:
            agent = self.request.user
        serializer.save(agent=agent, statut=statut, localisation_valide=localisation_valide)



class RolePermissionViewSet(viewsets.ModelViewSet):
    queryset = RolePermission.objects.all()
    serializer_class = RolePermissionSerializer
    permission_classes = [permissions.IsAuthenticated]

# --- API pour retourner les lieux de l'entreprise de l'utilisateur ---
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import LieuEntreprise

class LieuxEntrepriseView(APIView):
    def get(self, request):
        entreprise = getattr(request.user.profile, 'entreprise', None)
        if not entreprise:
            return Response([], status=200)
        lieux = LieuEntreprise.objects.filter(entreprise=entreprise)
        data = [
            {
                'id': lieu.id,
                'nom': lieu.nom,
                'latitude': lieu.latitude,
                'longitude': lieu.longitude,
                'seuil_metres': lieu.seuil_metres
            }
            for lieu in lieux
        ]
        return Response(data)
