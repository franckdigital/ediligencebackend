# 🚀 Guide de Configuration Celery pour la Surveillance Automatique

## Prérequis

- Redis installé et actif
- Celery installé dans le venv

## Étape 1 : Installer Redis

```bash
# Sur le serveur
sudo apt update
sudo apt install redis-server -y

# Démarrer Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Vérifier que Redis fonctionne
redis-cli ping
# Devrait répondre: PONG
```

## Étape 2 : Installer Celery

```bash
cd /var/www/numerix/ediligencebackend
source venv/bin/activate
pip install celery redis
```

## Étape 3 : Créer le service Celery Worker

Créer le fichier `/etc/systemd/system/celery.service` :

```ini
[Unit]
Description=Celery Worker Service
After=network.target redis-server.service

[Service]
Type=forking
User=root
Group=root
WorkingDirectory=/var/www/numerix/ediligencebackend
Environment="PATH=/var/www/numerix/ediligencebackend/venv/bin"
ExecStart=/var/www/numerix/ediligencebackend/venv/bin/celery -A ediligencebackend worker --loglevel=info --detach --pidfile=/var/run/celery/worker.pid --logfile=/var/log/celery/worker.log
ExecStop=/bin/kill -s TERM $MAINPID
Restart=always
RestartSec=10s

[Install]
WantedBy=multi-user.target
```

## Étape 4 : Créer le service Celery Beat (Scheduler)

Créer le fichier `/etc/systemd/system/celerybeat.service` :

```ini
[Unit]
Description=Celery Beat Service
After=network.target redis-server.service

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/var/www/numerix/ediligencebackend
Environment="PATH=/var/www/numerix/ediligencebackend/venv/bin"
ExecStart=/var/www/numerix/ediligencebackend/venv/bin/celery -A ediligencebackend beat --loglevel=info --pidfile=/var/run/celery/beat.pid --logfile=/var/log/celery/beat.log
Restart=always
RestartSec=10s

[Install]
WantedBy=multi-user.target
```

## Étape 5 : Créer les répertoires nécessaires

```bash
# Créer les répertoires pour les PID et logs
sudo mkdir -p /var/run/celery
sudo mkdir -p /var/log/celery
sudo chown -R root:root /var/run/celery
sudo chown -R root:root /var/log/celery
```

## Étape 6 : Activer et démarrer les services

```bash
# Recharger systemd
sudo systemctl daemon-reload

# Activer les services au démarrage
sudo systemctl enable celery
sudo systemctl enable celerybeat

# Démarrer les services
sudo systemctl start celery
sudo systemctl start celerybeat

# Vérifier le statut
sudo systemctl status celery
sudo systemctl status celerybeat
```

## Étape 7 : Vérifier les logs

```bash
# Logs Celery Worker
tail -f /var/log/celery/worker.log

# Logs Celery Beat
tail -f /var/log/celery/beat.log

# Logs systemd
sudo journalctl -u celery -f
sudo journalctl -u celerybeat -f
```

## Étape 8 : Tester

```bash
# Dans le shell Django
python manage.py shell
```

```python
from core.tasks_presence import check_agent_exits

# Exécuter manuellement
check_agent_exits()

# Vérifier que la tâche est planifiée
from celery import current_app
print(current_app.conf.beat_schedule)
```

## Configuration dans settings.py

Vérifier que ces lignes sont présentes dans `ediligencebackend/settings.py` :

```python
# Celery Configuration
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

# Celery Beat Schedule
CELERY_BEAT_SCHEDULE = {
    'check-agent-exits-every-5-minutes': {
        'task': 'core.tasks_presence.check_agent_exits',
        'schedule': 300.0,  # 5 minutes en secondes
    },
}
```

## Commandes utiles

```bash
# Redémarrer les services
sudo systemctl restart celery
sudo systemctl restart celerybeat

# Arrêter les services
sudo systemctl stop celery
sudo systemctl stop celerybeat

# Voir les logs en temps réel
tail -f /var/log/celery/worker.log
tail -f /var/log/celery/beat.log

# Vérifier Redis
redis-cli ping
redis-cli monitor  # Voir les commandes Redis en temps réel
```

## Dépannage

### Celery ne démarre pas

```bash
# Vérifier les permissions
sudo chown -R root:root /var/run/celery
sudo chown -R root:root /var/log/celery

# Vérifier Redis
sudo systemctl status redis-server

# Tester manuellement
cd /var/www/numerix/ediligencebackend
source venv/bin/activate
celery -A ediligencebackend worker --loglevel=debug
```

### Les tâches ne s'exécutent pas

```bash
# Vérifier que Beat est actif
sudo systemctl status celerybeat

# Voir les tâches planifiées
celery -A ediligencebackend inspect scheduled

# Voir les tâches actives
celery -A ediligencebackend inspect active
```

## ✅ Vérification finale

Une fois tout configuré, la tâche `check_agent_exits()` s'exécutera automatiquement toutes les 5 minutes pendant les heures de travail (7h30-16h30).

Vous pouvez vérifier dans les logs :
```bash
tail -f /var/log/celery/worker.log | grep "check_agent_exits"
```
