"""
Script de migration pour déplacer les services des directions vers les sous-directions.
Ce script crée une sous-direction par défaut pour chaque direction si nécessaire,
puis migre tous les services vers ces sous-directions.
"""

import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ediligence.settings')
django.setup()

from core.models import Direction, SousDirection, Service

def migrate_services():
    print("Debut de la migration des services vers les sous-directions...\n")
    
    # Récupérer tous les services qui ont une direction mais pas de sous-direction
    services_to_migrate = Service.objects.filter(direction__isnull=False, sous_direction__isnull=True)
    total_services = services_to_migrate.count()
    
    if total_services == 0:
        print("Aucun service a migrer. Tous les services sont deja lies a des sous-directions.")
        return
    
    print(f"{total_services} service(s) a migrer\n")
    
    migrated_count = 0
    created_sous_directions = {}
    
    for service in services_to_migrate:
        direction = service.direction
        
        # Vérifier si une sous-direction par défaut existe déjà pour cette direction
        if direction.id not in created_sous_directions:
            # Chercher une sous-direction existante pour cette direction
            sous_direction = SousDirection.objects.filter(direction=direction).first()
            
            if not sous_direction:
                # Créer une sous-direction par défaut
                sous_direction = SousDirection.objects.create(
                    nom=f"Services {direction.nom}",
                    description=f"Sous-direction regroupant les services de la {direction.nom}",
                    direction=direction
                )
                print(f"Sous-direction creee: '{sous_direction.nom}' pour la direction '{direction.nom}'")
            
            created_sous_directions[direction.id] = sous_direction
        
        # Migrer le service vers la sous-direction
        sous_direction = created_sous_directions[direction.id]
        service.sous_direction = sous_direction
        service.save()
        
        migrated_count += 1
        print(f"   Service '{service.nom}' migre vers '{sous_direction.nom}'")
    
    print(f"\nMigration terminee avec succes!")
    print(f"   - {len(created_sous_directions)} sous-direction(s) creee(s) ou utilisee(s)")
    print(f"   - {migrated_count} service(s) migre(s)")
    
    # Afficher un résumé de la structure
    print("\nResume de la structure organisationnelle:")
    for direction in Direction.objects.all():
        print(f"\n{direction.nom}")
        for sous_direction in direction.sous_directions.all():
            services_count = sous_direction.services.count()
            print(f"   {sous_direction.nom} ({services_count} service(s))")
            for service in sous_direction.services.all():
                print(f"      {service.nom}")

if __name__ == '__main__':
    try:
        migrate_services()
    except Exception as e:
        print(f"\nErreur lors de la migration: {str(e)}")
        import traceback
        traceback.print_exc()
