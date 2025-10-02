# 🔧 Correction de l'erreur AttributeError sur /api/directions/

## 🎯 Problème identifié

L'erreur `AttributeError at /api/directions/` se produit car le modèle `Direction` essaie d'accéder à la relation `sous_directions` qui n'existe pas encore en base de données (la migration 0033 n'a pas été appliquée).

## ✅ Solution appliquée

J'ai modifié le fichier `core/models.py` pour rendre les propriétés `nombre_sous_directions` et `nombre_services` sûres avec des try/except.

## 📋 Actions à effectuer

### 1. Transférer le fichier models.py corrigé

```bash
# Depuis votre machine locale
scp core/models.py root@srv958363:/var/www/numerix/ediligencebackend/core/
```

### 2. Redémarrer Gunicorn

```bash
# Sur le serveur
sudo systemctl restart gunicorn
```

### 3. Vérifier que l'API fonctionne

```bash
# Tester l'endpoint
curl -H "Authorization: Bearer YOUR_TOKEN" https://api-diligence.numerix.digital/api/directions/
```

### 4. Appliquer les migrations

Une fois que l'API fonctionne, appliquer les migrations :

```bash
cd /var/www/numerix/ediligencebackend
source venv/bin/activate

python manage.py migrate core 0033
python manage.py migrate core 0034
python migrate_services_to_sous_directions.py

sudo systemctl restart gunicorn
```

## 📝 Modifications apportées

**Avant :**
```python
@property
def nombre_sous_directions(self):
    return self.sous_directions.count()  # ❌ Erreur si sous_directions n'existe pas
```

**Après :**
```python
@property
def nombre_sous_directions(self):
    try:
        return self.sous_directions.count()
    except:
        return 0  # ✅ Retourne 0 si la relation n'existe pas encore
```

## 🔍 Vérification

Après le redémarrage, l'interface web devrait fonctionner normalement et vous pourrez accéder à la page "Gestion de la Structure Organisationnelle".
