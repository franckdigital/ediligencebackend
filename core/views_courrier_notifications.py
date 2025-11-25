from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.db.models import Q, Count
from django.utils import timezone
from .models import CourrierNotification
from .serializers_courrier import CourrierNotificationSerializer


class CourrierNotificationViewSet(viewsets.ModelViewSet):
    """ViewSet pour gérer les notifications de courriers"""
    serializer_class = CourrierNotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        """Récupérer les notifications de l'utilisateur connecté"""
        user = self.request.user
        queryset = CourrierNotification.objects.filter(utilisateur=user)
        
        # Filtres optionnels
        lue = self.request.query_params.get('lue')
        if lue is not None:
            queryset = queryset.filter(lue=lue.lower() == 'true')
        
        type_notification = self.request.query_params.get('type')
        if type_notification:
            queryset = queryset.filter(type_notification=type_notification)
        
        priorite = self.request.query_params.get('priorite')
        if priorite:
            queryset = queryset.filter(priorite=priorite)
        
        courrier_id = self.request.query_params.get('courrier')
        if courrier_id:
            queryset = queryset.filter(courrier_id=courrier_id)
        
        return queryset.select_related('utilisateur', 'courrier', 'cree_par')

    @action(detail=False, methods=['get'])
    def non_lues(self, request):
        """Récupérer uniquement les notifications non lues"""
        notifications = self.get_queryset().filter(lue=False)
        serializer = self.get_serializer(notifications, many=True)
        return Response({
            'count': notifications.count(),
            'notifications': serializer.data
        })

    @action(detail=False, methods=['get'])
    def count_non_lues(self, request):
        """Compter les notifications non lues"""
        count = self.get_queryset().filter(lue=False).count()
        return Response({'count': count})

    @action(detail=True, methods=['post'])
    def marquer_lue(self, request, pk=None):
        """Marquer une notification comme lue"""
        notification = self.get_object()
        notification.marquer_comme_lue()
        serializer = self.get_serializer(notification)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def marquer_toutes_lues(self, request):
        """Marquer toutes les notifications comme lues"""
        notifications = self.get_queryset().filter(lue=False)
        count = notifications.count()
        
        for notification in notifications:
            notification.marquer_comme_lue()
        
        return Response({
            'message': f'{count} notification(s) marquée(s) comme lue(s)',
            'count': count
        })

    @action(detail=False, methods=['delete'])
    def supprimer_lues(self, request):
        """Supprimer toutes les notifications lues"""
        notifications = self.get_queryset().filter(lue=True)
        count = notifications.count()
        notifications.delete()
        
        return Response({
            'message': f'{count} notification(s) supprimée(s)',
            'count': count
        })

    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        """Statistiques des notifications de l'utilisateur"""
        queryset = self.get_queryset()
        
        total = queryset.count()
        non_lues = queryset.filter(lue=False).count()
        lues = queryset.filter(lue=True).count()
        
        # Par type
        par_type = queryset.values('type_notification').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Par priorité
        par_priorite = queryset.values('priorite').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Notifications récentes (7 derniers jours)
        sept_jours = timezone.now() - timezone.timedelta(days=7)
        recentes = queryset.filter(created_at__gte=sept_jours).count()
        
        return Response({
            'total': total,
            'non_lues': non_lues,
            'lues': lues,
            'par_type': list(par_type),
            'par_priorite': list(par_priorite),
            'recentes_7_jours': recentes
        })

    @action(detail=False, methods=['get'])
    def par_courrier(self, request):
        """Récupérer les notifications groupées par courrier"""
        courrier_id = request.query_params.get('courrier_id')
        
        if not courrier_id:
            return Response(
                {'error': 'courrier_id est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        notifications = self.get_queryset().filter(courrier_id=courrier_id)
        serializer = self.get_serializer(notifications, many=True)
        
        return Response({
            'courrier_id': courrier_id,
            'count': notifications.count(),
            'notifications': serializer.data
        })

    @action(detail=False, methods=['post'])
    def creer_notification_manuelle(self, request):
        """Créer une notification manuelle (pour ADMIN/DIRECTEUR)"""
        user = request.user
        
        # Vérifier les permissions
        if not (hasattr(user, 'profile') and user.profile.role in ['ADMIN', 'DIRECTEUR']):
            return Response(
                {'error': 'Seuls les administrateurs et directeurs peuvent créer des notifications manuelles'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        utilisateur_id = request.data.get('utilisateur_id')
        courrier_id = request.data.get('courrier_id')
        titre = request.data.get('titre')
        message = request.data.get('message')
        priorite = request.data.get('priorite', 'normale')
        
        if not all([utilisateur_id, titre, message]):
            return Response(
                {'error': 'utilisateur_id, titre et message sont requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from django.contrib.auth.models import User
            from .models import Courrier
            
            utilisateur = User.objects.get(id=utilisateur_id)
            courrier = Courrier.objects.get(id=courrier_id) if courrier_id else None
            
            notification = CourrierNotification.objects.create(
                utilisateur=utilisateur,
                courrier=courrier,
                type_notification='commentaire_ajoute',
                titre=titre,
                message=message,
                priorite=priorite,
                cree_par=user
            )
            
            serializer = self.get_serializer(notification)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except User.DoesNotExist:
            return Response(
                {'error': 'Utilisateur non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Courrier.DoesNotExist:
            return Response(
                {'error': 'Courrier non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def urgentes(self, request):
        """Récupérer les notifications urgentes non lues"""
        notifications = self.get_queryset().filter(
            lue=False,
            priorite='urgente'
        )
        serializer = self.get_serializer(notifications, many=True)
        return Response({
            'count': notifications.count(),
            'notifications': serializer.data
        })
