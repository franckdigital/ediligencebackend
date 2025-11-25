# Exemples d'Utilisation de l'API - Imputation des Courriers

## Configuration

**Base URL :** `http://votre-serveur/api/`

**Headers requis :**
```json
{
  "Authorization": "Bearer YOUR_JWT_TOKEN",
  "Content-Type": "application/json"
}
```

---

## 1. Imputer un Courrier Ordinaire en Arrivée

### Requête
```bash
curl -X POST http://localhost:8000/api/courriers/45/imputer_courrier/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 5,
    "access_type": "view"
  }'
```

### Réponse (200 OK)
```json
{
  "message": "Courrier ordinaire imputé avec succès à Jean Dupont",
  "imputation_id": 12,
  "courrier_type": "ordinaire",
  "sens": "arrivee"
}
```

---

## 2. Imputer un Courrier Ordinaire en Départ avec Droit d'Édition

### Requête
```bash
curl -X POST http://localhost:8000/api/courriers/46/imputer_courrier/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 6,
    "access_type": "edit"
  }'
```

### Réponse (201 CREATED)
```json
{
  "message": "Courrier ordinaire imputé avec succès à Marie Martin",
  "imputation_id": 13,
  "courrier_type": "ordinaire",
  "sens": "depart"
}
```

---

## 3. Lister les Imputations d'un Courrier

### Requête
```bash
curl -X GET http://localhost:8000/api/courriers/45/imputations/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Réponse (200 OK)
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
  },
  {
    "id": 14,
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
    "user": 7,
    "user_details": {
      "id": 7,
      "username": "pdurand",
      "email": "pdurand@example.com",
      "first_name": "Pierre",
      "last_name": "Durand"
    },
    "access_type": "edit",
    "granted_by": 1,
    "granted_by_details": {
      "id": 1,
      "username": "admin",
      "email": "admin@example.com",
      "first_name": "Admin",
      "last_name": "System"
    },
    "created_at": "2025-11-25T19:15:00Z"
  }
]
```

---

## 4. Supprimer une Imputation Spécifique

### Requête
```bash
curl -X DELETE http://localhost:8000/api/courriers/45/imputations/12/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Réponse (200 OK)
```json
{
  "message": "Imputation supprimée avec succès"
}
```

---

## 5. Lister Toutes les Imputations de Courriers Ordinaires

### Requête
```bash
curl -X GET "http://localhost:8000/api/courrier-imputation/?type_courrier=ordinaire" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Réponse (200 OK)
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

---

## 6. Filtrer les Imputations par Sens (Arrivée)

### Requête
```bash
curl -X GET "http://localhost:8000/api/courrier-imputation/?sens=arrivee" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 7. Filtrer les Imputations par Utilisateur

### Requête
```bash
curl -X GET "http://localhost:8000/api/courrier-imputation/?user=5" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 8. Filtrer les Imputations avec Droit d'Édition

### Requête
```bash
curl -X GET "http://localhost:8000/api/courrier-imputation/?access_type=edit" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 9. Filtres Combinés

### Requête
```bash
curl -X GET "http://localhost:8000/api/courrier-imputation/?type_courrier=ordinaire&sens=arrivee&access_type=view" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Description :** Récupère toutes les imputations de courriers ordinaires en arrivée avec droit de lecture uniquement.

---

## 10. Créer une Imputation (Méthode Alternative)

### Requête
```bash
curl -X POST http://localhost:8000/api/courrier-imputation/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "courrier": 45,
    "user": 5,
    "access_type": "view"
  }'
```

### Réponse (201 CREATED)
```json
{
  "id": 15,
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
  "created_at": "2025-11-25T20:00:00Z"
}
```

---

## 11. Supprimer une Imputation (Méthode Alternative)

### Requête
```bash
curl -X DELETE http://localhost:8000/api/courrier-imputation/15/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Réponse (204 NO CONTENT)
```
(Pas de contenu)
```

---

## Gestion des Erreurs

### Erreur 403 - Permissions Insuffisantes

**Requête :**
```bash
curl -X POST http://localhost:8000/api/courriers/45/imputer_courrier/ \
  -H "Authorization: Bearer AGENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 5,
    "access_type": "view"
  }'
```

**Réponse (403 FORBIDDEN) :**
```json
{
  "error": "Seuls les administrateurs et directeurs peuvent imputer des courriers"
}
```

---

### Erreur 404 - Utilisateur Non Trouvé

**Requête :**
```bash
curl -X POST http://localhost:8000/api/courriers/45/imputer_courrier/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 9999,
    "access_type": "view"
  }'
```

**Réponse (404 NOT FOUND) :**
```json
{
  "error": "Utilisateur non trouvé"
}
```

---

### Erreur 400 - Paramètre Manquant

**Requête :**
```bash
curl -X POST http://localhost:8000/api/courriers/45/imputer_courrier/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "access_type": "view"
  }'
