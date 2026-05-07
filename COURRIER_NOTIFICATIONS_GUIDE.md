# Guide Complet - Système de Notifications pour Courriers

## 📢 Vue d'Ensemble

Le système de notifications pour courriers permet de notifier automatiquement les utilisateurs lors d'événements importants liés aux courriers ordinaires et confidentiels.

---

## 🎯 Types de Notifications

### 1. Nouveau Courrier Reçu (`nouveau_courrier`)
**Déclencheur :** Création d'un nouveau courrier

**Destinataires :**
- **Courriers confidentiels :** ADMIN et DIRECTEUR uniquement
- **Courriers ordinaires :** Utilisateurs du service concerné + ADMIN/DIRECTEUR

**Priorité :** 
- Haute pour courriers confidentiels
- Normale pour courriers ordinaires

**Exemple de message :**
> "Un nouveau courrier confidentiel en arrivée a été enregistré : CONF-2025-001. Objet: Demande urgente"

---

### 2. Courrier Imputé (`courrier_impute`)
**Déclencheur :** Attribution d'un courrier à un utilisateur

**Destinataires :** L'utilisateur à qui le courrier est imputé

**Priorité :** 
- Haute pour courriers confidentiels
- Normale pour courriers ordinaires

**Exemple de message :**
> "Le courrier COUR-2025-045 vous a été imputé en édition par Jean Dupont."

---

### 3. Accès Accordé (`acces_accorde`)
**Déclencheur :** Octroi d'un accès à un courrier confidentiel

**Destinataires :** L'utilisateur qui reçoit l'accès

**Priorité :** Haute

**Exemple de message :**
> "Vous avez reçu un accès en lecture au courrier confidentiel CONF-2025-002 de la part de Marie Martin."

---

### 4. Accès Révoqué (`acces_revoque`)
**Déclencheur :** Suppression d'un accès ou d'une imputation

**Destinataires :** L'utilisateur dont l'accès est révoqué

**Priorité :** Normale

**Exemple de message :**
> "Votre accès au courrier confidentiel CONF-2025-002 a été révoqué."

---

### 5. Rappel de Traitement (`rappel_traitement`)
**Déclencheur :** Système de rappels automatiques

**Destinataires :** Utilisateurs concernés par le courrier

**Priorité :** Urgente

**Exemple de message :**
> "Le courrier COUR-2025-045 nécessite votre attention. Échéance: 30/11/2025"

---

### 6. Statut Modifié (`statut_modifie`)
**Déclencheur :** Changement de statut d'un courrier

**Destinataires :** Utilisateurs ayant une imputation sur le courrier

**Priorité :** Normale

**Exemple de message :**
> "Le statut du courrier COUR-2025-045 a été modifié en 'Traité' par Jean Dupont."

---

### 7. Diligence Créée (`diligence_creee`)
**Déclencheur :** Création d'une diligence liée à un courrier

**Destinataires :** 
- Responsable de la diligence (priorité haute)
- Agents assignés (priorité normale)

**Exemple de message :**
> "Une diligence a été créée pour le courrier COUR-2025-045. Vous en êtes le responsable."

---

## 🔧 Backend - API Endpoints

### Base URL
```
/api/courrier-notifications/
```

### Endpoints Disponibles

#### 1. Liste des Notifications
```http
GET /api/courrier-notifications/
```

**Paramètres de filtrage :**
- `lue` - true/false
- `type` - Type de notification
- `priorite` - Priorité (urgente, haute, normale, basse)
- `courrier` - ID du courrier

**Réponse :**
```json
[
  {
    "id": 1,
    "titre": "Nouveau courrier confidentiel en arrivée",
    "message": "Un nouveau courrier...",
    "type_notification": "nouveau_courrier",
    "priorite": "haute",
    "lue": false,
    "courrier_details": {
      "id": 45,
      "reference": "CONF-2025-001",
      "objet": "Demande urgente"
    },
    "temps_ecoule": "il y a 5 minutes",
    "created_at": "2025-11-25T18:30:00Z"
  }
]
```

---

#### 2. Notifications Non Lues
```http
GET /api/courrier-notifications/non_lues/
```

**Réponse :**
```json
{
  "count": 5,
  "notifications": [...]
}
```

