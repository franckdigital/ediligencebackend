# ⚠️ IMPORTANT - Ordre des opérations

## ❌ NE PAS faire la sauvegarde AVANT les migrations

**ERREUR courante :**
```bash
# ❌ FAUX - Ne fonctionne pas
python manage.py dumpdata core.Service > backup_services.json
python manage.py migrate core 0033
```

**Erreur obtenue :**
```
CommandError: Unable to serialize database: (1054, "Unknown column 'core_service.sous_direction_id' in 'field list'")
```

## ✅ Ordre correct des opérations

### 1. Appliquer les migrations D'ABORD
```bash
python manage.py migrate core 0033
python manage.py migrate core 0034
```

### 2. Migrer les données
```bash
python migrate_services_to_sous_directions.py
```

### 3. Sauvegarder APRÈS (optionnel)
```bash
python manage.py dumpdata core.Service > backup_services.json
python manage.py dumpdata core.SousDirection > backup_sousdirections.json
```

## 🔍 Pourquoi cet ordre ?

La migration 0033 **crée** la colonne `sous_direction_id` dans la table `core_service`.

Si vous essayez de sauvegarder avant la migration :
- Django essaie de lire tous les champs du modèle Service
- Le modèle Python inclut déjà le champ `sous_direction`
- Mais la colonne n'existe pas encore en base de données
- ❌ Erreur : "Unknown column 'core_service.sous_direction_id'"

## 📋 Procédure complète et correcte

```bash
# 1. Se connecter au serveur
cd /var/www/numerix/ediligencebackend
source venv/bin/activate

# 2. Vérifier l'état actuel
python manage.py showmigrations core

# 3. Appliquer les migrations
python manage.py migrate core 0033
python manage.py migrate core 0034

# 4. Migrer les données
python migrate_services_to_sous_directions.py

# 5. Vérifier le résultat
python manage.py shell -c "from core.models import Service; print(f'Services sans sous-direction: {Service.objects.filter(sous_direction__isnull=True).count()}')"

# 6. Sauvegarder (maintenant c'est possible)
python manage.py dumpdata core.Service > backup_services.json
python manage.py dumpdata core.SousDirection > backup_sousdirections.json

# 7. Redémarrer
sudo systemctl restart gunicorn
```

## 🛡️ Sécurité des données

**Q: Mais si la migration échoue, je perds mes données ?**

**R:** Non, les migrations Django sont transactionnelles. Si une migration échoue :
- La transaction est annulée (rollback)
- Vos données restent intactes
- Aucune modification n'est appliquée

**Q: Comment faire une vraie sauvegarde préventive ?**

**R:** Utilisez mysqldump ou pg_dump directement sur la base de données :

```bash
# MySQL
mysqldump -u root -p ediligence_db > backup_full_$(date +%Y%m%d_%H%M%S).sql

# PostgreSQL
pg_dump ediligence_db > backup_full_$(date +%Y%m%d_%H%M%S).sql
```

Cette méthode sauvegarde la structure réelle de la base de données, pas le modèle Python.
