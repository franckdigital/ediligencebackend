print("SERIALIZERS.PY CHARGÉ")
import json
from rest_framework import serializers
from .models import ImputationFile

class ImputationFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImputationFile
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at', 'updated_at']
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from .models import *

class RolePermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RolePermission
        fields = ['id', 'role', 'permission', 'description']


class BasicUserSerializer(serializers.ModelSerializer):
    service = serializers.PrimaryKeyRelatedField(queryset=Service.objects.all(), required=False, allow_null=True)
    role_id = serializers.CharField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'service', 'role_id']
        read_only_fields = ['id']

class TacheHistoriqueSerializer(serializers.ModelSerializer):
    utilisateur = BasicUserSerializer(read_only=True)

    class Meta:
        model = TacheHistorique
        fields = ['id', 'tache', 'utilisateur', 'action', 'details', 'date']


class UserProfileSerializer(serializers.ModelSerializer):
    qr_code_url = serializers.SerializerMethodField()

    def get_qr_code_url(self, obj):
        if obj.qr_code:
            return obj.qr_code.url
        return None

    class Meta:
        model = UserProfile
        fields = ['role', 'service', 'qr_code_url']

from .models import Service

class ServiceSerializer(serializers.ModelSerializer):
    direction_nom = serializers.CharField(source='direction.nom', read_only=True)
    class Meta:
        model = Service
        fields = ['id', 'nom', 'description', 'direction', 'direction_nom']

