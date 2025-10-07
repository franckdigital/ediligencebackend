# --- VIEWSETS SUIVI PROJETS & TACHES ---

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import CommentaireSerializer
from .models import Tache, Commentaire

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def tache_commentaires(request, pk):
    """GET: Liste des commentaires d'une tâche. POST: Ajoute un commentaire à la tâche."""
    try:
        tache = Tache.objects.get(pk=pk)
    except Tache.DoesNotExist:
        return Response({'detail': 'Tâche introuvable.'}, status=404)
    if request.method == 'GET':
        commentaires = Commentaire.objects.filter(tache=tache).order_by('createdAt')
        serializer = CommentaireSerializer(commentaires, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        contenu = request.data.get('contenu')
        if not contenu:
            return Response({'detail': 'Le contenu est requis.'}, status=400)
        commentaire = Commentaire.objects.create(
            contenu=contenu,
            auteur=request.user,
            tache=tache
        )
        # Historique : ajout de commentaire
        from .models import TacheHistorique
        TacheHistorique.objects.create(
            tache=tache,
            utilisateur=request.user,
            action='ajout commentaire',
            details=contenu
        )
        serializer = CommentaireSerializer(commentaire)
        return Response(serializer.data, status=201)

@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def tache_commentaire_detail(request, pk, comment_id):
    """PATCH: Modifie un commentaire. DELETE: Supprime un commentaire."""
    try:
        commentaire = Commentaire.objects.get(pk=comment_id, tache__pk=pk)
    except Commentaire.DoesNotExist:
        return Response({'detail': 'Commentaire introuvable.'}, status=404)
    if commentaire.auteur != request.user:
        return Response({'detail': 'Non autorisé.'}, status=403)
    if request.method == 'PATCH':
        contenu = request.data.get('contenu')
        if not contenu:
            return Response({'detail': 'Le contenu est requis.'}, status=400)
        commentaire.contenu = contenu
        commentaire.save()
        serializer = CommentaireSerializer(commentaire)
        return Response(serializer.data)
    elif request.method == 'DELETE':
        commentaire.delete()
        return Response(status=204)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def tache_historique(request, pk):
    """Retourne l'historique d'une tâche"""
    from .models import TacheHistorique
    from .serializers import TacheHistoriqueSerializer
    historiques = TacheHistorique.objects.filter(tache_id=pk).order_by('-date')
    serializer = TacheHistoriqueSerializer(historiques, many=True)
    return Response(serializer.data)


from rest_framework import viewsets, permissions
from .models import Projet, Tache, Commentaire, Fichier, Activite, Domaine
from .serializers import ProjetSerializer, TacheSerializer, CommentaireSerializer, FichierSerializer, ActiviteSerializer, DomaineSerializer

class ActiviteViewSet(viewsets.ModelViewSet):
    queryset = Activite.objects.all().order_by('-created_at')
    serializer_class = ActiviteSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        
        # Créer une notification pour l'agent responsable
        if response.status_code == 201:
            try:
                from .models import DiligenceNotification
                activite = Activite.objects.get(id=response.data['id'])
                
                if activite.responsable_principal:
                    DiligenceNotification.objects.create(
                        user=activite.responsable_principal,
                        diligence=None,  # Pas de diligence associée
                        type_notification='nouvelle_diligence',
                        message=f'Nouvelle activité créée dont vous êtes responsable: {activite.nom} - {activite.description[:50] if activite.description else ""}...'
                    )
                    print(f"Notification d'activité créée pour {activite.responsable_principal.username}")
            except Exception as e:
                print(f"Erreur lors de la création de la notification d'activité: {e}")
        
        return response

class DomaineViewSet(viewsets.ModelViewSet):
    queryset = Domaine.objects.all().order_by('-created_at')
    serializer_class = DomaineSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        
        # Créer une notification pour le superviseur du domaine
        if response.status_code == 201:
            try:
                from .models import DiligenceNotification
                domaine = Domaine.objects.get(id=response.data['id'])
                
                if domaine.superviseur:
                    DiligenceNotification.objects.create(
                        user=domaine.superviseur,
                        diligence=None,  # Pas de diligence associée
                        type_notification='nouvelle_diligence',
                        message=f'Nouveau domaine créé dont vous êtes superviseur: {domaine.nom} (Activité: {domaine.activite.type})'
                    )
                    print(f"Notification de domaine créée pour {domaine.superviseur.username}")
            except Exception as e:
                print(f"Erreur lors de la création de la notification de domaine: {e}")
        
        return response

class ProjetViewSet(viewsets.ModelViewSet):
    queryset = Projet.objects.all().order_by('-createdAt')
    serializer_class = ProjetSerializer
    permission_classes = [permissions.IsAuthenticated]

class TacheViewSet(viewsets.ModelViewSet):
    queryset = Tache.objects.all().order_by('-createdAt')
    serializer_class = TacheSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        
        # Créer des notifications pour les agents assignés à la tâche
        if response.status_code == 201:
            try:
                from .models import DiligenceNotification
                tache = Tache.objects.get(id=response.data['id'])
                
                # Notifier tous les agents assignés
                for agent in tache.agents.all():
                    DiligenceNotification.objects.create(
                        user=agent,
                        diligence=None,  # Pas de diligence associée
                        type_notification='nouvelle_diligence',
                        message=f'Nouvelle tâche créée qui vous est assignée: {tache.titre} (Domaine: {tache.domaine.nom if tache.domaine else "N/A"})'
                    )
                    print(f"Notification de tâche créée pour {agent.username}")
            except Exception as e:
                print(f"Erreur lors de la création des notifications de tâche: {e}")
        
        return response

    def update(self, request, *args, **kwargs):
        # On récupère l'ancienne instance pour détecter les changements
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        old_data = {field: getattr(instance, field) for field in request.data.keys() if hasattr(instance, field)}
        response = super().update(request, *args, **kwargs)
        # Après modification, journalise les changements
        updated_instance = self.get_object()
        changed_fields = {}
        for field in request.data.keys():
            old = old_data.get(field)
            new = getattr(updated_instance, field, None)
            if old != new:
                changed_fields[field] = {'old': old, 'new': new}
        if changed_fields:
            from .models import TacheHistorique
            import json
            TacheHistorique.objects.create(
                tache=updated_instance,
                utilisateur=request.user,
                action='modification',
                details=json.dumps(changed_fields, ensure_ascii=False)
            )
        return response

class CommentaireViewSet(viewsets.ModelViewSet):
    queryset = Commentaire.objects.all().order_by('-createdAt')
    serializer_class = CommentaireSerializer
    permission_classes = [permissions.IsAuthenticated]

class FichierViewSet(viewsets.ModelViewSet):
    queryset = Fichier.objects.all().order_by('-id')
    serializer_class = FichierSerializer
    permission_classes = [permissions.IsAuthenticated]
