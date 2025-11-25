# Guide d'Utilisation - Imputation des Courriers

## Vue d'ensemble

La fonctionnalité d'imputation permet aux administrateurs et directeurs d'assigner des courriers (ordinaires et confidentiels) à des utilisateurs spécifiques avec des droits de lecture ou d'édition.

## Modifications Apportées

### 1. Extension de la Fonctionnalité

L'imputation, initialement limitée aux **courriers confidentiels**, est maintenant disponible pour :
- ✅ **Courriers ordinaires en arrivée**
- ✅ **Courriers ordinaires en départ**
- ✅ **Courriers confidentiels en arrivée**
- ✅ **Courriers confidentiels en départ**

### 2. Permissions

Seuls les utilisateurs avec les rôles suivants peuvent créer/supprimer des imputations :
- **ADMIN** : Accès complet à toutes les imputations
- **DIRECTEUR** : Accès complet à toutes les imputations

Les autres utilisateurs peuvent uniquement consulter leurs propres imputations.

## API Endpoints

### 1. Imputer un Courrier

**Endpoint :** `POST /api/courriers/{id}/imputer_courrier/`

**Permissions :** ADMIN, DIRECTEUR

**Body :**
```json
{
  "user_id": 5,
  "access_type": "view"  // ou "edit"
}
```

**Réponse :**
```json
{
  "message": "Courrier ordinaire imputé avec succès à Jean Dupont",
  "imputation_id": 12,
  "courrier_type": "ordinaire",
  "sens": "arrivee"
}
```

### 2. Lister les Imputations d'un Courrier

**Endpoint :** `GET /api/courriers/{id}/imputations/`

**Permissions :** Authentifié

**Réponse :**
```json
[
  {
    "id": 12,
    "courrier": 45,
    "courrier_details": {
      "id": 45,
      "reference": "COUR-2025-001",
      "objet": "Demande de subvention",
      "expediteur": "Ministère des Finances",
      "destinataire": "Direction Générale",
      "type_courrier": "ordinaire",
      "sens": "arrivee",
      "date_reception": "2025-11-25",
      "categorie": "Demande"
    },
    "user": 5,
    "user_details": {
      "id": 5,
      "username": "jdupont",
      "email": "jdupont@example.com",
      "first_name": "Jean",
      "last_name": "Dupont"
    },
    "access_type": "view",
    "granted_by": 1,
    "granted_by_details": {
      "id": 1,
      "username": "admin",
      "email": "admin@example.com",
      "first_name": "Admin",
      "last_name": "System"
    },
    "created_at": "2025-11-25T18:30:00Z"
  }
]
```

### 3. Supprimer une Imputation

**Endpoint :** `DELETE /api/courriers/{id}/imputations/{imputation_id}/`

**Permissions :** ADMIN, DIRECTEUR

**Réponse :**
```json
{
  "message": "Imputation supprimée avec succès"
}
```

### 4. Lister Toutes les Imputations

**Endpoint :** `GET /api/courrier-imputation/`

**Permissions :** Authentifié

**Filtres disponibles :**
- `?courrier={id}` - Filtrer par courrier
- `?type_courrier=ordinaire` - Filtrer par type (ordinaire/confidentiel)
- `?sens=arrivee` - Filtrer par sens (arrivee/depart)
- `?user={id}` - Filtrer par utilisateur imputé
- `?access_type=view` - Filtrer par type d'accès (view/edit)

**Exemples :**
```bash
# Toutes les imputations de courriers ordinaires en arrivée
GET /api/courrier-imputation/?type_courrier=ordinaire&sens=arrivee

# Toutes les imputations d'un utilisateur spécifique
GET /api/courrier-imputation/?user=5

# Toutes les imputations avec droit d'édition
GET /api/courrier-imputation/?access_type=edit
```

### 5. Créer une Imputation (Alternative)

**Endpoint :** `POST /api/courrier-imputation/`

**Permissions :** ADMIN, DIRECTEUR

**Body :**
```json
{
  "courrier": 45,
  "user": 5,
  "access_type": "edit"
}
```

### 6. Supprimer une Imputation (Alternative)

**Endpoint :** `DELETE /api/courrier-imputation/{id}/`

**Permissions :** ADMIN, DIRECTEUR

## Types d'Accès

