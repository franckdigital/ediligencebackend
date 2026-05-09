from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.db.models import Q, Count
from django.utils import timezone
from .models import (
    FicheAgent, MissionRH, EvaluationRH, FormationRH,
    InscriptionFormationRH, DocumentRH
)
from .serializers_rh import (
    FicheAgentSerializer, MissionRHSerializer, EvaluationRHSerializer,
    FormationRHSerializer, InscriptionFormationRHSerializer, DocumentRHSerializer
)


class FicheAgentViewSet(viewsets.ModelViewSet):
    queryset = FicheAgent.objects.select_related('user', 'direction', 'service', 'sous_direction').all()
    serializer_class = FicheAgentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['nom', 'prenoms', 'matricule', 'grade', 'emploi', 'fonction']

    def get_queryset(self):
        qs = super().get_queryset()
        statut = self.request.query_params.get('statut')
        direction = self.request.query_params.get('direction')
        service = self.request.query_params.get('service')
        if statut:
            qs = qs.filter(statut=statut)
        if direction:
            qs = qs.filter(direction_id=direction)
        if service:
            qs = qs.filter(service_id=service)
        return qs

    @action(detail=False, methods=['get'])
    def stats(self, request):
        qs = FicheAgent.objects.all()
        return Response({
            'total': qs.count(),
            'actifs': qs.filter(statut='actif').count(),
            'suspendus': qs.filter(statut='suspendu').count(),
            'retraites': qs.filter(statut='retraite').count(),
            'par_direction': list(
                qs.values('direction__nom').annotate(count=Count('id'))
            ),
        })


class MissionRHViewSet(viewsets.ModelViewSet):
    queryset = MissionRH.objects.select_related('agent', 'valideur').all()
    serializer_class = MissionRHSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['objet', 'destination', 'ordre_mission_num']

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        role = ''
        if hasattr(user, 'profile'):
            role = getattr(user.profile, 'role', '') or ''
        statut = self.request.query_params.get('statut')
        agent = self.request.query_params.get('agent')

        if role in ['ADMIN', 'DIRECTEUR', 'SOUS_DIRECTEUR', 'CHEF_SERVICE', 'SUPERIEUR']:
            pass  # full access
        else:
            qs = qs.filter(agent=user)

        if statut:
            qs = qs.filter(statut=statut)
        if agent:
            qs = qs.filter(agent_id=agent)
        return qs.order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save()

    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        mission = self.get_object()
        mission.statut = 'validee'
        mission.valideur = request.user
        mission.date_validation = timezone.now()
        mission.save()
        return Response({'status': 'Mission validée'})

    @action(detail=True, methods=['post'])
    def rejeter(self, request, pk=None):
        mission = self.get_object()
        mission.statut = 'rejetee'
        mission.motif_rejet = request.data.get('motif', '')
        mission.save()
        return Response({'status': 'Mission rejetée'})

    @action(detail=True, methods=['post'])
    def soumettre_rapport(self, request, pk=None):
        mission = self.get_object()
        mission.rapport = request.data.get('rapport', '')
        mission.statut = 'terminee'
        if 'rapport_fichier' in request.FILES:
            mission.rapport_fichier = request.FILES['rapport_fichier']
        mission.save()
        return Response({'status': 'Rapport soumis'})

    @action(detail=False, methods=['get'])
    def stats(self, request):
        qs = MissionRH.objects.all()
        return Response({
            'total': qs.count(),
            'demandes': qs.filter(statut='demande').count(),
            'en_cours': qs.filter(statut='en_cours').count(),
            'terminees': qs.filter(statut='terminee').count(),
            'validees': qs.filter(statut='validee').count(),
        })


class EvaluationRHViewSet(viewsets.ModelViewSet):
    queryset = EvaluationRH.objects.select_related('agent', 'evaluateur').all()
    serializer_class = EvaluationRHSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        annee = self.request.query_params.get('annee')
        agent = self.request.query_params.get('agent')
        if annee:
            qs = qs.filter(annee=annee)
        if agent:
            qs = qs.filter(agent_id=agent)
        return qs

    def perform_create(self, serializer):
        serializer.save(evaluateur=self.request.user)


class FormationRHViewSet(viewsets.ModelViewSet):
    queryset = FormationRH.objects.prefetch_related('inscriptions').all()
    serializer_class = FormationRHSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def inscrire_agent(self, request, pk=None):
        formation = self.get_object()
        agent_id = request.data.get('agent_id')
        try:
            agent = User.objects.get(id=agent_id)
            insc, created = InscriptionFormationRH.objects.get_or_create(
                formation=formation, agent=agent
            )
            return Response({'status': 'Inscrit' if created else 'Déjà inscrit'})
        except User.DoesNotExist:
            return Response({'error': 'Agent non trouvé'}, status=400)


class InscriptionFormationRHViewSet(viewsets.ModelViewSet):
    queryset = InscriptionFormationRH.objects.select_related('agent', 'formation').all()
    serializer_class = InscriptionFormationRHSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        formation = self.request.query_params.get('formation')
        agent = self.request.query_params.get('agent')
        if formation:
            qs = qs.filter(formation_id=formation)
        if agent:
            qs = qs.filter(agent_id=agent)
        return qs


class DocumentRHViewSet(viewsets.ModelViewSet):
    queryset = DocumentRH.objects.select_related('agent', 'created_by').all()
    serializer_class = DocumentRHSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        agent = self.request.query_params.get('agent')
        type_doc = self.request.query_params.get('type_document')
        if agent:
            qs = qs.filter(agent_id=agent)
        if type_doc:
            qs = qs.filter(type_document=type_doc)
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        qs = DocumentRH.objects.all()
        return Response({
            'total': qs.count(),
            'par_type': list(qs.values('type_document').annotate(count=Count('id'))),
        })
