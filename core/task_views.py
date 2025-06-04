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
from .models import Projet, Tache, Commentaire, Fichier
from .serializers import ProjetSerializer, TacheSerializer, CommentaireSerializer, FichierSerializer

class ProjetViewSet(viewsets.ModelViewSet):
    queryset = Projet.objects.all().order_by('-createdAt')
    serializer_class = ProjetSerializer
    permission_classes = [permissions.IsAuthenticated]

class TacheViewSet(viewsets.ModelViewSet):
    queryset = Tache.objects.all().order_by('-createdAt')
    serializer_class = TacheSerializer
    permission_classes = [permissions.IsAuthenticated]

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
