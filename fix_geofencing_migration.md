# Fix pour la Migration Géofencing

## Problème
La migration `0029_geofencesettings_agentlocation_geofencealert_and_more.py` échoue avec l'erreur :
```
(1170, "BLOB/TEXT column 'token' used in key specification without a key length")
```

## Solution

### 1. Sur le serveur de production, supprimer la migration problématique :

```bash
cd /var/www/numerix/ediligencebackend
rm core/migrations/0029_geofencesettings_agentlocation_geofencealert_and_more.py
```

### 2. Copier le modèle corrigé :

Le champ `token` dans `PushNotificationToken` a été changé de :
```python
token = models.TextField(unique=True, help_text="Token FCM/APNS")
```

À :
```python
token = models.CharField(max_length=500, unique=True, help_text="Token FCM/APNS")
```

Et la contrainte `unique_together = ('user', 'token')` a été supprimée.

### 3. Copier la nouvelle migration :

Copiez le fichier `core/migrations/0029_geofencesettings_pushnotificationtoken_geofencealert_and_more.py` 
depuis votre environnement local vers le serveur.

### 4. Appliquer la migration :

```bash
python manage.py migrate
```

### 5. Initialiser les paramètres de géofencing :

```bash
python manage.py setup_geofencing
```

### 6. Redémarrer le service :

```bash
sudo systemctl restart ediligencebackend
sudo systemctl status ediligencebackend
```

## Vérification

Vérifiez que les tables ont été créées :
```sql
SHOW TABLES LIKE '%geofence%';
SHOW TABLES LIKE '%agent%';
SHOW TABLES LIKE '%push%';
```

Les tables suivantes devraient exister :
- `core_geofencesettings`
- `core_geofencealert`
- `core_agentlocation`
- `core_pushnotificationtoken`
