import json
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from core.models import (
    UserProfile, Service, Direction, SousDirection, Courrier, CourrierAccess, CourrierImputation,
    UserDiligenceComment, UserDiligenceInstruction, DemandeConge, 
    DemandeAbsence, ImputationFile, DiligenceNotification, Diligence,
    Bureau, RolePermission, TacheHistorique, Agent, Presence,
    Notification, Observation, EtapeEvenement, Prestataire, 
    PrestataireEtape, Evaluation, DiligenceDocument, ImputationAccess,
    Fichier, Commentaire, Tache, Activite, Domaine, Projet,
    GeofenceAlert, GeofenceSettings, AgentLocation, PushNotificationToken,
    OccurrenceSpeciale
)

class ImputationFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImputationFile
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at', 'updated_at']

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        token['username'] = user.username
        return token

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        User = get_user_model()
        user = None
        
        # 1. Recherche par username
        try:
            user_obj = User.objects.get(username=username)
            if user_obj.check_password(password):
                user = user_obj
        except User.DoesNotExist:
            pass
            
        # 2. Recherche par email
        if user is None:
            email_lookup = username.strip().lower()
            try:
                user_obj = User.objects.get(email__iexact=email_lookup)
                if user_obj.check_password(password):
                    user = user_obj
            except User.DoesNotExist:
                pass
                
        # 3. Recherche par téléphone
        if user is None:
            try:
                profile = UserProfile.objects.get(telephone=username.strip())
                user_obj = profile.user
                if user_obj.check_password(password):
                    user = user_obj
            except UserProfile.DoesNotExist:
                pass
                
        if user is None:
            raise AuthenticationFailed('Aucun utilisateur trouvé')
        elif not user.is_active:
            raise AuthenticationFailed('Utilisateur inactif')
            
        attrs['username'] = user.username
        return super().validate(attrs)

class BureauSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bureau
        fields = '__all__'

    def validate(self, data):
        # Utilise la méthode clean du modèle pour la validation avancée
        instance = Bureau(**data)
        if self.instance:
            instance.pk = self.instance.pk
        try:
            instance.clean()
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message)
        return data

class RolePermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RolePermission
        fields = ['id', 'role', 'permission', 'description']


class BasicUserSerializer(serializers.ModelSerializer):
    service = serializers.PrimaryKeyRelatedField(queryset=Service.objects.all(), required=False, allow_null=True)
    role_id = serializers.CharField(required=False, allow_null=True)
    telephone = serializers.CharField(source='profile.telephone', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'telephone', 'service', 'role_id']
        read_only_fields = ['id']

class TacheHistoriqueSerializer(serializers.ModelSerializer):
    utilisateur = BasicUserSerializer(read_only=True)

    class Meta:
        model = TacheHistorique
        fields = ['id', 'tache', 'utilisateur', 'action', 'details', 'date']


class UserProfileSerializer(serializers.ModelSerializer):
    empreinte_hash = serializers.SerializerMethodField()
    telephone = serializers.CharField(required=False, allow_blank=True)

    def update(self, instance, validated_data):
        telephone = validated_data.get('telephone', None)
        if telephone is not None:
            instance.telephone = telephone
        # Mets à jour les autres champs si besoin
        instance = super().update(instance, validated_data)
        return instance

    def get_empreinte_hash(self, obj):
        # QR code functionality removed
        return None

    class Meta:
        model = UserProfile
        fields = ['role', 'service', 'empreinte_hash', 'telephone']

# Service déjà importé en haut

class ServiceSerializer(serializers.ModelSerializer):
    direction_nom = serializers.CharField(source='direction.nom', read_only=True)
    class Meta:
        model = Service
        fields = ['id', 'nom', 'description', 'direction', 'direction_nom']