### View (Lecture)
- L'utilisateur peut **consulter** le courrier
- Accès en lecture seule

### Edit (Édition)
- L'utilisateur peut **consulter et modifier** le courrier
- Accès complet

## Logique de Filtrage des Courriers

### Pour les ADMIN
- Accès à **tous les courriers** (ordinaires et confidentiels)

### Pour les autres utilisateurs
- **Courriers ordinaires** : Accès à tous (avec ou sans imputation)
- **Courriers confidentiels** : Accès uniquement si :
  - Imputation accordée (CourrierImputation)
  - OU Accès explicite accordé (CourrierAccess)

## Exemples d'Utilisation

### Exemple 1 : Imputer un courrier ordinaire en arrivée

```javascript
// Imputer le courrier #45 à l'utilisateur #5 avec droit de lecture
fetch('/api/courriers/45/imputer_courrier/', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_TOKEN',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    user_id: 5,
    access_type: 'view'
  })
})
```

### Exemple 2 : Lister les imputations d'un courrier

```javascript
// Récupérer toutes les imputations du courrier #45
fetch('/api/courriers/45/imputations/', {
  method: 'GET',
  headers: {
    'Authorization': 'Bearer YOUR_TOKEN'
  }
})
```

### Exemple 3 : Filtrer les imputations

```javascript
// Récupérer toutes les imputations de courriers ordinaires en départ
fetch('/api/courrier-imputation/?type_courrier=ordinaire&sens=depart', {
  method: 'GET',
  headers: {
    'Authorization': 'Bearer YOUR_TOKEN'
  }
})
```

## Cas d'Usage

### 1. Courrier Ordinaire en Arrivée
Un courrier arrive de l'extérieur. Le directeur l'impute à un agent pour traitement.

```json
POST /api/courriers/45/imputer_courrier/
{
  "user_id": 5,
  "access_type": "edit"
}
```

### 2. Courrier Ordinaire en Départ
Un courrier doit être envoyé. Le directeur l'impute à un agent pour rédaction.

```json
POST /api/courriers/46/imputer_courrier/
{
  "user_id": 6,
  "access_type": "edit"
}
```

### 3. Courrier Confidentiel
Un courrier confidentiel nécessite une attention particulière. Le directeur l'impute avec droit de lecture uniquement.

```json
POST /api/courriers/47/imputer_courrier/
{
  "user_id": 7,
  "access_type": "view"
}
```

## Modèle de Données

### CourrierImputation

| Champ | Type | Description |
|-------|------|-------------|
| id | Integer | Identifiant unique |
| courrier | ForeignKey | Référence au courrier |
| user | ForeignKey | Utilisateur imputé |
| access_type | String | Type d'accès (view/edit) |
| granted_by | ForeignKey | Utilisateur qui a accordé l'imputation |
| created_at | DateTime | Date de création |

**Contrainte :** `unique_together = ('courrier', 'user', 'access_type')`

## Notes Importantes

1. **Unicité** : Un utilisateur ne peut avoir qu'une seule imputation par type d'accès pour un courrier donné
2. **Mise à jour** : Si une imputation existe déjà, elle est mise à jour avec le nouveau `granted_by`
3. **Sécurité** : Les courriers confidentiels restent protégés - seuls les utilisateurs avec imputation ou accès explicite peuvent les voir
4. **Audit** : Toutes les imputations sont tracées avec l'utilisateur qui les a accordées et la date

## Migration depuis l'Ancien Système

Aucune migration de base de données n'est nécessaire. Le modèle `CourrierImputation` existant supporte déjà tous les types de courriers. Seules les restrictions au niveau des vues ont été supprimées.

## Tests

Pour tester la fonctionnalité :

```bash
# 1. Créer un courrier ordinaire
POST /api/courriers/
{
  "reference": "TEST-001",
  "expediteur": "Test Sender",
  "objet": "Test Object",
  "date_reception": "2025-11-25",
  "type_courrier": "ordinaire",
  "sens": "arrivee",
  "categorie": "Demande"
}

# 2. Imputer le courrier
POST /api/courriers/{id}/imputer_courrier/
{
  "user_id": 5,
  "access_type": "view"
}

# 3. Vérifier l'imputation
GET /api/courriers/{id}/imputations/
```
