from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.db.models import Count, Q, Avg, F, ExpressionWrapper, fields
from django.utils import timezone
from datetime import timedelta, datetime
from .models import (
    Courrier, CourrierAccess, CourrierImputation, 
    CourrierStatut, CourrierRappel, Diligence, Service, Direction
)
from django.contrib.auth.models import User


class CourrierStatsViewSet(viewsets.ViewSet):
    """ViewSet pour les statistiques des courriers"""
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    @action(detail=False, methods=['get'])
    def statistiques_globales(self, request):
        """
        Statistiques globales des courriers
        """
        # Filtres optionnels
        date_debut = request.query_params.get('date_debut')
        date_fin = request.query_params.get('date_fin')
        service_id = request.query_params.get('service')
        direction_id = request.query_params.get('direction')

        queryset = Courrier.objects.all()

        # Appliquer les filtres
        if date_debut:
            queryset = queryset.filter(date_reception__gte=date_debut)
        if date_fin:
            queryset = queryset.filter(date_reception__lte=date_fin)
        if service_id:
            queryset = queryset.filter(service_id=service_id)
        if direction_id:
            queryset = queryset.filter(service__direction_id=direction_id)

        # Nombre total de courriers
        total_courriers = queryset.count()

        # Courriers par type
        courriers_par_type = queryset.values('type_courrier').annotate(
            count=Count('id')
        )

        # Courriers par sens
        courriers_par_sens = queryset.values('sens').annotate(
            count=Count('id')
        )

        # Courriers par catégorie
        courriers_par_categorie = queryset.values('categorie').annotate(
            count=Count('id')
        ).order_by('-count')

        # Courriers par service
        courriers_par_service = queryset.values(
            'service__nom', 'service_id'
        ).annotate(
            count=Count('id')
        ).order_by('-count')

        # Courriers par direction
        courriers_par_direction = queryset.values(
            'service__direction__nom', 'service__direction_id'
        ).annotate(
            count=Count('id')
        ).order_by('-count')

        # Taux de traitement (courriers avec diligences)
        courriers_avec_diligence = queryset.filter(
            diligences__isnull=False
        ).distinct().count()
        
        taux_traitement = (courriers_avec_diligence / total_courriers * 100) if total_courriers > 0 else 0

        # Délai moyen de traitement
        courriers_traites = queryset.filter(
            diligences__isnull=False
        ).annotate(
            delai=ExpressionWrapper(
                F('diligences__created_at') - F('date_reception'),
                output_field=fields.DurationField()
            )
        )
        
        delai_moyen = courriers_traites.aggregate(
            delai_moyen=Avg('delai')
        )['delai_moyen']
        
        delai_moyen_jours = delai_moyen.days if delai_moyen else 0

        # Statistiques par période
        aujourd_hui = timezone.now().date()
        
        courriers_aujourd_hui = queryset.filter(
            date_reception=aujourd_hui
        ).count()
        
        courriers_cette_semaine = queryset.filter(
            date_reception__gte=aujourd_hui - timedelta(days=7)
        ).count()
        
        courriers_ce_mois = queryset.filter(
            date_reception__year=aujourd_hui.year,
            date_reception__month=aujourd_hui.month
        ).count()
        
        courriers_cette_annee = queryset.filter(
            date_reception__year=aujourd_hui.year
        ).count()

        return Response({
            'total_courriers': total_courriers,
            'courriers_par_type': list(courriers_par_type),
            'courriers_par_sens': list(courriers_par_sens),
            'courriers_par_categorie': list(courriers_par_categorie),
            'courriers_par_service': list(courriers_par_service),
            'courriers_par_direction': list(courriers_par_direction),
            'taux_traitement': round(taux_traitement, 2),
            'courriers_avec_diligence': courriers_avec_diligence,
            'courriers_sans_diligence': total_courriers - courriers_avec_diligence,
            'delai_moyen_traitement_jours': delai_moyen_jours,
            'periode': {
                'aujourd_hui': courriers_aujourd_hui,
                'cette_semaine': courriers_cette_semaine,
                'ce_mois': courriers_ce_mois,
                'cette_annee': courriers_cette_annee
            }
        })

    @action(detail=False, methods=['get'])
    def statistiques_confidentiels(self, request):
        """
        Statistiques spécifiques aux courriers confidentiels
        """
        user = request.user
        
        # Vérifier les permissions
        if not (hasattr(user, 'profile') and user.profile.role in ['ADMIN', 'DIRECTEUR']):
            return Response(
                {'error': 'Accès non autorisé'}, 
                status=status.HTTP_403_FORBIDDEN
            )

        courriers_confidentiels = Courrier.objects.filter(type_courrier='confidentiel')

        # Nombre total de courriers confidentiels
        total_confidentiels = courriers_confidentiels.count()

        # Nombre d'accès accordés par courrier
        acces_par_courrier = CourrierAccess.objects.filter(
            courrier__type_courrier='confidentiel'
        ).values('courrier__reference', 'courrier_id').annotate(
            nb_acces=Count('id')
        ).order_by('-nb_acces')[:10]

        # Utilisateurs avec le plus d'accès
        utilisateurs_acces = CourrierAccess.objects.filter(
            courrier__type_courrier='confidentiel'
        ).values(
            'user__username', 'user__first_name', 'user__last_name', 'user_id'
        ).annotate(
            nb_acces=Count('id')
        ).order_by('-nb_acces')[:10]

        # Imputations actives
        imputations_confidentiels = CourrierImputation.objects.filter(
            courrier__type_courrier='confidentiel'
        )
        
        total_imputations = imputations_confidentiels.count()
        imputations_lecture = imputations_confidentiels.filter(access_type='view').count()
        imputations_edition = imputations_confidentiels.filter(access_type='edit').count()

        # Courriers confidentiels non imputés
        courriers_non_imputes = courriers_confidentiels.filter(
            imputation_access__isnull=True
        ).count()

        # Historique des accès récents
        historique_acces = CourrierAccess.objects.filter(
            courrier__type_courrier='confidentiel'
        ).select_related('user', 'granted_by', 'courrier').order_by('-created_at')[:20]

        historique_data = [{
            'courrier_reference': acces.courrier.reference,
            'utilisateur': f"{acces.user.first_name} {acces.user.last_name}",
            'accorde_par': f"{acces.granted_by.first_name} {acces.granted_by.last_name}",
            'date': acces.created_at.strftime('%d/%m/%Y %H:%M'),
            'access_type': acces.access_type
        } for acces in historique_acces]

        return Response({
            'total_confidentiels': total_confidentiels,
            'acces_par_courrier': list(acces_par_courrier),
            'utilisateurs_avec_plus_acces': list(utilisateurs_acces),
            'imputations': {
                'total': total_imputations,
                'lecture': imputations_lecture,
                'edition': imputations_edition
            },
            'courriers_non_imputes': courriers_non_imputes,
            'historique_acces_recents': historique_data
        })

    @action(detail=False, methods=['get'])
    def statistiques_par_utilisateur(self, request):
        """
        Statistiques par utilisateur
        """
        user_id = request.query_params.get('user_id')
        
        if not user_id:
            user_id = request.user.id

        # Vérifier les permissions
        if str(request.user.id) != str(user_id):
            if not (hasattr(request.user, 'profile') and request.user.profile.role in ['ADMIN', 'DIRECTEUR']):
                return Response(
                    {'error': 'Accès non autorisé'}, 
                    status=status.HTTP_403_FORBIDDEN
                )

        try:
            utilisateur = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'Utilisateur non trouvé'}, 
                status=status.HTTP_404_NOT_FOUND
            )

        # Courriers imputés à l'utilisateur
        imputations = CourrierImputation.objects.filter(user=utilisateur)
        total_imputations = imputations.count()
        imputations_lecture = imputations.filter(access_type='view').count()
        imputations_edition = imputations.filter(access_type='edit').count()

        # Courriers confidentiels accessibles
        acces_confidentiels = CourrierAccess.objects.filter(user=utilisateur).count()

        # Diligences créées par l'utilisateur
        diligences_creees = Diligence.objects.filter(created_by=utilisateur).count()

        # Diligences assignées à l'utilisateur
        diligences_assignees = Diligence.objects.filter(
            Q(responsable=utilisateur) | Q(agents=utilisateur)
        ).distinct().count()

        # Courriers en attente d'imputation (pour ADMIN/DIRECTEUR)
        courriers_en_attente = 0
        if hasattr(utilisateur, 'profile') and utilisateur.profile.role in ['ADMIN', 'DIRECTEUR']:
            courriers_en_attente = Courrier.objects.filter(
                imputation_access__isnull=True,
                type_courrier='ordinaire'
            ).count()

        # Performance de traitement
        diligences_terminees = Diligence.objects.filter(
            responsable=utilisateur,
            statut='termine'
        )
        
        delai_moyen = diligences_terminees.aggregate(
            delai_moyen=Avg(
                ExpressionWrapper(
                    F('updated_at') - F('created_at'),
                    output_field=fields.DurationField()
                )
            )
        )['delai_moyen']
        
        delai_moyen_jours = delai_moyen.days if delai_moyen else 0

        return Response({
            'utilisateur': {
                'id': utilisateur.id,
                'username': utilisateur.username,
                'nom_complet': f"{utilisateur.first_name} {utilisateur.last_name}",
                'email': utilisateur.email
            },
            'imputations': {
                'total': total_imputations,
                'lecture': imputations_lecture,
                'edition': imputations_edition
            },
            'acces_confidentiels': acces_confidentiels,
            'diligences': {
                'creees': diligences_creees,
                'assignees': diligences_assignees,
                'terminees': diligences_terminees.count()
            },
            'courriers_en_attente_imputation': courriers_en_attente,
            'performance': {
                'delai_moyen_traitement_jours': delai_moyen_jours
            }
        })

    @action(detail=False, methods=['get'])
    def evolution_temporelle(self, request):
        """
        Évolution du nombre de courriers dans le temps
        """
        periode = request.query_params.get('periode', 'mois')  # jour, semaine, mois, annee
        annee = request.query_params.get('annee', timezone.now().year)

        queryset = Courrier.objects.filter(date_reception__year=annee)

        if periode == 'mois':
            evolution = queryset.extra(
                select={'mois': 'EXTRACT(month FROM date_reception)'}
            ).values('mois').annotate(
                count=Count('id'),
                ordinaires=Count('id', filter=Q(type_courrier='ordinaire')),
                confidentiels=Count('id', filter=Q(type_courrier='confidentiel'))
            ).order_by('mois')
        elif periode == 'semaine':
            evolution = queryset.extra(
                select={'semaine': 'EXTRACT(week FROM date_reception)'}
            ).values('semaine').annotate(
                count=Count('id'),
                ordinaires=Count('id', filter=Q(type_courrier='ordinaire')),
                confidentiels=Count('id', filter=Q(type_courrier='confidentiel'))
            ).order_by('semaine')
        else:
            evolution = queryset.extra(
                select={'jour': 'date_reception'}
            ).values('jour').annotate(
                count=Count('id'),
                ordinaires=Count('id', filter=Q(type_courrier='ordinaire')),
                confidentiels=Count('id', filter=Q(type_courrier='confidentiel'))
            ).order_by('jour')

        return Response({
            'periode': periode,
            'annee': annee,
            'evolution': list(evolution)
        })

    @action(detail=False, methods=['get'])
    def tableau_de_bord(self, request):
        """
        Tableau de bord complet avec toutes les statistiques essentielles
        """
        aujourd_hui = timezone.now().date()
        
        # Statistiques générales
        total_courriers = Courrier.objects.count()
        courriers_ordinaires = Courrier.objects.filter(type_courrier='ordinaire').count()
        courriers_confidentiels = Courrier.objects.filter(type_courrier='confidentiel').count()
        
        # Courriers récents
        courriers_aujourd_hui = Courrier.objects.filter(date_reception=aujourd_hui).count()
        courriers_semaine = Courrier.objects.filter(
            date_reception__gte=aujourd_hui - timedelta(days=7)
        ).count()
        courriers_mois = Courrier.objects.filter(
            date_reception__year=aujourd_hui.year,
            date_reception__month=aujourd_hui.month
        ).count()
        
        # Courriers par statut (si le modèle CourrierStatut est utilisé)
        courriers_nouveaux = Courrier.objects.filter(
            diligences__isnull=True
        ).count()
        
        courriers_en_cours = Courrier.objects.filter(
            diligences__statut__in=['en_attente', 'en_cours']
        ).distinct().count()
        
        courriers_traites = Courrier.objects.filter(
            diligences__statut='termine'
        ).distinct().count()
        
        # Top 5 catégories
        top_categories = Courrier.objects.values('categorie').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        # Top 5 services
        top_services = Courrier.objects.values(
            'service__nom', 'service_id'
        ).annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        # Imputations récentes
        imputations_recentes = CourrierImputation.objects.select_related(
            'courrier', 'user', 'granted_by'
        ).order_by('-created_at')[:10]
        
        imputations_data = [{
            'courrier_reference': imp.courrier.reference,
            'utilisateur': f"{imp.user.first_name} {imp.user.last_name}",
            'type_acces': imp.access_type,
            'date': imp.created_at.strftime('%d/%m/%Y %H:%M')
        } for imp in imputations_recentes]

        return Response({
            'statistiques_generales': {
                'total_courriers': total_courriers,
                'courriers_ordinaires': courriers_ordinaires,
                'courriers_confidentiels': courriers_confidentiels,
                'courriers_aujourd_hui': courriers_aujourd_hui,
                'courriers_semaine': courriers_semaine,
                'courriers_mois': courriers_mois
            },
            'statuts': {
                'nouveaux': courriers_nouveaux,
                'en_cours': courriers_en_cours,
                'traites': courriers_traites
            },
            'top_categories': list(top_categories),
            'top_services': list(top_services),
            'imputations_recentes': imputations_data
        })