class UserSerializer(serializers.ModelSerializer):
    telephone = serializers.CharField(source='profile.telephone', required=False, allow_blank=True)
    service_obj = ServiceSerializer(source='profile.service', read_only=True)
    service = serializers.PrimaryKeyRelatedField(
        queryset=Service.objects.all(),
        source='profile.service',
        allow_null=True,
        required=False
    )
    matricule = serializers.CharField(
        source='profile.matricule',
        allow_null=True,
        allow_blank=True,
        required=False
    )
    role = serializers.CharField(source='profile.role')
    role_display = serializers.CharField(source='profile.get_role_display', read_only=True)
    direction = serializers.SerializerMethodField(read_only=True)
    empreinte_hash = serializers.SerializerMethodField()
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    profile = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'role_display', 'service', 'service_obj', 'direction',
            'matricule', 'empreinte_hash', 'telephone', 'password', 'profile'
        ]
        read_only_fields = ['id', 'role_display', 'direction', 'empreinte_hash', 'service_obj']

    def get_empreinte_hash(self, obj):
        # Champ qr_code supprimé, retourne None ou la valeur voulue
        return None

    def get_direction(self, obj):
        print(f"[DEBUG] get_direction called for user {obj.id}")
        try:
            if hasattr(obj, 'profile') and obj.profile and obj.profile.service and obj.profile.service.direction:
                print(f"[DEBUG] Direction found: {obj.profile.service.direction.id}")
                return obj.profile.service.direction.id
        except AttributeError as e:
            print(f"[DEBUG] AttributeError in get_direction for user {obj.id}: {e}")
        print(f"[DEBUG] No direction found for user {obj.id}")
        return None
    
    def get_profile(self, obj):
        print(f"[DEBUG] get_profile called for user {obj.id}")
        try:
            if hasattr(obj, 'profile') and obj.profile:
                print(f"[DEBUG] Profile found for user {obj.id}")
                service_data = None
                if obj.profile.service:
                    direction_data = None
                    if obj.profile.service.direction:
                        direction_data = {
                            'id': obj.profile.service.direction.id,
                            'nom': obj.profile.service.direction.nom
                        }
                    service_data = {
                        'id': obj.profile.service.id,
                        'nom': obj.profile.service.nom,
                        'direction': direction_data
                    }
                
                return {
                    'role': obj.profile.role,
                    'matricule': obj.profile.matricule,
                    'telephone': obj.profile.telephone,
                    'service': service_data
                }
        except AttributeError as e:
            print(f"[DEBUG] AttributeError in get_profile for user {obj.id}: {e}")
        print(f"[DEBUG] No profile found for user {obj.id}")
        return None

    def update(self, instance, validated_data):
        import logging
        logger = logging.getLogger(__name__)
        profile_data = validated_data.pop('profile', {}) if 'profile' in validated_data else {}
        # Récupération du matricule
        matricule = None
        if 'matricule' in profile_data:
            matricule = profile_data['matricule']
        elif 'matricule' in validated_data:
            matricule = validated_data.pop('matricule')
        # Récupération du service
        service = None
        if 'service' in profile_data:
            service = profile_data['service']
        elif 'service' in validated_data:
            service = validated_data.pop('service')
        # Récupération du rôle
        role = None
        if 'role' in profile_data:
            role = profile_data['role']
        elif 'role' in validated_data:
            role = validated_data.pop('role')
        # Mot de passe
        password = validated_data.pop('password', None)
        # Update user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            logger.info(f'[UserSerializer] Mise à jour du mot de passe pour {instance.username}')
            instance.set_password(password)
        instance.save()
        # Update profile fields
        profile = getattr(instance, 'profile', None)
        if profile:
            # Matricule
            if matricule is not None and matricule != profile.matricule:
                logger.info(f'[UserSerializer] Mise à jour du matricule: {profile.matricule} -> {matricule}')
                profile.matricule = str(matricule)
            # Téléphone
            telephone = None
            if 'telephone' in validated_data:
                telephone = validated_data.pop('telephone')
            elif 'profile' in validated_data and 'telephone' in validated_data['profile']:
                telephone = validated_data['profile'].pop('telephone')
            if telephone is not None and telephone != profile.telephone:
                logger.info(f'[UserSerializer] Mise à jour du téléphone: {profile.telephone} -> {telephone}')
                profile.telephone = telephone

            # Service
            if service is not None:
                if isinstance(service, int):
                    try:
                        service_obj = Service.objects.get(pk=service)
                        logger.info(f'[UserSerializer] Mise à jour du service: {profile.service} -> {service_obj}')
                        profile.service = service_obj
                    except Service.DoesNotExist:
                        logger.warning(f'[UserSerializer] Service id {service} introuvable')
                else:
                    logger.info(f'[UserSerializer] Mise à jour du service: {profile.service} -> {service}')
                    profile.service = service
            # Role
            if role is not None and role != profile.role:
                logger.info(f'[UserSerializer] Mise à jour du rôle: {profile.role} -> {role}')
                profile.role = role
            # Correction finale du rôle si présent dans le payload à plat
            if hasattr(self, 'initial_data') and 'role' in self.initial_data:
                new_role = self.initial_data['role']
                if new_role != profile.role:
                    logger.info(f'[UserSerializer] Correction du rôle: {profile.role} -> {new_role}')
                    profile.role = new_role
            profile.save()
        return instance

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # S'assurer que tous les champs principaux sont présents
        for champ in ['id', 'username', 'email', 'first_name', 'last_name']:
            if champ not in data:
                data[champ] = getattr(instance, champ, None)
        return data

    def get_role(self, obj):
        if hasattr(obj, 'profile'):
            return obj.profile.role
        return None

    def get_role_display(self, obj):
        if hasattr(obj, 'profile'):
            return obj.profile.get_role_display()
        return None

    def get_service(self, obj):
        if hasattr(obj, 'profile') and obj.profile.service:
            return {
                'id': obj.profile.service.id,
                'nom': obj.profile.service.nom
            }
        return None

    def get_direction(self, obj):
        if hasattr(obj, 'profile') and obj.profile.service and obj.profile.service.direction:
            return {
                'id': obj.profile.service.direction.id,
                'nom': obj.profile.service.direction.nom
            }
        return None

