# Résolution du Conflit de Migration Géofencing

## 🚨 Problème
- Erreur: `(1050, "Table 'core_geofencesettings' already exists")`
- Les tables géofencing existent déjà mais les migrations ne sont pas synchronisées
- Avertissement MySQL sur la longueur du champ `token` (> 255 caractères)

## ✅ Solution Recommandée

### Étape 1: Vérifier l'état actuel
```bash
cd /var/www/numerix/ediligencebackend

# Vérifier les migrations appliquées
python manage.py showmigrations core

# Vérifier les tables existantes
mysql -u root -p ediligence -e "SHOW TABLES LIKE '%geofence%'; SHOW TABLES LIKE '%agent%'; SHOW TABLES LIKE '%push%';"
```

### Étape 2: Marquer les migrations comme appliquées (SOLUTION RECOMMANDÉE)
```bash
# Marquer la migration de merge comme appliquée sans l'exécuter
python manage.py migrate core 0030_merge_20251001_1244 --fake

# Vérifier que c'est bien marqué
python manage.py showmigrations core
```

### Étape 3: Copier les fichiers corrigés
Copiez depuis votre environnement local :
- `core/models.py` (champ token corrigé à max_length=255)
- `core/migrations/0030_alter_pushnotificationtoken_token.py` (nouvelle migration)

### Étape 4: Appliquer la correction du champ token
```bash
# Appliquer la migration de correction du token
python manage.py migrate core 0030_alter_pushnotificationtoken_token
```

### Étape 5: Initialiser les paramètres
```bash
# Initialiser les paramètres de géofencing
python manage.py setup_geofencing
```

### Étape 6: Redémarrer le service
```bash
sudo systemctl restart ediligencebackend
sudo systemctl status ediligencebackend
```

## 🔄 Solution Alternative (Si la première ne fonctionne pas)

### Option A: Supprimer et recréer les tables
```bash
# ⚠️ ATTENTION: Cela supprimera toutes les données géofencing
mysql -u root -p ediligence -e "
DROP TABLE IF EXISTS core_pushnotificationtoken;
DROP TABLE IF EXISTS core_agentlocation;
DROP TABLE IF EXISTS core_geofencealert;
DROP TABLE IF EXISTS core_geofencesettings;
"

# Puis relancer la migration
python manage.py migrate
```

### Option B: Utiliser le script automatique
```bash
# Copier le script fix_migration_conflict.py sur le serveur
python fix_migration_conflict.py
```

## 🧪 Vérification Finale

### Vérifier les tables créées
```sql
DESCRIBE core_geofencesettings;
DESCRIBE core_geofencealert;
DESCRIBE core_agentlocation;
DESCRIBE core_pushnotificationtoken;
```

### Vérifier le champ token
```sql
SHOW COLUMNS FROM core_pushnotificationtoken WHERE Field = 'token';
```
Le champ `token` doit avoir `varchar(255)` et non `text`.

### Tester l'API
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/geofence-settings/
```

## 📋 Résumé des Corrections

1. **Champ token** : `CharField(max_length=255)` au lieu de `CharField(max_length=500)`
2. **Migration fake** : Marquer les migrations existantes comme appliquées
3. **Migration corrective** : Appliquer uniquement la correction du champ token
4. **Initialisation** : Configurer les paramètres par défaut

Cette approche évite de supprimer les données existantes tout en résolvant le conflit de migration.