---

#### 3. Compter les Non Lues
```http
GET /api/courrier-notifications/count_non_lues/
```

**Réponse :**
```json
{
  "count": 5
}
```

---

#### 4. Marquer comme Lue
```http
POST /api/courrier-notifications/{id}/marquer_lue/
```

**Réponse :**
```json
{
  "id": 1,
  "lue": true,
  "date_lecture": "2025-11-25T19:00:00Z",
  ...
}
```

---

#### 5. Marquer Toutes comme Lues
```http
POST /api/courrier-notifications/marquer_toutes_lues/
```

**Réponse :**
```json
{
  "message": "5 notification(s) marquée(s) comme lue(s)",
  "count": 5
}
```

---

#### 6. Supprimer les Lues
```http
DELETE /api/courrier-notifications/supprimer_lues/
```

**Réponse :**
```json
{
  "message": "3 notification(s) supprimée(s)",
  "count": 3
}
```

---

#### 7. Statistiques
```http
GET /api/courrier-notifications/statistiques/
```

**Réponse :**
```json
{
  "total": 25,
  "non_lues": 5,
  "lues": 20,
  "par_type": [
    {"type_notification": "nouveau_courrier", "count": 10},
    {"type_notification": "courrier_impute", "count": 8}
  ],
  "par_priorite": [
    {"priorite": "haute", "count": 5},
    {"priorite": "normale", "count": 15}
  ],
  "recentes_7_jours": 12
}
```

---

#### 8. Notifications par Courrier
```http
GET /api/courrier-notifications/par_courrier/?courrier_id=45
```

---

#### 9. Créer Notification Manuelle (ADMIN/DIRECTEUR)
```http
POST /api/courrier-notifications/creer_notification_manuelle/
```

**Body :**
```json
{
  "utilisateur_id": 5,
  "courrier_id": 45,
  "titre": "Attention requise",
  "message": "Ce courrier nécessite votre attention immédiate",
  "priorite": "haute"
}
```

---

#### 10. Notifications Urgentes
```http
GET /api/courrier-notifications/urgentes/
```

---

## 🎨 Frontend - Composants

### 1. CourrierNotificationBell
**Emplacement :** Barre de navigation

**Fonctionnalités :**
- Badge avec nombre de notifications non lues
- Dropdown avec liste des notifications récentes
- Polling automatique toutes les 30 secondes
- Marquage comme lu au clic
- Navigation vers le courrier concerné

**Utilisation :**
```jsx
import CourrierNotificationBell from './components/CourrierNotificationBell';

<CourrierNotificationBell />
```

---

### 2. CourrierNotificationsPage
**Route :** `/courriers/notifications`

**Fonctionnalités :**
- Liste complète des notifications
- Filtres (statut, type, priorité)
- Actions en masse (marquer toutes comme lues, supprimer les lues)
- Statistiques détaillées
- Pagination

---

## 🔔 Signaux Automatiques

### Configuration
Les signaux sont automatiquement activés dans `core/apps.py` :

```python
def ready(self):
    import core.signals_courrier
```

### Signaux Implémentés

1. **post_save(Courrier)** → Nouveau courrier
2. **post_save(CourrierImputation)** → Courrier imputé
3. **post_save(CourrierAccess)** → Accès accordé
4. **post_delete(CourrierAccess)** → Accès révoqué
5. **post_delete(CourrierImputation)** → Imputation supprimée
6. **post_save(CourrierStatut)** → Statut modifié
7. **post_save(Diligence)** → Diligence créée

---

## 💻 Exemples d'Utilisation

### Frontend - Service API

#### Récupérer les notifications
```javascript
import courrierNotificationService from './services/courrierNotificationService';

// Toutes les notifications
const notifications = await courrierNotificationService.getAllNotifications();

// Non lues uniquement
const unread = await courrierNotificationService.getUnreadNotifications();

// Avec filtres
const filtered = await courrierNotificationService.getAllNotifications({
  lue: false,
  priorite: 'haute'
});
```

#### Marquer comme lue
```javascript
await courrierNotificationService.markAsRead(notificationId);
```