# --- PresenceSerializer doit être défini APRÈS UserSerializer pour éviter l'import circulaire ---
class PresenceSerializer(serializers.ModelSerializer):
    agent = serializers.PrimaryKeyRelatedField(read_only=True)
    
    class AgentSerializer(serializers.ModelSerializer):
        service_obj = ServiceSerializer(source='service', read_only=True)
        bureau_obj = serializers.SerializerMethodField()
        
        def get_bureau_obj(self, obj):
            if obj.bureau:
                return {'id': obj.bureau.id, 'nom': obj.bureau.nom}
            return None
        
        class Meta:
            model = Agent
            fields = ['id', 'nom', 'prenom', 'matricule', 'poste', 'service', 'service_obj', 'bureau', 'bureau_obj']
    
    agent_details = AgentSerializer(source='agent', read_only=True)

    class Meta:
        model = Presence
        fields = [
            'id', 'agent', 'agent_details', 'date_presence', 'heure_arrivee', 'heure_depart',
            'heure_sortie', 'sortie_detectee', 'temps_absence_minutes', 'statut_modifiable',
            'statut', 'latitude', 'longitude', 'localisation_valide', 'device_fingerprint',
            'commentaire', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'agent', 'created_at', 'updated_at', 'localisation_valide']

class OccurrenceSpecialeSerializer(serializers.ModelSerializer):
    agent_details = UserSerializer(source='agent', read_only=True)
    createur_details = UserSerializer(source='createur', read_only=True)
    agent_id = serializers.IntegerField(write_only=True)
    createur_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = OccurrenceSpeciale
        fields = [
            'id', 'agent', 'agent_id', 'agent_details', 'type_occurrence', 'nom_occurrence',
            'statut', 'date', 'date_debut', 'date_fin', 'heure_debut', 'heure_fin', 
            'createur', 'createur_id', 'createur_details', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'agent', 'createur', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        agent_id = validated_data.pop('agent_id')
        createur_id = validated_data.pop('createur_id', None)
        
        validated_data['agent_id'] = agent_id
        if createur_id:
            validated_data['createur_id'] = createur_id
        
        return super().create(validated_data)


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    role = serializers.ChoiceField(choices=UserProfile.ROLE_CHOICES, default='AGENT')
    service = serializers.PrimaryKeyRelatedField(queryset=Service.objects.all(), required=False, allow_null=True)
    matricule = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    telephone = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ('username', 'password', 'password2', 'email', 'first_name', 'last_name', 'role', 'service', 'matricule', 'telephone')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'email': {'required': True}
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        try:
            validate_password(attrs['password'])
        except ValidationError as e:
            raise serializers.ValidationError({"password": list(e)})
        return attrs

    def create(self, validated_data):
        # Retirer les champs non User
        password = validated_data.pop('password', None)
        password2 = validated_data.pop('password2', None)
        role = validated_data.pop('role', 'AGENT')
        service = validated_data.pop('service', None)
        matricule = validated_data.pop('matricule', None)
        telephone = validated_data.pop('telephone', None)
        user = User.objects.create(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        # Créer ou mettre à jour le profil utilisateur
        profile, created = UserProfile.objects.get_or_create(user=user)
        profile.role = role
        updated = False
        
        if service:
            profile.service = service
            updated = True
            
        if matricule:
            profile.matricule = matricule
            updated = True
            
        if telephone:
            profile.telephone = telephone
            updated = True
            
        if updated or created:
            profile.save()  # Déclenche aussi la génération du QR code si besoin

        # Créer aussi un profil Agent si le rôle est AGENT
        if role == 'AGENT':
            from .models import Agent
            agent, agent_created = Agent.objects.get_or_create(
                user=user,
                defaults={
                    'nom': user.last_name or '',
                    'prenom': user.first_name or '',
                    'matricule': matricule or '',
                    'poste': 'AGENT',
                    'service': service
                }
            )

        return user

class DirectionSerializer(serializers.ModelSerializer):
    nombre_services = serializers.SerializerMethodField()
    services = serializers.SerializerMethodField()

    class Meta:
        model = Direction
        fields = ['id', 'nom', 'description', 'nombre_services', 'services', 'created_at', 'updated_at']

    def get_nombre_services(self, obj):
        # Utiliser la propriété du modèle qui gère le try/except
        return obj.nombre_services

    def get_services(self, obj):
        # Récupérer les services via les sous-directions
        try:
            services = []
            for sous_direction in obj.sous_directions.all():
                for service in sous_direction.services.all():
                    services.append({
                        'id': service.id,
                        'nom': service.nom,
                        'description': service.description
                    })
            return services
        except:
            # Fallback pour compatibilité
            return []

class SousDirectionSerializer(serializers.ModelSerializer):
    direction_nom = serializers.CharField(source='direction.nom', read_only=True)
    nombre_services = serializers.ReadOnlyField()

    class Meta:
        model = SousDirection
        fields = ['id', 'nom', 'description', 'direction', 'direction_nom', 'nombre_services', 'created_at', 'updated_at']


class ServiceSerializer(serializers.ModelSerializer):
    direction_nom = serializers.CharField(source='get_direction.nom', read_only=True)
    sous_direction_nom = serializers.CharField(source='sous_direction.nom', read_only=True)
    sous_direction_obj = SousDirectionSerializer(source='sous_direction', read_only=True)

    class Meta:
        model = Service
        fields = ['id', 'nom', 'description', 'sous_direction', 'sous_direction_nom', 'sous_direction_obj', 'direction', 'direction_nom']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        print(f'\nService {instance.nom}:')
        print('- Full data:', representation)
        return representation

class CourrierSerializer(serializers.ModelSerializer):
    service_details = serializers.SerializerMethodField()
    fichier_joint_url = serializers.SerializerMethodField()

    class Meta:
        model = Courrier
        fields = ['id', 'reference', 'expediteur', 'destinataire', 'objet', 'date_reception', 
                 'service', 'service_details', 'categorie', 'type_courrier', 'sens', 'fichier_joint', 'fichier_joint_url', 'created_at', 'updated_at']
        extra_kwargs = {
            'reference': {'required': True},
            'expediteur': {'required': True},
            'destinataire': {'required': False},
            'objet': {'required': True},
            'date_reception': {'required': True},
            'service': {'required': False},
            'categorie': {'required': True},
            'fichier_joint': {'required': False}
        }

    def get_fichier_joint_url(self, obj):
        request = self.context.get('request')
        if obj.fichier_joint and hasattr(obj.fichier_joint, 'url'):
            return request.build_absolute_uri(obj.fichier_joint.url)
        return None

    def get_service_details(self, obj):
        if obj.service:
            service = obj.service
            return {
                'id': service.id,
                'nom': service.nom,
                'description': service.description,
                'direction': service.direction.id if service.direction else None,
                'direction_nom': service.direction.nom if service.direction else None
            }
        return None

    def create(self, validated_data):
        try:
            print('\nValidated data:', validated_data)
            request_data = self.context['request'].data
            print('Request data:', dict(request_data))
            print('Files:', dict(self.context['request'].FILES))
            
            service_id = request_data.get('service')
            print('Service ID from request:', service_id)
            
            # Convertir les champs en types appropriés
            if 'date_reception' in validated_data:
                date_str = validated_data['date_reception']
                if isinstance(date_str, str):
                    try:
                        from datetime import datetime
                        validated_data['date_reception'] = datetime.strptime(date_str, '%Y-%m-%d').date()
                    except ValueError as e:
                        print('Error parsing date:', e)
                        raise serializers.ValidationError({'date_reception': 'Le format de date invalide'})
            
            # Si le service est dans validated_data, on le retire car on va le gérer manuellement
            validated_data.pop('service', None)
            
            instance = super().create(validated_data)
            if service_id:
                try:
                    service = Service.objects.get(id=service_id)
                    instance.service = service
                    instance.save()  # IMPORTANT: Sauvegarder l'instance après avoir assigné le service
                    print('Service successfully linked to courrier:', instance.service)
                except Service.DoesNotExist as e:
                    print(f'Service with id {service_id} does not exist')
                    raise serializers.ValidationError({'non_field_errors': str(e)})
            return instance
        except Exception as e:
            print('Error creating courrier:', str(e))
            raise serializers.ValidationError(str(e))

    def update(self, instance, validated_data):
        print('\nValidated data:', validated_data)
        service_id = self.context['request'].data.get('service')
        print('Service ID from request:', service_id)
        
        # Si le service est dans validated_data, on le retire car on va le gérer manuellement
        validated_data.pop('service', None)
        
        instance = super().update(instance, validated_data)
        if service_id:
            try:
                service = Service.objects.get(id=service_id)
                instance.service = service
                instance.save()
                print('Service linked to courrier:', instance.service)
            except Service.DoesNotExist:
                print(f'Service with id {service_id} does not exist')
        return instance

    def validate_reference(self, value):
        if not value.strip():
            raise serializers.ValidationError("La référence est requise")
        return value

    def validate_expediteur(self, value):
        if not value.strip():
            raise serializers.ValidationError("L'expéditeur est requis")
        return value

    def validate_objet(self, value):
        if not value.strip():
            raise serializers.ValidationError("L'objet est requis")
        return value

    def validate_date_reception(self, value):
        if not value:
            raise serializers.ValidationError("La date de réception est requise")
        return value
    def get_direction(self, obj):
        if hasattr(obj, 'profile') and obj.profile.service and obj.profile.service.direction:
            return {
                'id': obj.profile.service.direction.id,
                'nom': obj.profile.service.direction.nom
            }
        return None

class AdminUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    role = serializers.ChoiceField(choices=UserProfile.ROLE_CHOICES, default='USER')
    service = serializers.PrimaryKeyRelatedField(queryset=Service.objects.all(), required=False, allow_null=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'email', 'first_name', 'last_name', 'role', 'service')
        extra_kwargs = {
            'first_name': {'required': True},
        }

    def create(self, validated_data):
        role = validated_data.pop('role')
        service = validated_data.pop('service', None)
        validated_data['password'] = make_password(validated_data.get('password'))
        user = User.objects.create(**validated_data)
        # Create user profile
        UserProfile.objects.create(
            user=user,
            role=role,
            service=service
        )
        return user

class CourrierAccessSerializer(serializers.ModelSerializer):
    user_details = serializers.SerializerMethodField()
    granted_by_details = serializers.SerializerMethodField()
    
    class Meta:
        model = CourrierAccess
        fields = ['id', 'courrier', 'user', 'user_details', 'granted_by', 'granted_by_details', 'granted_at']
    
    def get_user_details(self, obj):
        return {
            'id': obj.user.id,
            'username': obj.user.username,
            'email': obj.user.email,
            'first_name': obj.user.first_name,
            'last_name': obj.user.last_name
        }
    
    def get_granted_by_details(self, obj):
        return {
            'id': obj.granted_by.id,
            'username': obj.granted_by.username,
            'email': obj.granted_by.email,
            'first_name': obj.granted_by.first_name,
            'last_name': obj.granted_by.last_name
        }

class CourrierImputationSerializer(serializers.ModelSerializer):
    user_details = serializers.SerializerMethodField()
    granted_by_details = serializers.SerializerMethodField()
    courrier_details = serializers.SerializerMethodField()
    
    class Meta:
        model = CourrierImputation
        fields = ['id', 'courrier', 'courrier_details', 'user', 'user_details', 'access_type', 'granted_by', 'granted_by_details', 'created_at']
    
    def get_user_details(self, obj):
        return {
            'id': obj.user.id,
            'username': obj.user.username,
            'email': obj.user.email,
            'first_name': obj.user.first_name,
            'last_name': obj.user.last_name
        }
    
    def get_granted_by_details(self, obj):
        return {
            'id': obj.granted_by.id,
            'username': obj.granted_by.username,
            'email': obj.granted_by.email,
            'first_name': obj.granted_by.first_name,
            'last_name': obj.granted_by.last_name
        }
    
    def get_courrier_details(self, obj):
        return {
            'id': obj.courrier.id,
            'reference': obj.courrier.reference,
            'objet': obj.courrier.objet,
            'type_courrier': obj.courrier.type_courrier
        }

    def get_fichier_joint_url(self, obj):
        request = self.context.get('request', None)
        if obj.fichier_joint and hasattr(obj.fichier_joint, 'url'):
            url = obj.fichier_joint.url
            if request is not None:
                return request.build_absolute_uri(url)
            return url
        return None


class DiligenceSerializer(serializers.ModelSerializer):
    agents = UserSerializer(many=True, read_only=True)
    agents_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)
    services_concernes = ServiceSerializer(many=True, read_only=True)
    services_concernes_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)
    fichier_joint = serializers.FileField(required=False, allow_null=True, allow_empty_file=True)
    fichier_joint_url = serializers.SerializerMethodField()
    courrier_fichier_url = serializers.SerializerMethodField()

    def create(self, validated_data):
        print('>>> DILIGENCE SERIALIZER CREATE APPELÉ <<<')
        print('DEBUG validated_data AVANT:', dict(validated_data))
        for key in [
            'agents_ids', 'services_concernes_ids', 'courrier_id',
            'fichiers', 'commentaires', 'direction_details',
            'agents', 'services_concernes', 'courrier'
        ]:
            validated_data.pop(key, None)
        print('DEBUG validated_data APRES:', dict(validated_data))

        instance = super().create(validated_data)

        # Récupère les ids depuis self.initial_data (plus robuste)
        agents_ids = self.initial_data.get('agents_ids', [])
        services_ids = self.initial_data.get('services_concernes_ids', [])
        courrier_id = self.initial_data.get('courrier_id', None)

        if agents_ids:
            if isinstance(agents_ids, str):
                try:
                    agents_ids = json.loads(agents_ids)
                except json.JSONDecodeError:
                    agents_ids = []
            if isinstance(agents_ids, int):
                agents_ids = [agents_ids]
            if not isinstance(agents_ids, list):
                agents_ids = list(agents_ids)
            instance.agents.set(agents_ids)
        if services_ids:
            if isinstance(services_ids, str):
                try:
                    services_ids = json.loads(services_ids)
                except json.JSONDecodeError:
                    services_ids = []
            if isinstance(services_ids, int):
                services_ids = [services_ids]
            if not isinstance(services_ids, list):
                services_ids = list(services_ids)
            instance.services_concernes.set(services_ids)
        if courrier_id:
            instance.courrier_id = courrier_id
            instance.save()

        return instance

    services_concernes = ServiceSerializer(many=True, read_only=True)

    services_concernes_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)
    fichier_joint = serializers.FileField(required=False, allow_null=True, allow_empty_file=True)
    fichier_joint_url = serializers.SerializerMethodField()
    courrier = CourrierSerializer(read_only=True)
    courrier_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    direction = serializers.PrimaryKeyRelatedField(queryset=Direction.objects.all(), required=False, allow_null=True)
    direction_details = DirectionSerializer(source='direction', read_only=True)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        # Ajouter les détails des services concernés
        services_details = []
        for service in instance.services_concernes.all():
            service_data = {
                'id': service.id,
                'nom': service.nom,
                'direction': {
                    'id': service.direction.id,
                    'nom': service.direction.nom
                } if service.direction else None
            }
            services_details.append(service_data)
        ret['services_details'] = services_details
        # Forcer agents_ids dans la sortie
        ret['agents_ids'] = [a.id for a in instance.agents.all()]
        return ret

    def get_agents(self, obj):
        agents_data = []
        for agent in obj.agents.all():
            service_info = None
            if hasattr(agent, 'profile') and agent.profile.service:
                service_info = {
                    'id': agent.profile.service.id,
                    'nom': agent.profile.service.nom,
                    'direction': {
                        'id': agent.profile.service.direction.id,
                        'nom': agent.profile.service.direction.nom
                    } if agent.profile.service.direction else None
                }
            
            agents_data.append({
                'id': agent.id,
                'username': agent.username,
                'email': agent.email,
                'first_name': agent.first_name,
                'last_name': agent.last_name,
                'service': service_info,
                'role': agent.profile.role if hasattr(agent, 'profile') else None
            })
        return agents_data

    class Meta:
        model = Diligence
        fields = ['id', 'type_diligence', 'reference_courrier', 'agents', 'agents_ids', 'services_concernes', 
                 'services_concernes_ids', 'domaine', 'categorie', 'statut', 'pourcentage_avancement',
                 'fichier_joint', 'fichier_joint_url', 'courrier_fichier_url', 'instructions', 'date_limite', 'date_rappel_1', 
                 'date_rappel_2', 'commentaires', 'commentaires_agents', 'expediteur', 'objet', 'date_reception', 'created_at', 
                 'updated_at', 'courrier', 'courrier_id', 'direction', 'direction_details', 
                 'nouvelle_instruction', 'validated_at', 'validated_by', 'archived_at', 'archived_by']

    def get_fichier_joint_url(self, obj):
        if obj.fichier_joint:
            return obj.fichier_joint.url
        return None
    
    def get_courrier_fichier_url(self, obj):
        """Retourne l'URL du fichier joint du courrier lié"""
        if obj.courrier and obj.courrier.fichier_joint:
            request = self.context.get('request')
            if request and hasattr(obj.courrier.fichier_joint, 'url'):
                return request.build_absolute_uri(obj.courrier.fichier_joint.url)
            return obj.courrier.fichier_joint.url
        return None

    def _process_list_field(self, value):
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return []
        return value

    
    def update(self, instance, validated_data):
        print(f"[DEBUG] DiligenceSerializer.update called with validated_data: {validated_data}")
        
        agents_ids = validated_data.pop('agents_ids', None)
        services_ids = validated_data.pop('services_concernes_ids', None)
        courrier_id = validated_data.pop('courrier_id', None)

        print(f"[DEBUG] agents_ids: {agents_ids}, services_ids: {services_ids}, courrier_id: {courrier_id}")

        if agents_ids is not None:
            agents_ids = self._process_list_field(agents_ids)
            print(f"[DEBUG] Processed agents_ids: {agents_ids}")
            instance.agents.set(User.objects.filter(id__in=agents_ids))

        if services_ids is not None:
            services_ids = self._process_list_field(services_ids)
            print(f"[DEBUG] Processed services_ids: {services_ids}")
            instance.services_concernes.set(Service.objects.filter(id__in=services_ids))

        if courrier_id is not None:
            print(f"[DEBUG] Setting courrier_id: {courrier_id}")
            try:
                instance.courrier = Courrier.objects.get(id=courrier_id) if courrier_id else None
            except Courrier.DoesNotExist:
                print(f"[ERROR] Courrier with id {courrier_id} does not exist")
                raise serializers.ValidationError(f"Courrier with id {courrier_id} does not exist")

        print(f"[DEBUG] Remaining validated_data: {validated_data}")
        for attr, value in validated_data.items():
            print(f"[DEBUG] Setting {attr} = {value}")
            setattr(instance, attr, value)
        
        try:
            instance.save()
            print(f"[DEBUG] Diligence {instance.id} saved successfully")
        except Exception as e:
            print(f"[ERROR] Failed to save diligence: {str(e)}")
            raise

        return instance

class NotificationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Notification
        fields = '__all__'

class ObservationSerializer(serializers.ModelSerializer):
    auteur = UserSerializer(read_only=True)

    class Meta:
        model = Observation
        fields = '__all__'

class EtapeEvenementSerializer(serializers.ModelSerializer):
    responsable = UserSerializer(read_only=True)

    class Meta:
        model = EtapeEvenement
        fields = '__all__'

# PresenceSerializer déjà défini plus haut avec agent_details

class PrestataireSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prestataire
        fields = '__all__'

class PrestataireEtapeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrestataireEtape
        fields = '__all__'

class EvaluationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Evaluation
        fields = '__all__'

# --- SERIALIZERS POUR DILIGENCES AMÉLIORÉES ---
class DiligenceDocumentSerializer(serializers.ModelSerializer):
    created_by_details = UserSerializer(source='created_by', read_only=True)
    validated_by_details = UserSerializer(source='validated_by', read_only=True)

    class Meta:
        model = DiligenceDocument
        fields = [
            'id', 'diligence', 'titre', 'contenu', 'fichier', 'statut', 'version',
            'created_by', 'created_by_details', 'created_at', 'updated_at',
            'validated_by', 'validated_by_details', 'validated_at'
        ]

class DiligenceNotificationSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)
    diligence_details = serializers.SerializerMethodField()

    def get_diligence_details(self, obj):
        if not obj.diligence:
            return None
        return {
            'id': obj.diligence.id,
            'reference_courrier': getattr(obj.diligence, 'reference_courrier', None),
            'objet': getattr(obj.diligence, 'objet', None)
        }

    class Meta:
        model = DiligenceNotification
        fields = [
            'id', 'user', 'user_details', 'diligence', 'diligence_details',
            'type_notification', 'message', 'read', 'created_at'
        ]


