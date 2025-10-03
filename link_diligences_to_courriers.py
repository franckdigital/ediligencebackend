#!/usr/bin/env python
"""
Script pour lier les diligences existantes à leurs courriers
basé sur la référence du courrier
"""
import os
import sys
import django

# Configuration Django
sys.path.append('/var/www/numerix/ediligencebackend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ediligence.settings')
django.setup()

from core.models import Diligence, Courrier

def link_diligences_to_courriers():
    """Lie les diligences aux courriers basé sur reference_courrier"""
    
    # Récupérer toutes les diligences sans courrier lié mais avec une référence
    diligences_sans_courrier = Diligence.objects.filter(
        courrier__isnull=True,
        reference_courrier__isnull=False
    ).exclude(reference_courrier='')
    
    print(f"Nombre de diligences sans courrier lié: {diligences_sans_courrier.count()}")
    
    linked_count = 0
    not_found_count = 0
    
    for diligence in diligences_sans_courrier:
        try:
            # Chercher le courrier correspondant
            courrier = Courrier.objects.get(reference=diligence.reference_courrier)
            
            # Lier la diligence au courrier
            diligence.courrier = courrier
            diligence.save()
            
            linked_count += 1
            print(f"✓ Diligence #{diligence.id} liée au courrier #{courrier.id} ({courrier.reference})")
            
        except Courrier.DoesNotExist:
            not_found_count += 1
            print(f"✗ Courrier non trouvé pour la diligence #{diligence.id} (référence: {diligence.reference_courrier})")
        except Courrier.MultipleObjectsReturned:
            print(f"⚠ Plusieurs courriers trouvés pour la référence: {diligence.reference_courrier}")
        except Exception as e:
            print(f"❌ Erreur pour la diligence #{diligence.id}: {str(e)}")
    
    print(f"\n=== RÉSUMÉ ===")
    print(f"Diligences liées: {linked_count}")
    print(f"Courriers non trouvés: {not_found_count}")
    print(f"Total traité: {linked_count + not_found_count}")

if __name__ == '__main__':
    print("Démarrage de la liaison diligences-courriers...\n")
    link_diligences_to_courriers()
    print("\nTerminé!")