#### Polling automatique
```javascript
const intervalId = courrierNotificationService.startPolling((count) => {
  console.log(`${count} nouvelles notifications`);
}, 30000); // Toutes les 30 secondes

// Arrêter le polling
courrierNotificationService.stopPolling(intervalId);
```

---

### Backend - Créer une Notification Manuellement

```python
from core.signals_courrier import creer_notification
from core.models import Courrier, User

courrier = Courrier.objects.get(id=45)
utilisateur = User.objects.get(id=5)

creer_notification(
    utilisateur=utilisateur,
    courrier=courrier,
    type_notification='rappel_traitement',
    titre='Rappel de traitement',
    message='Ce courrier nécessite votre attention',
    priorite='urgente',
    metadata={'deadline': '2025-12-01'}
)
```

---

## 📊 Modèle de Données

### CourrierNotification

| Champ | Type | Description |
|-------|------|-------------|
| utilisateur | ForeignKey | Destinataire de la notification |
| courrier | ForeignKey | Courrier concerné (optionnel) |
| type_notification | CharField | Type de notification |
| titre | CharField | Titre de la notification |
| message | TextField | Message détaillé |
| priorite | CharField | Priorité (basse, normale, haute, urgente) |
| lue | BooleanField | Statut de lecture |
| date_lecture | DateTimeField | Date de lecture |
| cree_par | ForeignKey | Créateur (optionnel) |
| created_at | DateTimeField | Date de création |
| metadata | JSONField | Données supplémentaires |

---

## 🎯 Bonnes Pratiques

### 1. Gestion des Notifications
- ✅ Marquer comme lues après lecture
- ✅ Supprimer régulièrement les anciennes notifications
- ✅ Utiliser les filtres pour cibler les notifications importantes
- ✅ Activer le polling pour les mises à jour en temps réel

### 2. Priorités
- **Urgente :** Courriers critiques, rappels d'échéance
- **Haute :** Courriers confidentiels, imputations importantes
- **Normale :** Courriers ordinaires, modifications de statut
- **Basse :** Informations générales

### 3. Performance
- Le polling est configuré à 30 secondes par défaut
- Les notifications sont indexées pour des requêtes rapides
- Utiliser les filtres pour limiter les données chargées

---

## 🔒 Sécurité

### Permissions
- Tous les utilisateurs peuvent voir leurs propres notifications
- Seuls ADMIN et DIRECTEUR peuvent créer des notifications manuelles
- Les notifications sont filtrées par utilisateur automatiquement

### Données Sensibles
- Les courriers confidentiels ne sont notifiés qu'aux utilisateurs autorisés
- Les métadonnées peuvent contenir des informations supplémentaires sécurisées

---

## 🚀 Déploiement

### Backend
```bash
# 1. Créer les migrations
python manage.py makemigrations

# 2. Appliquer les migrations
python manage.py migrate

# 3. Vérifier que les signaux sont activés
# Voir les logs au démarrage du serveur
```

### Frontend
```bash
# Aucune dépendance supplémentaire requise
# Les composants utilisent Ant Design déjà installé
```

---

## 📈 Monitoring

### Vérifier le Fonctionnement

1. **Créer un courrier** → Vérifier la notification
2. **Imputer un courrier** → Vérifier la notification de l'utilisateur
3. **Consulter les statistiques** → `/api/courrier-notifications/statistiques/`
4. **Tester le polling** → Observer le badge de notifications

---

## 🐛 Dépannage

### Les notifications ne s'affichent pas
- Vérifier que les signaux sont importés dans `apps.py`
- Vérifier les logs du serveur Django
- Tester l'endpoint `/api/courrier-notifications/`

### Le polling ne fonctionne pas
- Vérifier la console du navigateur
- Vérifier que le token JWT est valide
- Augmenter l'intervalle de polling si nécessaire

### Notifications en double
- Vérifier que les signaux ne sont pas importés plusieurs fois
- Vérifier la logique de création dans `signals_courrier.py`

---

## 📞 Support

Pour toute question :
1. Consulter cette documentation
2. Vérifier les logs (`python manage.py runserver`)
3. Tester avec Postman les endpoints API
4. Consulter le code source des signaux

**Date de création :** 25 Novembre 2025  
**Version :** 1.0  
**Statut :** ✅ Opérationnel
