import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ediligence.settings')
django.setup()

from core.models import Direction, Service

# Vérifier les directions
print("=== Directions ===")
for direction in Direction.objects.all():
    print(f"- {direction.nom}")
    print(f"  Description: {direction.description}")
    print(f"  Nombre de services: {direction.nombre_services}")
    print()

# Vérifier les services
print("\n=== Services ===")
for service in Service.objects.all():
    print(f"- {service.nom}")
    print(f"  Direction: {service.direction.nom if service.direction else 'Non assigné'}")
    print(f"  Description: {service.description}")
    print()