# --- SERIALIZERS SUIVI
# --- SERIALIZER POUR LES AUTORISATIONS D'IMPUTATION ---
# ImputationAccess déjà importé en haut

class ImputationAccessSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImputationAccess
        fields = ['id', 'diligence', 'user', 'access_type', 'created_at']

# --- SERIALIZERS SUIVI PROJETS & TACHES ---
# Tous les modèles déjà importés en haut du fichier

class FichierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fichier
        fields = '__all__'

class CommentaireSerializer(serializers.ModelSerializer):
    auteur_username = serializers.CharField(source='auteur.username', read_only=True)
    class Meta:
        model = Commentaire
        fields = ['id', 'contenu', 'auteur', 'auteur_username', 'tache', 'createdAt']

def users_with_role(role):
    return User.objects.filter(profile__role=role)

class TacheSerializer(serializers.ModelSerializer):
    responsable_details = UserSerializer(source='responsable', read_only=True)
    agents_details = UserSerializer(source='agents', many=True, read_only=True)
    domaine_details = serializers.SerializerMethodField()
    sous_taches = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    
    def get_domaine_details(self, obj):
        if obj.domaine:
            return {
                'id': obj.domaine.id,
                'nom': obj.domaine.nom,
                'superviseur': obj.domaine.superviseur.username if obj.domaine.superviseur else None
            }
        return None

    class Meta:
        model = Tache
        fields = [
            'id', 'titre', 'description', 'etat', 'priorite', 
            'responsable', 'responsable_details',
            'agents', 'agents_details',
            'domaine', 'domaine_details',
            'tache_parent', 'sous_taches',
            'date_debut', 'date_fin_prevue', 'date_fin_effective',
            'pourcentage_avancement',
            'createdAt', 'updatedAt',
            # Garder pour compatibilité
            'projet', 'directeurs', 'superieurs', 'secretaires'
        ]

