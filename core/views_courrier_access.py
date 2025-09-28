from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth.models import User
from .models import CourrierAccess, Courrier
from .serializers import CourrierAccessSerializer
from .permissions import IsProfileAdmin

class CourrierAccessViewSet(viewsets.ModelViewSet):
    """ViewSet pour gérer les accès aux courriers confidentiels"""
    queryset = CourrierAccess.objects.all()
    serializer_class = CourrierAccessSerializer
    permission_classes = [permissions.IsAuthenticated, IsProfileAdmin]
    authentication_classes = [JWTAuthentication]
    
    def get_queryset(self):
        """Seuls les admins peuvent voir tous les accès"""
        user = self.request.user
        if hasattr(user, 'profile') and user.profile.role == 'ADMIN':
            return CourrierAccess.objects.all().select_related('courrier', 'user', 'granted_by')
        return CourrierAccess.objects.none()
    
    @action(detail=False, methods=['post'])
    def grant_access(self, request):
        """Accorder l'accès à un courrier confidentiel"""
        courrier_id = request.data.get('courrier_id')
        user_ids = request.data.get('user_ids', [])
        
        if not courrier_id or not user_ids:
            return Response({
                'error': 'courrier_id et user_ids sont requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            courrier = Courrier.objects.get(id=courrier_id, type_courrier='confidentiel')
        except Courrier.DoesNotExist:
            return Response({
                'error': 'Courrier confidentiel non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
        
        granted_accesses = []
        for user_id in user_ids:
            try:
                user = User.objects.get(id=user_id)
                access, created = CourrierAccess.objects.get_or_create(
                    courrier=courrier,
                    user=user,
                    defaults={'granted_by': request.user}
                )
                if created:
                    granted_accesses.append({
                        'user_id': user.id,
                        'username': user.username,
                        'granted': True
                    })
                else:
                    granted_accesses.append({
                        'user_id': user.id,
                        'username': user.username,
                        'granted': False,
                        'message': 'Accès déjà accordé'
                    })
            except User.DoesNotExist:
                granted_accesses.append({
                    'user_id': user_id,
                    'granted': False,
                    'message': 'Utilisateur non trouvé'
                })
        
        return Response({
            'message': 'Traitement des accès terminé',
            'results': granted_accesses
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'])
    def revoke_access(self, request):
        """Révoquer l'accès à un courrier confidentiel"""
        courrier_id = request.data.get('courrier_id')
        user_ids = request.data.get('user_ids', [])
        
        if not courrier_id or not user_ids:
            return Response({
                'error': 'courrier_id et user_ids sont requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        revoked_count = CourrierAccess.objects.filter(
            courrier_id=courrier_id,
            user_id__in=user_ids
        ).delete()[0]
        
        return Response({
            'message': f'{revoked_count} accès révoqués'
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def courrier_users(self, request):
        """Obtenir la liste des utilisateurs ayant accès à un courrier confidentiel"""
        courrier_id = request.query_params.get('courrier_id')
        
        if not courrier_id:
            return Response({
                'error': 'courrier_id est requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        accesses = CourrierAccess.objects.filter(
            courrier_id=courrier_id
        ).select_related('user', 'granted_by')
        
        serializer = self.get_serializer(accesses, many=True)
        return Response(serializer.data)