class UserSerializer(serializers.ModelSerializer):
    service_obj = ServiceSerializer(source='profile.service', read_only=True)
    service = serializers.PrimaryKeyRelatedField(queryset=Service.objects.all(), source='profile.service', allow_null=True, required=False)
    matricule = serializers.CharField(source='profile.matricule', allow_null=True, allow_blank=True, required=False)
    role = serializers.CharField(source='profile.role')
    role_display = serializers.CharField(source='profile.get_role_display', read_only=True)
    qr_code_url = serializers.SerializerMethodField()


    role = serializers.SerializerMethodField(read_only=True)
    role_display = serializers.SerializerMethodField(read_only=True)
    service = serializers.PrimaryKeyRelatedField(source='profile.service', queryset=Service.objects.all(), required=False, allow_null=True)
    direction = serializers.SerializerMethodField(read_only=True)
    matricule = serializers.CharField(source='profile.matricule', required=False, allow_blank=True, allow_null=True)
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    qr_code_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name',
                 'role', 'role_display', 'service', 'service_obj', 'direction', 'matricule', 'qr_code_url', 'password']
        read_only_fields = ['id', 'role_display', 'direction', 'qr_code_url', 'service_obj']

    def get_qr_code_url(self, obj):
        if hasattr(obj, 'profile') and obj.profile.qr_code:
            return obj.profile.qr_code.url
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
        qr_code_needs_update = False
        if profile:
            # Matricule
            if matricule is not None and matricule != profile.matricule:
                logger.info(f'[UserSerializer] Mise à jour du matricule: {profile.matricule} -> {matricule}')
                profile.matricule = str(matricule)
                qr_code_needs_update = True
            # Service
            if service is not None:
                from .models import Service
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
            if qr_code_needs_update:
                try:
                    import qrcode
                    from io import BytesIO
                    from django.core.files.base import ContentFile
                    qr_content = f"{profile.matricule or instance.username}"
                    from PIL import Image, ImageDraw, ImageFont
                    img = qrcode.make(qr_content)
                    matricule_text = profile.matricule or instance.username
                    img = img.convert('RGB')
                    draw = ImageDraw.Draw(img)
                    font = None
                    try:
                        font = ImageFont.truetype("arial.ttf", 18)
                    except:
                        font = ImageFont.load_default()
                    bbox = draw.textbbox((0, 0), matricule_text, font=font)
                    text_w = bbox[2] - bbox[0]
                    text_h = bbox[3] - bbox[1]
                    # Position: bottom-right corner with padding
                    padding = 6
                    x = img.width - text_w - padding
                    y = img.height - text_h - padding
                    # Draw a white rectangle for readability
                    draw.rectangle([x - 2, y - 2, x + text_w + 2, y + text_h + 2], fill='white')
                    draw.text((x, y), matricule_text, fill='black', font=font)
                    buffer = BytesIO()
                    img.save(buffer, format="PNG")
                    file_name = f"qrcodes/agent_{profile.matricule or profile.id}.png"
                    profile.qr_code.save(file_name, ContentFile(buffer.getvalue()), save=True)
                    logger.info(f'[UserSerializer] QR code régénéré pour {profile.matricule}')
                except Exception as e:
                    logger.error(f'[UserSerializer] Error regenerating QR code: {str(e)}', exc_info=True)
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
    from .models import Agent
    class AgentSerializer(serializers.ModelSerializer):
        class Meta:
            model = Agent
            fields = ['id', 'nom', 'prenom', 'matricule', 'poste', 'service', 'role']
    agent_details = AgentSerializer(source='agent', read_only=True)

    class Meta:
        model = Presence
        fields = [
            'id', 'agent', 'agent_details', 'date_presence', 'heure_arrivee', 'heure_depart',
            'statut', 'qr_code_data', 'latitude', 'longitude', 'localisation_valide',
            'commentaire', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'agent', 'created_at', 'updated_at', 'localisation_valide', 'statut']

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user
        profile = user.profile
        
        # Ajouter les informations de l'utilisateur dans la réponse
        data.update({
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
        return data

    def get_role_display(self, role):
        """Retourne une version formatée du rôle pour l'affichage"""
        role_mapping = {
            'ADMIN': 'Administrateur',
            'superadmin': 'Super Administrateur',
            'USER': 'Utilisateur',
            'MANAGER': 'Manager'
        }
        return role_mapping.get(role, role)

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    role = serializers.ChoiceField(choices=UserProfile.ROLE_CHOICES, default='AGENT')
    service = serializers.PrimaryKeyRelatedField(queryset=Service.objects.all(), required=False, allow_null=True)
    matricule = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = User
        fields = ('username', 'password', 'password2', 'email', 'first_name', 'last_name', 'role', 'service', 'matricule')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'email': {'required': True}
        }

    def validate(self, attrs):
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f'[UserRegistrationSerializer] Validation data: {attrs}')
        if attrs['password'] != attrs['password2']:
            logger.error('[UserRegistrationSerializer] Password mismatch error')
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        try:
            validate_password(attrs['password'])
        except ValidationError as e:
            logger.error(f'[UserRegistrationSerializer] Password validation error: {e}')
            raise serializers.ValidationError({"password": list(e)})
        logger.info('[UserRegistrationSerializer] Validation successful')
        return attrs

    def create(self, validated_data):
        import logging
        import qrcode
        from io import BytesIO
        from django.core.files.base import ContentFile
        logger = logging.getLogger(__name__)
        logger.info(f'[UserRegistrationSerializer] Creating user with data: {validated_data}')
        try:
            role = validated_data.pop('role')
            service = validated_data.pop('service', None)
            matricule = validated_data.pop('matricule', None)
            validated_data.pop('password2')
            logger.debug(f'[UserRegistrationSerializer] Values after pop: role={role}, service={service}, matricule={matricule}')
            user = User.objects.create_user(**validated_data)
            logger.info(f'[UserRegistrationSerializer] User object created: {user}')
            profile = UserProfile.objects.create(user=user, role=role, service=service, matricule=matricule)
            qr_content = f"{matricule or getattr(profile, 'matricule', user.username)}"
            import qrcode
            from PIL import Image, ImageDraw, ImageFont
            img = qrcode.make(qr_content)
            matricule_text = matricule or getattr(profile, 'matricule', user.username)
            img = img.convert('RGB')
            draw = ImageDraw.Draw(img)
            font = None
            try:
                font = ImageFont.truetype("arial.ttf", 18)
            except:
                font = ImageFont.load_default()
            bbox = draw.textbbox((0, 0), matricule_text, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
            new_img = Image.new('RGB', (img.width, img.height + text_h + 10), 'white')
            new_img.paste(img, (0, 0))
            draw = ImageDraw.Draw(new_img)
            draw.text(((img.width - text_w) // 2, img.height + 5), matricule_text, fill='black', font=font)
            buffer = BytesIO()
            new_img.save(buffer, format="PNG")
            file_name = f"qrcodes/agent_{matricule or profile.id}.png"
            profile.qr_code.save(file_name, ContentFile(buffer.getvalue()), save=True)
            logger.info('[UserRegistrationSerializer] UserProfile and QR code created successfully')
            return user
        except Exception as e:
            logger.error(f'[UserRegistrationSerializer] Error creating user: {str(e)}', exc_info=True)
            raise serializers.ValidationError(str(e))

class DirectionSerializer(serializers.ModelSerializer):
    nombre_services = serializers.SerializerMethodField()
    services = serializers.SerializerMethodField()

    class Meta:
        model = Direction
        fields = ['id', 'nom', 'description', 'nombre_services', 'services', 'created_at', 'updated_at']

    def get_nombre_services(self, obj):
        return obj.services.count()

    def get_services(self, obj):
        return [{
            'id': service.id,
            'nom': service.nom,
            'description': service.description
        } for service in obj.services.all()]

class ServiceSerializer(serializers.ModelSerializer):
    direction_nom = serializers.CharField(source='direction.nom', read_only=True)

    class Meta:
        model = Service
        fields = ['id', 'nom', 'description', 'direction', 'direction_nom']

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
        fields = ['id', 'reference', 'expediteur', 'objet', 'date_reception', 
                 'service', 'service_details', 'categorie', 'fichier_joint', 'fichier_joint_url', 'created_at', 'updated_at']
        extra_kwargs = {
            'reference': {'required': True},
            'expediteur': {'required': True},
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
                except Service.DoesNotExist as e:
                    raise serializers.ValidationError({'non_field_errors': str(e)})
            return instance
        except Exception as e:
            print('Error creating user:', str(e))
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

class CourrierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Courrier
        fields = '__all__'
        # Si tu veux être explicite :
        # fields = ['id', 'reference', 'expediteur', 'objet', 'date_reception', 'service', 'categorie', 'fichier_joint', 'fichier_joint_url', 'created_at', 'updated_at']

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
        fields = ['id', 'reference_courrier', 'agents', 'agents_ids', 'services_concernes', 
                 'services_concernes_ids', 'categorie', 'statut', 'fichier_joint', 
                 'fichier_joint_url', 'instructions', 'date_limite', 'commentaires',
                 'expediteur', 'objet', 'date_reception', 'created_at', 'updated_at',
                 'courrier', 'courrier_id', 'direction', 'direction_details', 'nouvelle_instruction']

    def get_fichier_joint_url(self, obj):
        if obj.fichier_joint:
            return obj.fichier_joint.url
        return None

    def _process_list_field(self, value):
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return []
        return value

    
    def update(self, instance, validated_data):
        agents_ids = validated_data.pop('agents_ids', None)
        services_ids = validated_data.pop('services_concernes_ids', None)
        courrier_id = validated_data.pop('courrier_id', None)

        if agents_ids is not None:
            agents_ids = self._process_list_field(agents_ids)
            instance.agents.set(User.objects.filter(id__in=agents_ids))

        if services_ids is not None:
            services_ids = self._process_list_field(services_ids)
            instance.services_concernes.set(Service.objects.filter(id__in=services_ids))

        if courrier_id is not None:
            instance.courrier = Courrier.objects.get(id=courrier_id) if courrier_id else None

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

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

class EvenementSerializer(serializers.ModelSerializer):
    organisateur = UserSerializer(read_only=True)

    class Meta:
        model = Evenement
        fields = '__all__'

class EtapeEvenementSerializer(serializers.ModelSerializer):
    responsable = UserSerializer(read_only=True)

    class Meta:
        model = EtapeEvenement
        fields = '__all__'

class PresenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Presence
        fields = '__all__'

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


# --- SERIALIZERS SUIVI
# --- SERIALIZER POUR LES AUTORISATIONS D'IMPUTATION ---
from .models import ImputationAccess

class ImputationAccessSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImputationAccess
        fields = ['id', 'diligence', 'user', 'access_type', 'created_at']

# --- SERIALIZERS SUIVI PROJETS & TACHES ---
from .models import Projet, Tache, Commentaire, Fichier

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
    def get_agentsAffectes_usernames(self, obj):
        return [u.username for u in obj.agentsAffectes.all()]
    directeurs = serializers.PrimaryKeyRelatedField(queryset=users_with_role('DIRECTEUR'), many=True, required=False)
    superieurs = serializers.PrimaryKeyRelatedField(queryset=users_with_role('SUPERIEUR'), many=True, required=False)
    agents = serializers.PrimaryKeyRelatedField(queryset=users_with_role('AGENT'), many=True, required=False)
    secretaires = serializers.PrimaryKeyRelatedField(queryset=users_with_role('SECRETAIRE'), many=True, required=False)
    responsable_username = serializers.CharField(source='responsable.username', read_only=True)
    agentsAffectes_usernames = serializers.SerializerMethodField()
    sous_taches = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    commentaires = CommentaireSerializer(many=True, read_only=True)
    fichiers = FichierSerializer(many=True, read_only=True)

    class Meta:
        model = Tache
        fields = [
            'id', 'titre', 'description', 'etat', 'dateDebut', 'dateEcheance',
            'priorite', 'responsable', 'responsable_username', 'agentsAffectes', 'agentsAffectes_usernames',
            'projet', 'parentTache', 'sous_taches', 'createdAt', 'updatedAt',
            'commentaires', 'fichiers',
            'directeurs',
            'superieurs',
            'secretaires',
            'agents'  # Ajouté pour DRF
        ]

def users_with_role(role):
    return User.objects.filter(profile__role=role)

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