def users_with_role(role):
    return User.objects.filter(profile__role=role)

class ActiviteSerializer(serializers.ModelSerializer):
    responsable_principal_details = UserSerializer(source='responsable_principal', read_only=True)
    service_details = ServiceSerializer(source='service', read_only=True)
    domaines = serializers.SerializerMethodField()
    
    class Meta:
        model = Activite
        fields = ['id', 'nom', 'description', 'type_activite', 'service', 'service_details',
                 'responsable_principal', 'responsable_principal_details', 'date_debut', 
                 'date_fin_prevue', 'date_fin_effective', 'etat', 'lieu', 'budget_previsionnel',
                 'nombre_participants_prevu', 'domaines', 'created_at', 'updated_at']
    
    def get_domaines(self, obj):
        return DomaineSerializer(obj.domaines.all(), many=True).data

class DomaineSerializer(serializers.ModelSerializer):
    superviseur_details = UserSerializer(source='superviseur', read_only=True)
    activite_details = serializers.SerializerMethodField()
    taches = serializers.SerializerMethodField()
    
    class Meta:
        model = Domaine
        fields = ['id', 'nom', 'description', 'activite', 'activite_details', 'superviseur',
                 'superviseur_details', 'date_debut', 'date_fin_prevue', 'date_fin_effective',
                 'pourcentage_avancement', 'taches', 'created_at', 'updated_at']
    
    def get_activite_details(self, obj):
        return {'id': obj.activite.id, 'nom': obj.activite.nom}
    
    def get_taches(self, obj):
        return TacheSerializer(obj.taches.filter(tache_parent__isnull=True), many=True).data

