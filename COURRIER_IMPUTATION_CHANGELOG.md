# Changelog - Extension de l'Imputation aux Courriers Ordinaires

## Date : 25 Novembre 2025

## Résumé des Modifications

Extension de la fonctionnalité d'imputation pour inclure les **courriers ordinaires** (arrivée et départ) en plus des courriers confidentiels.

---

## Fichiers Modifiés

### 1. `core/models.py`

**Ligne 250 :** Mise à jour de la description du modèle

```python
# AVANT
"""Modèle pour l'imputation des courriers confidentiels basé sur ImputationAccess"""

# APRÈS
"""Modèle pour l'imputation des courriers (ordinaires et confidentiels)"""
```

**Impact :** Documentation du modèle mise à jour pour refléter le nouveau scope.

---

### 2. `core/views.py`

#### A. Méthode `imputer_courrier` (Lignes 801-850)

**Modifications :**
- ✅ Suppression de la restriction limitant l'imputation aux courriers confidentiels
- ✅ Ajout du type de courrier et du sens dans la réponse
- ✅ Message de succès dynamique selon le type de courrier

```python
# AVANT
if courrier.type_courrier != 'confidentiel':
    return Response(
        {'error': 'Seuls les courriers confidentiels peuvent être imputés'}, 
        status=status.HTTP_400_BAD_REQUEST
    )

# APRÈS
# Restriction supprimée - tous les types de courriers peuvent être imputés
```

**Nouvelle réponse :**
```json
{
  "message": "Courrier ordinaire imputé avec succès à Jean Dupont",
  "imputation_id": 12,
  "courrier_type": "ordinaire",
  "sens": "arrivee"
}
```

#### B. Nouvelles Actions Ajoutées (Lignes 852-885)

**1. Action `imputations` :**
```python
@action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
def imputations(self, request, pk=None):
    """Lister toutes les imputations d'un courrier"""
```

**Endpoint :** `GET /api/courriers/{id}/imputations/`

**2. Action `delete_imputation` :**
```python
@action(detail=True, methods=['delete'], permission_classes=[permissions.IsAuthenticated], 
        url_path='imputations/(?P<imputation_id>[^/.]+)')
def delete_imputation(self, request, pk=None, imputation_id=None):
    """Supprimer une imputation spécifique d'un courrier"""
```

**Endpoint :** `DELETE /api/courriers/{id}/imputations/{imputation_id}/`

#### C. Méthode `get_queryset` du CourrierViewSet (Lignes 714-751)

**Modifications :**
- ✅ Amélioration de la logique de filtrage
- ✅ Tous les courriers ordinaires sont accessibles (avec ou sans imputation)
- ✅ Les courriers confidentiels nécessitent toujours une imputation ou un accès explicite

```python
# Nouvelle logique
# - Tous les courriers ordinaires (avec ou sans imputation)
# - Courriers confidentiels avec accès ou imputation
queryset = queryset.filter(
    models.Q(type_courrier='ordinaire') |
    models.Q(type_courrier='confidentiel', id__in=all_confidential_accessible_ids)
)
```

#### D. CourrierImputationViewSet (Lignes 2061-2103)

**Modifications :**
- ✅ Mise à jour de la description du ViewSet
- ✅ Ajout de filtres avancés dans `get_queryset`

**Nouveaux filtres disponibles :**
- `?courrier={id}` - Filtrer par courrier
- `?type_courrier=ordinaire` - Filtrer par type
- `?sens=arrivee` - Filtrer par sens
- `?user={id}` - Filtrer par utilisateur
- `?access_type=view` - Filtrer par type d'accès

---

### 3. `core/serializers.py`

#### Méthode `get_courrier_details` (Lignes 759-770)

**Modifications :** Ajout de champs supplémentaires dans les détails du courrier

```python
# AVANT
return {
    'id': obj.courrier.id,
    'reference': obj.courrier.reference,
    'objet': obj.courrier.objet,
    'type_courrier': obj.courrier.type_courrier
}

# APRÈS
return {
    'id': obj.courrier.id,
    'reference': obj.courrier.reference,
    'objet': obj.courrier.objet,
    'expediteur': obj.courrier.expediteur,
    'destinataire': obj.courrier.destinataire,
    'type_courrier': obj.courrier.type_courrier,
    'sens': obj.courrier.sens,
    'date_reception': obj.courrier.date_reception,
    'categorie': obj.courrier.categorie
}
```

**Impact :** Plus d'informations disponibles lors de la consultation des imputations.

---

## Nouveaux Endpoints

