from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth.models import User
from django.utils import timezone
from .models import UserProfile, DeviceLock
import logging

logger = logging.getLogger(__name__)


class CheckDeviceLockView(APIView):
    """Vérifier si un appareil est verrouillé pour un autre utilisateur"""
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    def post(self, request):
        device_id = request.data.get('device_id')
        username = request.data.get('username')
        
        if not device_id or not username:
            return Response({
                'error': 'device_id et username requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Vérifier si l'appareil est verrouillé
            device_lock = DeviceLock.objects.filter(device_id=device_id).first()
            
            if device_lock:
                # L'appareil est verrouillé
                if device_lock.username != username:
                    # Verrouillé pour un autre utilisateur
                    return Response({
                        'is_locked': True,
                        'locked_by': device_lock.username,
                        'message': f'Ce téléphone est associé à {device_lock.username}. Contactez l\'administrateur.'
                    })
                else:
                    # Verrouillé pour le même utilisateur
                    device_lock.last_used = timezone.now()
                    device_lock.save()
                    return Response({
                        'is_locked': False,
                        'message': 'Appareil autorisé'
                    })
            else:
                # Appareil non verrouillé
                return Response({
                    'is_locked': False,
                    'message': 'Appareil non verrouillé'
                })
                
        except Exception as e:
            logger.error(f'Erreur vérification verrouillage: {str(e)}')
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LockDeviceView(APIView):
    """Verrouiller un appareil pour l'utilisateur actuel"""
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    def post(self, request):
        device_id = request.data.get('device_id')
        username = request.data.get('username')
        email = request.data.get('email')
        
        if not device_id or not username:
            return Response({
                'error': 'device_id et username requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Vérifier si l'appareil est déjà verrouillé
            device_lock = DeviceLock.objects.filter(device_id=device_id).first()
            
            if device_lock:
                if device_lock.username != username:
                    # Verrouillé pour un autre utilisateur
                    return Response({
                        'error': f'Appareil déjà verrouillé pour {device_lock.username}'
                    }, status=status.HTTP_403_FORBIDDEN)
                else:
                    # Mettre à jour la dernière utilisation
                    device_lock.last_used = timezone.now()
                    device_lock.save()
                    return Response({
                        'message': 'Appareil déjà verrouillé pour vous'
                    })
            else:
                # Créer un nouveau verrouillage
                device_lock = DeviceLock.objects.create(
                    device_id=device_id,
                    user=request.user,
                    username=username,
                    email=email or request.user.email
                )
                
                logger.info(f'Appareil {device_id} verrouillé pour {username}')
                
                return Response({
                    'message': 'Appareil verrouillé avec succès',
                    'device_id': device_id,
                    'username': username
                }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            logger.error(f'Erreur verrouillage appareil: {str(e)}')
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UnlockDeviceView(APIView):
    """Déverrouiller un appareil (admin uniquement)"""
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    def post(self, request):
        device_id = request.data.get('device_id')
        
        if not device_id:
            return Response({
                'error': 'device_id requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Vérifier si l'utilisateur est admin
        try:
            profile = request.user.profile
            if profile.role not in ['ADMIN', 'superadmin']:
                return Response({
                    'error': 'Seuls les administrateurs peuvent déverrouiller les appareils'
                }, status=status.HTTP_403_FORBIDDEN)
        except:
            return Response({
                'error': 'Profil utilisateur non trouvé'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            device_lock = DeviceLock.objects.filter(device_id=device_id).first()
            
            if device_lock:
                username = device_lock.username
                device_lock.delete()
                logger.info(f'Appareil {device_id} déverrouillé par {request.user.username}')
                
                return Response({
                    'message': f'Appareil déverrouillé (était verrouillé pour {username})'
                })
            else:
                return Response({
                    'message': 'Appareil non verrouillé'
                })
                
        except Exception as e:
            logger.error(f'Erreur déverrouillage appareil: {str(e)}')
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
