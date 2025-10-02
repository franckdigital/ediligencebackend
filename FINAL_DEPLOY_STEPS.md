# 🚀 Étapes finales de déploiement

## ✅ Fichiers déjà transférés sur le serveur

- ✅ `core/migrations/0033_alter_service_options_alter_service_direction_and_more.py`
- ✅ `core/migrations/0034_add_new_roles.py`
- ✅ `migrate_services_to_sous_directions.py`

## 🔄 Action requise : Mettre à jour le fichier 0033

Le fichier 0033 sur le serveur doit être mis à jour pour dépendre de `0030_update_roles_final` au lieu de `0030_alter_pushnotificationtoken_token`.

### Option 1 : Retransférer le fichier corrigé

```bash
# Depuis votre machine locale
scp core/migrations/0033_alter_service_options_alter_service_direction_and_more.py root@srv958363:/var/www/numerix/ediligencebackend/core/migrations/
```

### Option 2 : Modifier directement sur le serveur

```bash
# Sur le serveur
cd /var/www/numerix/ediligencebackend
nano core/migrations/0033_alter_service_options_alter_service_direction_and_more.py

# Modifier la ligne 11 :
# DE:   ('core', '0030_alter_pushnotificationtoken_token'),
# VERS: ('core', '0030_update_roles_final'),

# Sauvegarder : Ctrl+O, Enter, Ctrl+X
```

## 📋 Commandes finales à exécuter

Une fois le fichier 0033 corrigé :

```bash
cd /var/www/numerix/ediligencebackend
source venv/bin/activate

# 1. Vérifier les migrations
python manage.py showmigrations core | tail -10

# 2. Appliquer la migration 0033
python manage.py migrate core 0033

# 3. Appliquer la migration 0034
python manage.py migrate core 0034

# 4. Migrer les données existantes
python migrate_services_to_sous_directions.py

# 5. Vérifier le résultat
python manage.py shell -c "from core.models import Service, SousDirection; print(f'Services: {Service.objects.count()}, Sous-directions: {SousDirection.objects.count()}, Services sans SD: {Service.objects.filter(sous_direction__isnull=True).count()}')"

# 6. Redémarrer Gunicorn
sudo systemctl restart gunicorn

# 7. Vérifier les logs
sudo journalctl -u gunicorn -n 20
```

## ✅ Vérification finale

Accéder à l'interface web et vérifier :
1. Page "Gestion de la Structure Organisationnelle" accessible
2. Onglet "Sous-directions" visible
3. Création d'une sous-direction fonctionne
4. Création d'un service avec sélection Direction → Sous-direction fonctionne

## 🐛 En cas d'erreur

Si vous voyez encore une erreur de dépendance, vérifiez :

```bash
# Afficher le contenu de la ligne 11 du fichier 0033
sed -n '11p' core/migrations/0033_alter_service_options_alter_service_direction_and_more.py

# Devrait afficher :
# ('core', '0030_update_roles_final'),
```

Si ce n'est pas le cas, retransférez le fichier corrigé depuis votre machine locale.
