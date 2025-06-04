import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ediligence.settings')
django.setup()

from core.models import Direction, Service

# Créer une direction
direction = Direction.objects.create(
    nom='Direction des Ressources Humaines',
    description='Gestion des ressources humaines et du personnel'
)
print(f'Direction créée : {direction}')

# Créer un service dans cette direction
service = Service.objects.create(
    nom='Service Recrutement',
    description='Gestion des recrutements',
    direction=direction
)
print(f'Service créé : {service}')
