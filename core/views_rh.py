from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.db.models import Q, Count
from django.utils import timezone
from .models import (
    FicheAgent, MissionRH, EvaluationRH, FormationRH,
    InscriptionFormationRH, DocumentRH, DemandeAttestation
)
from .serializers_rh import (
    FicheAgentSerializer, MissionRHSerializer, EvaluationRHSerializer,
    FormationRHSerializer, InscriptionFormationRHSerializer, DocumentRHSerializer,
    DemandeAttestationSerializer
)


def _get_site_id(request):
    """Effective site_id for filtering: admin reads X-Site-ID header, others use own site."""
    profile = getattr(request.user, 'profile', None)
    role = getattr(profile, 'role', None) if profile else None
    if role == 'ADMIN':
        raw = request.headers.get('X-Site-ID') or request.query_params.get('site_id')
        if raw:
            try:
                return int(raw)
            except (ValueError, TypeError):
                pass
        return None
    return getattr(profile, 'site_id', None)


class FicheAgentViewSet(viewsets.ModelViewSet):
    queryset = FicheAgent.objects.select_related('user', 'direction', 'service', 'sous_direction').all()
    serializer_class = FicheAgentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['nom', 'prenoms', 'matricule', 'grade', 'emploi', 'fonction']

    def get_queryset(self):
        qs = super().get_queryset()
        site_id = _get_site_id(self.request)
        if site_id:
            qs = qs.filter(user__profile__site_id=site_id)
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

        if role in ['ADMIN', 'DIRECTEUR', 'SOUS_DIRECTEUR', 'CHEF_SERVICE', 'SUPERIEUR']:
            site_id = _get_site_id(self.request)
            if site_id:
                qs = qs.filter(agent__profile__site_id=site_id)
        else:
            qs = qs.filter(agent=user)

        statut = self.request.query_params.get('statut')
        agent = self.request.query_params.get('agent')
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
        site_id = _get_site_id(self.request)
        if site_id:
            qs = qs.filter(agent__profile__site_id=site_id)
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
        site_id = _get_site_id(self.request)
        if site_id:
            qs = qs.filter(agent__profile__site_id=site_id)
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
        site_id = _get_site_id(self.request)
        if site_id:
            qs = qs.filter(agent__profile__site_id=site_id)
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


class DemandeAttestationViewSet(viewsets.ModelViewSet):
    serializer_class = DemandeAttestationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        role = getattr(getattr(user, 'profile', None), 'role', '')
        qs = DemandeAttestation.objects.select_related(
            'agent', 'agent__profile', 'responsable_rh'
        ).all()
        if role not in ['ADMIN', 'DIRECTEUR', 'SUPERIEUR']:
            qs = qs.filter(agent=user)
        else:
            site_id = _get_site_id(self.request)
            if site_id:
                qs = qs.filter(agent__profile__site_id=site_id)
        statut = self.request.query_params.get('statut')
        type_att = self.request.query_params.get('type_attestation')
        if statut:
            qs = qs.filter(statut=statut)
        if type_att:
            qs = qs.filter(type_attestation=type_att)
        return qs

    def perform_create(self, serializer):
        instance = serializer.save(agent=self.request.user)
        instance.generer_numero()

    @action(detail=True, methods=['post'])
    def approuver(self, request, pk=None):
        demande = self.get_object()
        if demande.statut != 'en_attente':
            return Response({'error': 'Seules les demandes en attente peuvent être approuvées'}, status=400)
        demande.statut = 'en_cours'
        demande.responsable_rh = request.user
        demande.commentaire_rh = request.data.get('commentaire_rh', '')
        demande.save()
        return Response(DemandeAttestationSerializer(demande, context={'request': request}).data)

    @action(detail=True, methods=['post'])
    def rejeter(self, request, pk=None):
        demande = self.get_object()
        if demande.statut not in ['en_attente', 'en_cours']:
            return Response({'error': 'Cette demande ne peut plus être rejetée'}, status=400)
        demande.statut = 'rejetee'
        demande.responsable_rh = request.user
        demande.commentaire_rh = request.data.get('commentaire_rh', '')
        demande.save()
        return Response(DemandeAttestationSerializer(demande, context={'request': request}).data)

    @action(detail=True, methods=['post'])
    def terminer(self, request, pk=None):
        demande = self.get_object()
        demande.statut = 'terminee'
        demande.save()
        return Response(DemandeAttestationSerializer(demande, context={'request': request}).data)

    @action(detail=True, methods=['post'])
    def annuler(self, request, pk=None):
        demande = self.get_object()
        if demande.agent != request.user:
            return Response({'error': 'Non autorisé'}, status=403)
        if demande.statut not in ['en_attente']:
            return Response({'error': "Impossible d'annuler cette demande"}, status=400)
        demande.statut = 'annulee'
        demande.save()
        return Response(DemandeAttestationSerializer(demande, context={'request': request}).data)

    @action(detail=True, methods=['post'])
    def generer_pdf(self, request, pk=None):
        from .pdf_utils import generate_attestation_pdf
        from django.core.files.base import ContentFile
        demande = self.get_object()
        if demande.statut not in ['en_cours', 'traitee']:
            return Response({'error': 'La demande doit être en cours pour générer le PDF'}, status=400)
        try:
            pdf_bytes = generate_attestation_pdf(demande)
            filename = f"attestation_{demande.numero_attestation or demande.pk}.pdf"
            demande.pdf_file.save(filename, ContentFile(pdf_bytes), save=True)
            demande.statut = 'traitee'
            demande.responsable_rh = request.user
            demande.save()
            return Response({
                'pdf_url': request.build_absolute_uri(demande.pdf_file.url),
                'statut': demande.statut,
                'numero': demande.numero_attestation,
            })
        except Exception as e:
            return Response({'error': str(e)}, status=500)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        role = getattr(getattr(request.user, 'profile', None), 'role', '')
        qs = DemandeAttestation.objects.all()
        if role not in ['ADMIN', 'DIRECTEUR', 'SUPERIEUR']:
            qs = qs.filter(agent=request.user)
        else:
            site_id = _get_site_id(request)
            if site_id:
                qs = qs.filter(agent__profile__site_id=site_id)
        return Response({
            'total': qs.count(),
            'en_attente': qs.filter(statut='en_attente').count(),
            'en_cours': qs.filter(statut='en_cours').count(),
            'traitees': qs.filter(statut='traitee').count(),
            'terminees': qs.filter(statut='terminee').count(),
            'rejetees': qs.filter(statut='rejetee').count(),
        })
