"""
Configuration Celery pour ediligencebackend
"""
import os
from celery import Celery
from celery.schedules import crontab

# Définir le module de settings Django par défaut
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ediligencebackend.settings')

# Créer l'instance Celery
app = Celery('ediligencebackend')

# Charger la configuration depuis Django settings avec le namespace CELERY
app.config_from_object('django.conf:settings', namespace='CELERY')

# Découvrir automatiquement les tâches dans les applications Django
app.autodiscover_tasks()

# Configuration du scheduler Beat
app.conf.beat_schedule = {
    'check-agent-exits-every-5-minutes': {
        'task': 'core.tasks_presence.check_agent_exits',
        'schedule': 300.0,  # 5 minutes en secondes
        'options': {'expires': 290.0}  # Expire avant la prochaine exécution
    },
    'check-geofence-violations-every-5-minutes': {
        'task': 'core.geofencing_tasks.check_geofence_violations',
        'schedule': 300.0,  # 5 minutes en secondes
        'options': {'expires': 290.0}  # Expire avant la prochaine exécution
    },
    'cleanup-old-locations-daily': {
        'task': 'core.geofencing_tasks.cleanup_old_locations',
        'schedule': crontab(hour=2, minute=0),  # Tous les jours à 2h00
    },
    'cleanup-old-alerts-weekly': {
        'task': 'core.geofencing_tasks.cleanup_old_alerts',
        'schedule': crontab(hour=3, minute=0, day_of_week=1),  # Tous les lundis à 3h00
    },
    'generate-geofence-report-daily': {
        'task': 'core.geofencing_tasks.generate_geofence_report',
        'schedule': crontab(hour=18, minute=0),  # Tous les jours à 18h00
    },
}

# Configuration du timezone
app.conf.timezone = 'UTC'

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
