# 📡 Changements API - Hiérarchie Direction → Sous-direction → Service

## Nouveaux endpoints

### Sous-directions

#### Liste des sous-directions
```http
GET /api/sous-directions/
```

**Réponse :**
```json
[
  {
    "id": 1,
    "nom": "Services DSI",
    "description": "Sous-direction regroupant les services de la DSI",
    "direction": 1,
    "direction_nom": "DSI",
    "nombre_services": 2,
    "created_at": "2025-10-02T18:30:00Z",
    "updated_at": "2025-10-02T18:30:00Z"
  }
]
```

#### Créer une sous-direction
```http
POST /api/sous-directions/
Content-Type: application/json

{
  "nom": "Sous-direction Développement",
  "description": "Gestion du développement logiciel",
  "direction": 1
}
```

#### Modifier une sous-direction
```http
PUT /api/sous-directions/{id}/
Content-Type: application/json

{
  "nom": "Sous-direction Dev & Innovation",
  "description": "Développement et innovation",
  "direction": 1
}
```

#### Supprimer une sous-direction
```http
DELETE /api/sous-directions/{id}/
```

**Note :** La suppression échoue si la sous-direction contient des services.

## Endpoints modifiés

### Services

#### Structure de réponse modifiée

**Avant :**
```json
{
  "id": 1,
  "nom": "Service Développement",
  "description": "...",
  "direction": 1,
  "direction_nom": "DSI"
}
```

**Après :**
```json
{
  "id": 1,
  "nom": "Service Développement",
  "description": "...",
  "sous_direction": 1,
  "sous_direction_nom": "Services DSI",
  "sous_direction_obj": {
    "id": 1,
    "nom": "Services DSI",
    "direction": 1,
    "direction_nom": "DSI",
    "nombre_services": 2
  },
  "direction": 1,  // DEPRECATED - À ne plus utiliser
  "direction_nom": "DSI"  // Maintenant via sous_direction_obj
}
```

#### Créer un service (nouvelle structure)

**Avant :**
```http
POST /api/services/
Content-Type: application/json

{
  "nom": "Service Développement",
  "description": "...",
  "direction": 1
}
```

**Après :**
```http
POST /api/services/
Content-Type: application/json

{
  "nom": "Service Développement",
  "description": "...",
  "sous_direction": 1
}
```

**Note :** Le champ `direction` est toujours accepté pour la rétrocompatibilité mais sera ignoré. Utilisez `sous_direction` à la place.

## Modèles de données

### SousDirection (nouveau)

```python
{
  "id": Integer,
  "nom": String (max 255 caractères),
  "description": String (optionnel),
  "direction": Integer (Foreign Key vers Direction),
  "direction_nom": String (lecture seule),
  "nombre_services": Integer (lecture seule),
  "created_at": DateTime,
  "updated_at": DateTime
}
```

**Contraintes :**
- Un nom de sous-direction doit être unique dans une direction
- Une sous-direction ne peut pas être supprimée si elle contient des services

### Service (modifié)

**Nouveaux champs :**
- `sous_direction` : Integer (Foreign Key vers SousDirection) - **REQUIS**
- `sous_direction_nom` : String (lecture seule)
- `sous_direction_obj` : Object (lecture seule, contient les détails de la sous-direction)

**Champs dépréciés :**
- `direction` : Integer (Foreign Key vers Direction) - **DEPRECATED**
- Utilisez `sous_direction_obj.direction` pour obtenir la direction

**Contraintes :**
- Un nom de service doit être unique dans une sous-direction

## Filtrage et recherche

### Filtrer les sous-directions par direction

```http
GET /api/sous-directions/?direction=1
```

### Filtrer les services par sous-direction

```http
GET /api/services/?sous_direction=1
```

### Recherche dans les services

La recherche inclut maintenant :
- Nom du service
- Description du service
- Nom de la sous-direction
- Nom de la direction (via sous-direction)

## Migration des clients existants

### Frontend React

**Avant :**
```javascript
// Création d'un service
const service = {
  nom: "Service Dev",
  description: "...",
  direction: directionId
};
```

**Après :**
```javascript
// Création d'un service
const service = {
  nom: "Service Dev",
  description: "...",
  sous_direction: sousDirectionId
};

// Affichage de la direction
const directionNom = service.sous_direction_obj?.direction_nom;
```

### Applications mobiles

**Important :** Mettre à jour les applications mobiles pour utiliser `sous_direction` au lieu de `direction` lors de la création/modification de services.

## Rétrocompatibilité

### Période de transition

Pour faciliter la migration, le champ `direction` reste présent dans les réponses API mais est marqué comme **DEPRECATED**.

**Recommandations :**
1. Mettre à jour tous les clients pour utiliser `sous_direction`
2. Utiliser `sous_direction_obj.direction` pour obtenir la direction
3. Ne plus envoyer le champ `direction` lors de la création/modification

### Suppression future

Le champ `direction` sera supprimé dans une version future (prévu pour 3 mois après le déploiement).

## Exemples d'utilisation

### Créer une structure complète

```javascript
// 1. Créer une direction (si nécessaire)
const direction = await api.post('/api/directions/', {
  nom: "Direction des Systèmes d'Information",
  description: "..."
});

// 2. Créer une sous-direction
const sousDirection = await api.post('/api/sous-directions/', {
  nom: "Sous-direction Développement",
  description: "...",
  direction: direction.id
});

// 3. Créer un service
const service = await api.post('/api/services/', {
  nom: "Service Applications Web",
  description: "...",
  sous_direction: sousDirection.id
});
```

### Récupérer la hiérarchie complète

```javascript
// Récupérer un service avec sa hiérarchie
const service = await api.get('/api/services/1/');

console.log(service.nom);  // "Service Applications Web"
console.log(service.sous_direction_obj.nom);  // "Sous-direction Développement"
console.log(service.sous_direction_obj.direction_nom);  // "Direction des SI"
```

## Tests

### Tester la création d'une sous-direction

```bash
curl -X POST http://localhost:8000/api/sous-directions/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "nom": "Test Sous-direction",
    "description": "Test",
    "direction": 1
  }'
```

### Tester la création d'un service

```bash
curl -X POST http://localhost:8000/api/services/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "nom": "Test Service",
    "description": "Test",
    "sous_direction": 1
  }'
```

## Questions fréquentes

### Q: Que se passe-t-il si j'envoie `direction` au lieu de `sous_direction` ?

**R:** Le champ sera ignoré. Vous devez utiliser `sous_direction` pour créer ou modifier un service.

### Q: Comment migrer mes services existants ?

**R:** Exécutez le script `migrate_services_to_sous_directions.py` qui créera automatiquement des sous-directions par défaut et migrera tous les services.

### Q: Puis-je supprimer une sous-direction qui contient des services ?

**R:** Non, vous devez d'abord supprimer ou déplacer tous les services de cette sous-direction.

### Q: Comment obtenir tous les services d'une direction ?

**R:** 
```javascript
// Récupérer toutes les sous-directions d'une direction
const sousDirections = await api.get(`/api/sous-directions/?direction=${directionId}`);

// Récupérer les services de chaque sous-direction
const services = [];
for (const sd of sousDirections) {
  const sdServices = await api.get(`/api/services/?sous_direction=${sd.id}`);
  services.push(...sdServices);
}
```

Ou utiliser le champ `nombre_services` de la direction pour obtenir le total.
