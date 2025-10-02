# 🔍 Diagnostic des erreurs 500

## Commandes à exécuter sur le serveur

### 1. Voir les logs détaillés du service

```bash
sudo journalctl -u ediligencebackend -n 100 --no-pager
```

### 2. Voir les logs d'erreur Django

```bash
# Si vous avez un fichier de log Django
tail -n 100 /var/www/numerix/ediligencebackend/logs/django.log

# Ou chercher les fichiers de log
find /var/www/numerix/ediligencebackend -name "*.log" -type f
```

### 3. Tester directement avec Python

```bash
cd /var/www/numerix/ediligencebackend
source venv/bin/activate

python manage.py shell
```

Puis dans le shell Python :

```python
from core.models import Direction, Service

# Tester Direction
try:
    directions = Direction.objects.all()
    for d in directions:
        print(f"Direction: {d.nom}")
        print(f"  Sous-directions: {d.nombre_sous_directions}")
        print(f"  Services: {d.nombre_services}")
except Exception as e:
    print(f"Erreur: {e}")
    import traceback
    traceback.print_exc()

# Tester Service
try:
    services = Service.objects.all()
    for s in services:
        print(f"Service: {s.nom}")
        print(f"  Sous-direction: {s.sous_direction}")
except Exception as e:
    print(f"Erreur: {e}")
    import traceback
    traceback.print_exc()
```

### 4. Vérifier les serializers

```bash
cd /var/www/numerix/ediligencebackend
source venv/bin/activate

python manage.py shell
```

```python
from core.serializers import DirectionSerializer, ServiceSerializer
from core.models import Direction, Service

# Tester DirectionSerializer
try:
    direction = Direction.objects.first()
    serializer = DirectionSerializer(direction)
    print(serializer.data)
except Exception as e:
    print(f"Erreur DirectionSerializer: {e}")
    import traceback
    traceback.print_exc()

# Tester ServiceSerializer
try:
    service = Service.objects.first()
    serializer = ServiceSerializer(service)
    print(serializer.data)
except Exception as e:
    print(f"Erreur ServiceSerializer: {e}")
    import traceback
    traceback.print_exc()
```

## Problèmes possibles

### 1. Serializer qui accède à des champs inexistants

Le `DirectionSerializer` ou `ServiceSerializer` essaie peut-être d'accéder à des champs qui n'existent pas encore.

**Vérifier :**
```bash
grep -n "nombre_sous_directions\|nombre_services" core/serializers.py
```

### 2. Relation sous_direction non configurée

Le champ `sous_direction` dans Service doit être nullable.

**Vérifier :**
```bash
grep -A 3 "sous_direction" core/models.py | grep -A 3 "class Service"
```

### 3. Cache Python

Le serveur utilise peut-être une version en cache du code.

**Solution :**
```bash
# Trouver et supprimer les fichiers .pyc
find /var/www/numerix/ediligencebackend -name "*.pyc" -delete
find /var/www/numerix/ediligencebackend -name "__pycache__" -type d -exec rm -rf {} +

# Redémarrer
sudo systemctl restart ediligencebackend
```

## Actions immédiates

1. **Exécutez les commandes de diagnostic** ci-dessus
2. **Envoyez-moi les logs** complets de l'erreur
3. **Vérifiez que le fichier models.py** a bien été transféré avec les try/except

Une fois que j'aurai les logs détaillés, je pourrai identifier le problème exact.
