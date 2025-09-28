import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ediligence.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import UserProfile, Diligence, Service, Direction
from django.db import models
import traceback

try:
    # Trouver un utilisateur avec le rôle DIRECTEUR
    directeur_profiles = UserProfile.objects.filter(role='DIRECTEUR')
    print(f"Nombre de directeurs trouvés: {directeur_profiles.count()}")
    
    if directeur_profiles.exists():
        directeur_profile = directeur_profiles.first()
        directeur_user = directeur_profile.user
        directeur_direction = directeur_profile.service.direction if directeur_profile.service else None
        
        print(f"\n=== Test pour DIRECTEUR ===")
        print(f"Directeur: {directeur_user.username}")
        print(f"Service: {directeur_profile.service}")
        print(f"Direction: {directeur_direction}")
        
        if directeur_direction:
            # Services de cette direction
            direction_services = Service.objects.filter(direction=directeur_direction)
            print(f"Services dans la direction: {[s.nom for s in direction_services]}")
            
            # Agents de tous les services de cette direction
            direction_agents = User.objects.filter(profile__service__in=direction_services)
            print(f"Agents dans la direction: {[u.username for u in direction_agents]}")
            
            # Diligences directement liées à la direction
            base_qs = Diligence.objects.all()
            direction_qs = base_qs.filter(
                models.Q(direction=directeur_direction) |
                models.Q(services_concernes__direction=directeur_direction) |
                models.Q(courrier__service__direction=directeur_direction)
            ).distinct()
            
            # Diligences des agents de la direction
            agents_direction_qs = base_qs.filter(agents__in=direction_agents).distinct()
            
            print(f"\nRésultats:")
            print(f"Diligences directement liées à la direction: {direction_qs.count()}")
            print(f"Diligences des agents de la direction: {agents_direction_qs.count()}")
            
            # Combiner les IDs
            diligence_ids = set()
            diligence_ids.update(direction_qs.values_list('id', flat=True))
            diligence_ids.update(agents_direction_qs.values_list('id', flat=True))
            
            final_qs = base_qs.filter(id__in=diligence_ids)
            print(f"Total diligences visibles par le directeur: {final_qs.count()}")
            
            # Afficher les détails des diligences
            for diligence in final_qs:
                print(f"- Diligence {diligence.id}: {diligence.objet[:50]}...")
                if diligence.agents.exists():
                    agents = [a.username for a in diligence.agents.all()]
                    print(f"  Agents: {agents}")
                if diligence.courrier and diligence.courrier.service:
                    print(f"  Service courrier: {diligence.courrier.service.nom}")
        
    else:
        print("Aucun directeur trouvé dans la base de données")
        
        # Créer un utilisateur directeur pour test
        print("\nCréation d'un utilisateur directeur pour test...")
        
        # Vérifier s'il y a des directions
        directions = Direction.objects.all()
        if directions.exists():
            direction = directions.first()
            print(f"Direction utilisée: {direction.nom}")
            
            # Vérifier s'il y a des services dans cette direction
            services = Service.objects.filter(direction=direction)
            if services.exists():
                service = services.first()
                print(f"Service utilisé: {service.nom}")
                
                # Créer un utilisateur directeur
                directeur_user, created = User.objects.get_or_create(
                    username='directeur_test',
                    defaults={'email': 'directeur@test.com'}
                )
                
                directeur_profile, created = UserProfile.objects.get_or_create(
                    user=directeur_user,
                    defaults={
                        'role': 'DIRECTEUR',
                        'service': service
                    }
                )
                
                print(f"Directeur créé: {directeur_user.username} (Profile: {directeur_profile.role})")
            else:
                print("Aucun service trouvé dans la direction")
        else:
            print("Aucune direction trouvée dans la base de données")
        
except Exception as e:
    print(f"Erreur: {e}")
    traceback.print_exc()