```

**Réponse (400 BAD REQUEST) :**
```json
{
  "error": "user_id est requis"
}
```

---

## Exemples JavaScript (Frontend)

### Imputer un Courrier

```javascript
async function imputerCourrier(courrierId, userId, accessType = 'view') {
  try {
    const response = await fetch(`/api/courriers/${courrierId}/imputer_courrier/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        user_id: userId,
        access_type: accessType
      })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Erreur lors de l\'imputation');
    }
    
    const data = await response.json();
    console.log('Imputation réussie:', data);
    return data;
  } catch (error) {
    console.error('Erreur:', error);
    throw error;
  }
}

// Utilisation
imputerCourrier(45, 5, 'view')
  .then(result => console.log('Succès:', result))
  .catch(error => console.error('Échec:', error));
```

---

### Lister les Imputations d'un Courrier

```javascript
async function getImputationsCourrier(courrierId) {
  try {
    const response = await fetch(`/api/courriers/${courrierId}/imputations/`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    });
    
    if (!response.ok) {
      throw new Error('Erreur lors de la récupération des imputations');
    }
    
    const imputations = await response.json();
    return imputations;
  } catch (error) {
    console.error('Erreur:', error);
    throw error;
  }
}

// Utilisation
getImputationsCourrier(45)
  .then(imputations => {
    console.log('Imputations:', imputations);
    imputations.forEach(imp => {
      console.log(`- ${imp.user_details.first_name} ${imp.user_details.last_name} (${imp.access_type})`);
    });
  });
```

---

### Filtrer les Imputations

```javascript
async function getImputationsFiltered(filters = {}) {
  const params = new URLSearchParams();
  
  if (filters.type_courrier) params.append('type_courrier', filters.type_courrier);
  if (filters.sens) params.append('sens', filters.sens);
  if (filters.user) params.append('user', filters.user);
  if (filters.access_type) params.append('access_type', filters.access_type);
  
  try {
    const response = await fetch(`/api/courrier-imputation/?${params.toString()}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    });
    
    if (!response.ok) {
      throw new Error('Erreur lors de la récupération des imputations');
    }
    
    const imputations = await response.json();
    return imputations;
  } catch (error) {
    console.error('Erreur:', error);
    throw error;
  }
}

// Utilisation
getImputationsFiltered({
  type_courrier: 'ordinaire',
  sens: 'arrivee',
  access_type: 'view'
}).then(imputations => {
  console.log('Imputations filtrées:', imputations);
});
```

---

### Supprimer une Imputation

```javascript
async function supprimerImputation(courrierId, imputationId) {
  try {
    const response = await fetch(`/api/courriers/${courrierId}/imputations/${imputationId}/`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Erreur lors de la suppression');
    }
    
    const data = await response.json();
    console.log('Suppression réussie:', data);
    return data;
  } catch (error) {
    console.error('Erreur:', error);
    throw error;
  }
}

// Utilisation
supprimerImputation(45, 12)
  .then(result => console.log('Imputation supprimée'))
  .catch(error => console.error('Échec:', error));
```

---

## Exemples Python (Tests)

### Imputer un Courrier

```python
import requests

def imputer_courrier(courrier_id, user_id, access_type='view', token=None):
    url = f'http://localhost:8000/api/courriers/{courrier_id}/imputer_courrier/'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    data = {
        'user_id': user_id,
        'access_type': access_type
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code in [200, 201]:
        return response.json()
    else:
        raise Exception(f"Erreur {response.status_code}: {response.text}")

# Utilisation
try:
    result = imputer_courrier(45, 5, 'view', token='YOUR_TOKEN')
    print(f"✅ {result['message']}")
except Exception as e:
    print(f"❌ Erreur: {e}")
```

---

### Lister et Filtrer les Imputations

```python
import requests

def get_imputations(filters=None, token=None):
    url = 'http://localhost:8000/api/courrier-imputation/'
    headers = {'Authorization': f'Bearer {token}'}
    
    response = requests.get(url, headers=headers, params=filters or {})
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Erreur {response.status_code}: {response.text}")

# Utilisation
try:
    # Toutes les imputations de courriers ordinaires en arrivée
    imputations = get_imputations({
        'type_courrier': 'ordinaire',
        'sens': 'arrivee'
    }, token='YOUR_TOKEN')
    
    print(f"📊 {len(imputations)} imputations trouvées")
    for imp in imputations:
        print(f"  - {imp['courrier_details']['reference']}: "
              f"{imp['user_details']['username']} ({imp['access_type']})")
except Exception as e:
    print(f"❌ Erreur: {e}")
```

---

## Notes Importantes

1. **Authentification :** Tous les endpoints nécessitent un token JWT valide
2. **Permissions :** Seuls ADMIN et DIRECTEUR peuvent créer/supprimer des imputations
3. **Unicité :** Un utilisateur ne peut avoir qu'une seule imputation par type d'accès pour un courrier
4. **Mise à jour :** Si une imputation existe déjà, elle est mise à jour automatiquement
