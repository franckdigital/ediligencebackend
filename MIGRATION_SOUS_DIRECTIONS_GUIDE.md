# Guide de Migration - Hiérarchie Direction → Sous-direction → Service

## 📋 Résumé des changements

Ce guide explique comment déployer la nouvelle structure hiérarchique à trois niveaux :
- **Direction** (niveau 1)
- **Sous-direction** (niveau 2) - NOUVEAU
- **Service** (niveau 3)

## 🔧 Migrations Django

### Ordre des migrations

1. **0031_add_sortie_fields.py** - Déjà appliquée (champs sortie pour présences)
2. **0033_alter_service_options_alter_service_direction_and_more.py** - Crée le modèle SousDirection et ajoute le champ `sous_direction` au modèle Service
3. **0034_add_new_roles.py** - Ajoute les nouveaux rôles (DIRECTEUR, SOUS_DIRECTEUR, CHEF_SERVICE)

### ⚠️ Important : Résolution du conflit de migration

La migration 0032 a été renommée en 0034 pour éviter les conflits avec le serveur de production.
La migration 0033 dépend maintenant directement de 0031.

## 🚀 Procédure de déploiement sur le serveur

### Étape 1 : Sauvegarder la base de données

```bash
cd /var/www/numerix/ediligencebackend
source venv/bin/activate
python manage.py dumpdata core.Service > backup_services.json
python manage.py dumpdata core.Direction > backup_directions.json
```

### Étape 2 : Déployer le code

```bash
# Pull les derniers changements
git pull origin main

# Ou copier les fichiers manuellement si nécessaire
```

### Étape 3 : Appliquer les migrations

```bash
cd /var/www/numerix/ediligencebackend
source venv/bin/activate

# Vérifier l'état des migrations
python manage.py showmigrations core

# Appliquer les nouvelles migrations
python manage.py migrate core 0033
python manage.py migrate core 0034
```

### Étape 4 : Migrer les données existantes

```bash
# Copier le script de migration sur le serveur
# Puis l'exécuter
python migrate_services_to_sous_directions.py
```

Ce script va :
- Créer une sous-direction par défaut pour chaque direction
- Migrer tous les services existants vers ces sous-directions
- Afficher un résumé de la structure

### Étape 5 : Redémarrer les services

```bash
# Redémarrer Gunicorn
sudo systemctl restart gunicorn

# Redémarrer Nginx (si nécessaire)
sudo systemctl restart nginx

# Redémarrer Celery (si utilisé)
sudo systemctl restart celery
```

### Étape 6 : Vérifier le déploiement

1. Accéder à l'interface web
2. Aller dans "Gestion de la Structure Organisationnelle"
3. Vérifier l'onglet "Sous-directions"
4. Créer un nouveau service et vérifier la sélection en cascade

## 📊 Structure des données après migration

```
Direction DSI
└── Sous-direction "Services DSI"
    ├── Service Developpement d'Application
    └── Service Maintenance Informatique
```

## 🔍 Vérifications post-déploiement

### Vérifier les migrations appliquées

```bash
python manage.py showmigrations core
```

Vous devriez voir :
```
[X] 0031_add_sortie_fields
[X] 0033_alter_service_options_alter_service_direction_and_more
[X] 0034_add_new_roles
```

### Vérifier la structure en base de données

```bash
python manage.py shell
```

```python
from core.models import Direction, SousDirection, Service

# Compter les entités
print(f"Directions: {Direction.objects.count()}")
print(f"Sous-directions: {SousDirection.objects.count()}")
print(f"Services: {Service.objects.count()}")

# Vérifier qu'aucun service n'a direction sans sous_direction
services_sans_sd = Service.objects.filter(sous_direction__isnull=True).count()
print(f"Services sans sous-direction: {services_sans_sd}")  # Devrait être 0

# Afficher la structure
for direction in Direction.objects.all():
    print(f"\n{direction.nom}")
    for sd in direction.sous_directions.all():
        print(f"  └─ {sd.nom} ({sd.services.count()} services)")
        for service in sd.services.all():
            print(f"      └─ {service.nom}")
```

## 🐛 Dépannage

### Erreur : "Migration core.0033 dependencies reference nonexistent parent node"

**Solution :** La migration 0033 a été corrigée pour dépendre de 0031 au lieu de 0032.

```bash
# Vérifier le contenu de la migration 0033
grep "dependencies" core/migrations/0033_alter_service_options_alter_service_direction_and_more.py
```

Devrait afficher :
```python
dependencies = [
    ('core', '0031_add_sortie_fields'),
]
```

### Erreur : "Duplicate key value violates unique constraint"

**Solution :** Supprimer les doublons avant d'appliquer la migration.

```bash
python manage.py shell
```

```python
from core.models import Service
# Identifier les doublons
duplicates = Service.objects.values('nom', 'direction').annotate(count=models.Count('id')).filter(count__gt=1)
print(duplicates)
```

### Services non migrés

Si certains services n'ont pas été migrés automatiquement :

```bash
python migrate_services_to_sous_directions.py
```

## 📝 Fichiers modifiés

### Backend
- `core/models.py` - Modèle SousDirection ajouté
- `core/serializers.py` - SousDirectionSerializer ajouté
- `core/views.py` - SousDirectionViewSet ajouté
- `core/migrations/0033_*.py` - Migration principale
- `core/migrations/0034_*.py` - Migration des rôles

### Frontend
- `frontend/src/pages/Services/ServiceList.js` - Affichage hiérarchique
- `frontend/src/pages/Services/ServiceModal.js` - Sélection en cascade

### Scripts
- `migrate_services_to_sous_directions.py` - Script de migration des données
- `fix_migration_0033.py` - Script de correction de la dépendance

## ✅ Checklist de déploiement

- [ ] Sauvegarder la base de données
- [ ] Déployer le code (git pull ou copie manuelle)
- [ ] Appliquer les migrations (0033, 0034)
- [ ] Exécuter le script de migration des données
- [ ] Redémarrer les services (gunicorn, nginx, celery)
- [ ] Vérifier l'interface web
- [ ] Tester la création d'une sous-direction
- [ ] Tester la création d'un service
- [ ] Vérifier les données migrées

## 📞 Support

En cas de problème, vérifier :
1. Les logs Django : `/var/www/numerix/ediligencebackend/logs/`
2. Les logs Gunicorn : `sudo journalctl -u gunicorn -n 50`
3. Les logs Nginx : `/var/log/nginx/error.log`
