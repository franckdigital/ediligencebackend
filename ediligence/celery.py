"""
Configuration Celery pour ediligence
"""
import os
from celery import Celery
from celery.schedules import crontab

# Définir le module de settings Django par défaut
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ediligence.settings')

# Créer l'instance Celery
app = Celery('ediligence')

# Charger la configuration depuis Django settings avec le namespace CELERY
app.config_from_object('django.conf:settings', namespace='CELERY')

# Découvrir automatiquement les tâches dans les applications Django
# Celery cherche automatiquement un fichier tasks.py dans chaque app
app.autodiscover_tasks()

# Configuration du scheduler Beat
app.conf.beat_schedule = {
    'check-agent-exits-every-5-minutes': {
        'task': 'core.tasks_presence.check_agent_exits',
        'schedule': 300.0,  # 5 minutes en secondes
        'options': {'expires': 290.0}  # Expire avant la prochaine exécution
    },
}

# Configuration du timezone
app.conf.timezone = 'UTC'

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