class ProjetSerializer(serializers.ModelSerializer):
    service = serializers.PrimaryKeyRelatedField(queryset=Service.objects.all(), required=False, allow_null=True)
    direction = serializers.PrimaryKeyRelatedField(queryset=Direction.objects.all(), required=False, allow_null=True)
    def create(self, validated_data):
        # Lier automatiquement la direction à partir du service sélectionné
        service = validated_data.get('service')
        if service and not validated_data.get('direction'):
            validated_data['direction'] = service.direction
        return super().create(validated_data)

    directeurs_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)
    superieurs_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)
    agents_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)
    secretaires_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)
    directeurs = serializers.PrimaryKeyRelatedField(queryset=users_with_role('DIRECTEUR'), many=True, required=False)
    superieurs = serializers.PrimaryKeyRelatedField(queryset=users_with_role('SUPERIEUR'), many=True, required=False)
    agents = serializers.PrimaryKeyRelatedField(queryset=users_with_role('AGENT'), many=True, required=False)
    secretaires = serializers.PrimaryKeyRelatedField(queryset=users_with_role('SECRETAIRE'), many=True, required=False)
    responsable_username = serializers.CharField(source='responsable.username', read_only=True)
    membres_usernames = serializers.SlugRelatedField(many=True, slug_field='username', read_only=True, source='membres')
    taches = TacheSerializer(many=True, read_only=True)
    fichiers = FichierSerializer(many=True, read_only=True)

    def update(self, instance, validated_data):
        directeurs_ids = validated_data.pop('directeurs_ids', None)
        superieurs_ids = validated_data.pop('superieurs_ids', None)
        agents_ids = validated_data.pop('agents_ids', None)
        secretaires_ids = validated_data.pop('secretaires_ids', None)

        if directeurs_ids is not None:
            directeurs_ids = self._process_list_field(directeurs_ids)
            instance.directeurs.set(User.objects.filter(id__in=directeurs_ids))

        if superieurs_ids is not None:
            superieurs_ids = self._process_list_field(superieurs_ids)
            instance.superieurs.set(User.objects.filter(id__in=superieurs_ids))

        if agents_ids is not None:
            agents_ids = self._process_list_field(agents_ids)
            instance.agents.set(User.objects.filter(id__in=agents_ids))

        if secretaires_ids is not None:
            secretaires_ids = self._process_list_field(secretaires_ids)
            instance.secretaires.set(User.objects.filter(id__in=secretaires_ids))

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance

    def _process_list_field(self, value):
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return []
        return value

    class Meta:
        model = Projet
        fields = [
            'id', 'nom', 'description', 'dateDebut', 'dateFinPrevue', 'dateFinEffective',
            'etat', 'responsable', 'responsable_username', 'membres', 'membres_usernames',
            'directeurs', 'directeurs_ids', 'superieurs', 'superieurs_ids', 'agents', 'agents_ids', 'secretaires', 'secretaires_ids',
            'createdAt', 'updatedAt', 'taches', 'fichiers', 'service', 'direction'
        ]


class UserDiligenceCommentSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    diligence_reference = serializers.CharField(source='diligence.reference_courrier', read_only=True)

    class Meta:
        model = UserDiligenceComment
        fields = ['id', 'diligence', 'user', 'user_name', 'diligence_reference', 'comment', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class UserDiligenceInstructionSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    diligence_reference = serializers.CharField(source='diligence.reference_courrier', read_only=True)

    class Meta:
        model = UserDiligenceInstruction
        fields = ['id', 'diligence', 'user', 'user_name', 'diligence_reference', 'instruction', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class DemandeCongeSerializer(serializers.ModelSerializer):
    demandeur_name = serializers.CharField(source='demandeur.username', read_only=True)
    demandeur_full_name = serializers.SerializerMethodField()
    superieur_name = serializers.CharField(source='superieur_hierarchique.username', read_only=True)
    directeur_name = serializers.SerializerMethodField()
    superieur_selected_name = serializers.SerializerMethodField()
    type_conge_display = serializers.CharField(source='get_type_conge_display', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    
    class Meta:
        model = DemandeConge
        fields = [
            'id', 'demandeur', 'demandeur_name', 'demandeur_full_name',
            'matricule', 'emploi', 'fonction',
            'type_conge', 'type_conge_display', 'date_debut', 'date_fin', 
            'nombre_jours', 'motif', 'adresse_conge', 'telephone_conge',
            'directeur', 'directeur_name', 'superieur', 'superieur_selected_name',
            'superieur_hierarchique', 'superieur_name', 'statut', 'statut_display',
            'date_validation', 'commentaire_validation', 'document_demande', 
            'document_reponse', 'agents_concernes', 'date_creation', 'date_modification'
        ]
        read_only_fields = ['date_creation', 'date_modification', 'nombre_jours', 'demandeur', 'superieur_hierarchique']
    
    def get_demandeur_full_name(self, obj):
        return f"{obj.demandeur.first_name} {obj.demandeur.last_name}".strip() or obj.demandeur.username
    
    def get_directeur_name(self, obj):
        if obj.directeur:
            return f"{obj.directeur.first_name} {obj.directeur.last_name}".strip() or obj.directeur.username
        return None
    
    def get_superieur_selected_name(self, obj):
        if obj.superieur:
            return f"{obj.superieur.first_name} {obj.superieur.last_name}".strip() or obj.superieur.username
        return None


class DemandeAbsenceSerializer(serializers.ModelSerializer):
    demandeur_name = serializers.CharField(source='demandeur.username', read_only=True)
    demandeur_full_name = serializers.SerializerMethodField()
    superieur_name = serializers.CharField(source='superieur_hierarchique.username', read_only=True)
    directeur_name = serializers.SerializerMethodField()
    superieur_selected_name = serializers.SerializerMethodField()
    type_absence_display = serializers.CharField(source='get_type_absence_display', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    
    class Meta:
        model = DemandeAbsence
        fields = [
            'id', 'demandeur', 'demandeur_name', 'demandeur_full_name',
            'matricule', 'emploi', 'fonction',
            'type_absence', 'type_absence_display', 'date_debut', 'date_fin',
            'duree_heures', 'motif', 
            'directeur', 'directeur_name', 'superieur', 'superieur_selected_name',
            'superieur_hierarchique', 'superieur_name',
            'statut', 'statut_display', 'date_validation', 'commentaire_validation',
            'document_demande', 'document_reponse', 'agents_concernes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'duree_heures', 'demandeur', 'superieur_hierarchique']
    
    def get_demandeur_full_name(self, obj):
        return f"{obj.demandeur.first_name} {obj.demandeur.last_name}".strip() or obj.demandeur.username
    
    def get_directeur_name(self, obj):
        if obj.directeur:
            return f"{obj.directeur.first_name} {obj.directeur.last_name}".strip() or obj.directeur.username
        return None
    
    def get_superieur_selected_name(self, obj):
        if obj.superieur:
            return f"{obj.superieur.first_name} {obj.superieur.last_name}".strip() or obj.superieur.username
        return None