| Méthode | Endpoint | Description | Permissions |
|---------|----------|-------------|-------------|
| POST | `/api/courriers/{id}/imputer_courrier/` | Imputer un courrier | ADMIN, DIRECTEUR |
| GET | `/api/courriers/{id}/imputations/` | Lister les imputations d'un courrier | Authentifié |
| DELETE | `/api/courriers/{id}/imputations/{imputation_id}/` | Supprimer une imputation | ADMIN, DIRECTEUR |
| GET | `/api/courrier-imputation/` | Lister toutes les imputations (avec filtres) | Authentifié |
| POST | `/api/courrier-imputation/` | Créer une imputation | ADMIN, DIRECTEUR |
| DELETE | `/api/courrier-imputation/{id}/` | Supprimer une imputation | ADMIN, DIRECTEUR |

---

## Fonctionnalités Ajoutées

### 1. Imputation sur Courriers Ordinaires
- ✅ Courriers ordinaires en **arrivée**
- ✅ Courriers ordinaires en **départ**
- ✅ Deux types d'accès : **view** (lecture) et **edit** (édition)

### 2. Gestion Avancée des Imputations
- ✅ Lister les imputations par courrier
- ✅ Supprimer une imputation spécifique
- ✅ Filtrage multi-critères des imputations

### 3. Informations Enrichies
- ✅ Détails complets du courrier dans les imputations
- ✅ Informations sur l'utilisateur imputé
- ✅ Informations sur l'utilisateur qui a accordé l'imputation
- ✅ Type de courrier et sens dans les réponses

---

## Sécurité et Permissions

### Permissions Maintenues
- ✅ Seuls **ADMIN** et **DIRECTEUR** peuvent créer/supprimer des imputations
- ✅ Les utilisateurs ne voient que leurs propres imputations (sauf ADMIN/DIRECTEUR)
- ✅ Les courriers confidentiels restent protégés (accès uniquement avec imputation ou permission)

### Nouvelles Règles d'Accès
- ✅ **Courriers ordinaires** : Accessibles à tous les utilisateurs authentifiés
- ✅ **Courriers confidentiels** : Accessibles uniquement avec imputation ou accès explicite
- ✅ **Imputations** : Traçabilité complète (qui a imputé, quand)

---

## Compatibilité

### Rétrocompatibilité
- ✅ **100% compatible** avec l'ancien système
- ✅ Aucune migration de base de données nécessaire
- ✅ Les imputations existantes sur courriers confidentiels continuent de fonctionner
- ✅ Aucun changement dans le modèle de données

### Base de Données
- ✅ Aucune modification de schéma requise
- ✅ Le modèle `CourrierImputation` existant supporte déjà tous les types de courriers
- ✅ Contrainte `unique_together` maintenue : `('courrier', 'user', 'access_type')`

---

## Tests Recommandés

### 1. Test d'Imputation sur Courrier Ordinaire en Arrivée
```bash
POST /api/courriers/{id}/imputer_courrier/
{
  "user_id": 5,
  "access_type": "view"
}
```

### 2. Test d'Imputation sur Courrier Ordinaire en Départ
```bash
POST /api/courriers/{id}/imputer_courrier/
{
  "user_id": 6,
  "access_type": "edit"
}
```

### 3. Test de Filtrage
```bash
GET /api/courrier-imputation/?type_courrier=ordinaire&sens=arrivee
```

### 4. Test de Suppression
```bash
DELETE /api/courriers/{id}/imputations/{imputation_id}/
```

---

## Documentation

Fichiers de documentation créés :
- ✅ `COURRIER_IMPUTATION_GUIDE.md` - Guide complet d'utilisation
- ✅ `COURRIER_IMPUTATION_CHANGELOG.md` - Ce fichier

---

## Prochaines Étapes Recommandées

### Court Terme
1. Tester les endpoints avec différents rôles utilisateurs
2. Vérifier la sécurité des courriers confidentiels
3. Tester les filtres de recherche

### Moyen Terme
1. Ajouter des notifications lors de l'imputation
2. Créer un dashboard des imputations
3. Ajouter des statistiques sur les imputations

### Long Terme
1. Historique des modifications d'imputation
2. Imputation en masse
3. Workflow de validation des imputations

---

## Notes Importantes

⚠️ **Sécurité :** Les courriers confidentiels restent protégés. Seuls les utilisateurs avec imputation ou accès explicite peuvent les consulter.

✅ **Performance :** Les requêtes utilisent `select_related` pour optimiser les performances.

📊 **Audit :** Toutes les imputations sont tracées avec `granted_by` et `created_at`.

🔄 **Mise à jour :** Si une imputation existe déjà, elle est mise à jour avec le nouveau `granted_by`.

---

## Support

Pour toute question ou problème, consulter :
- `COURRIER_IMPUTATION_GUIDE.md` pour l'utilisation
- Les logs du serveur pour le débogage
- Les tests unitaires pour les exemples d'utilisation
