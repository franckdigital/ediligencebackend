# Vérification des migrations sur le serveur

## Commande à exécuter sur le serveur

```bash
cd /var/www/numerix/ediligencebackend
source venv/bin/activate
python manage.py showmigrations core
```

Cette commande va afficher toutes les migrations avec leur état :
- `[X]` = Migration appliquée
- `[ ]` = Migration non appliquée

## Trouver la dernière migration appliquée

```bash
# Afficher seulement les migrations appliquées
python manage.py showmigrations core | grep "\[X\]" | tail -5
```

## Lister les fichiers de migration présents

```bash
ls -la core/migrations/ | grep "^-" | tail -10
```

## Une fois que vous avez identifié la dernière migration

Envoyez-moi le résultat et je corrigerai la dépendance de la migration 0033.

Par exemple, si la dernière migration est `0030_alter_pushnotificationtoken_token`, 
je modifierai la migration 0033 pour dépendre de 0030 au lieu de 0031.
