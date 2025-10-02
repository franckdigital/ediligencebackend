# 🚀 Déploiement Rapide - Sous-directions

## Commandes à exécuter sur le serveur de production

### 1. Se connecter au serveur et aller dans le répertoire du projet

```bash
cd /var/www/numerix/ediligencebackend
source venv/bin/activate
```

### 2. Sauvegarder les données (IMPORTANT)

```bash
python manage.py dumpdata core.Service > backup_services_$(date +%Y%m%d_%H%M%S).json
python manage.py dumpdata core.Direction > backup_directions_$(date +%Y%m%d_%H%M%S).json
```

### 3. Appliquer les migrations

```bash
python manage.py migrate core 0033
python manage.py migrate core 0034
```

### 4. Migrer les données existantes

```bash
python migrate_services_to_sous_directions.py
```

### 5. Redémarrer les services

```bash
sudo systemctl restart gunicorn
```

## ✅ Vérification

Accéder à l'interface web et vérifier :
- Onglet "Sous-directions" visible
- Création d'un service avec sélection Direction → Sous-direction

## 🐛 En cas d'erreur

Si vous voyez l'erreur : `Migration core.0033 dependencies reference nonexistent parent node`

**Solution :**
```bash
# Éditer le fichier de migration
nano core/migrations/0033_alter_service_options_alter_service_direction_and_more.py

# Changer la ligne 11 de :
# ('core', '0032_add_new_roles'),
# vers :
# ('core', '0031_add_sortie_fields'),

# Puis réessayer
python manage.py migrate core 0033
```

## 📞 Fichiers à transférer sur le serveur

Si les fichiers ne sont pas encore sur le serveur, transférer :

1. **Migrations :**
   - `core/migrations/0033_alter_service_options_alter_service_direction_and_more.py`
   - `core/migrations/0034_add_new_roles.py`

2. **Script de migration des données :**
   - `migrate_services_to_sous_directions.py`

3. **Modèles et vues (si modifiés) :**
   - `core/models.py`
   - `core/serializers.py`
   - `core/views.py`

## 📋 Commande de transfert (depuis votre machine locale)

```bash
# Depuis le répertoire ediligencebackend
scp core/migrations/0033_*.py root@srv958363:/var/www/numerix/ediligencebackend/core/migrations/
scp core/migrations/0034_*.py root@srv958363:/var/www/numerix/ediligencebackend/core/migrations/
scp migrate_services_to_sous_directions.py root@srv958363:/var/www/numerix/ediligencebackend/
```

Remplacer `srv958363` par l'adresse IP ou le nom d'hôte de votre serveur.
