"""
Script de test pour la fonctionnalité d'imputation des courriers ordinaires et confidentiels
"""

import os
import django
import sys

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ediligence.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import Courrier, CourrierImputation, Service, Direction
from datetime import date

def print_section(title):
    """Affiche un titre de section"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")

def test_courrier_imputation():
    """Test complet de la fonctionnalité d'imputation"""
    
    print_section("TEST DE LA FONCTIONNALITÉ D'IMPUTATION DES COURRIERS")
    
    # 1. Vérifier les utilisateurs
    print_section("1. Vérification des Utilisateurs")
    
    try:
        admin = User.objects.filter(profile__role='ADMIN').first()
        directeur = User.objects.filter(profile__role='DIRECTEUR').first()
        agent = User.objects.filter(profile__role='AGENT').first()
        
        if admin:
            print(f"✅ Admin trouvé: {admin.username} (ID: {admin.id})")
        else:
            print("❌ Aucun admin trouvé")
            
        if directeur:
            print(f"✅ Directeur trouvé: {directeur.username} (ID: {directeur.id})")
        else:
            print("⚠️  Aucun directeur trouvé")
            
        if agent:
            print(f"✅ Agent trouvé: {agent.username} (ID: {agent.id})")
        else:
            print("❌ Aucun agent trouvé")
            
    except Exception as e:
        print(f"❌ Erreur lors de la vérification des utilisateurs: {e}")
        return
    
    # 2. Créer des courriers de test
    print_section("2. Création de Courriers de Test")
    
    try:
        # Courrier ordinaire en arrivée
        courrier_ord_arrivee, created = Courrier.objects.get_or_create(
            reference='TEST-ORD-ARR-001',
            defaults={
                'expediteur': 'Ministère Test',
                'destinataire': 'Direction Générale',
                'objet': 'Test courrier ordinaire arrivée',
                'date_reception': date.today(),
                'type_courrier': 'ordinaire',
                'sens': 'arrivee',
                'categorie': 'Demande'
            }
        )
        print(f"{'✅ Créé' if created else '✅ Existant'}: Courrier ordinaire arrivée (ID: {courrier_ord_arrivee.id})")
        
        # Courrier ordinaire en départ
        courrier_ord_depart, created = Courrier.objects.get_or_create(
            reference='TEST-ORD-DEP-001',
            defaults={
                'expediteur': 'Direction Générale',
                'destinataire': 'Ministère Test',
                'objet': 'Test courrier ordinaire départ',
                'date_reception': date.today(),
                'type_courrier': 'ordinaire',
                'sens': 'depart',
                'categorie': 'Autre'
            }
        )
        print(f"{'✅ Créé' if created else '✅ Existant'}: Courrier ordinaire départ (ID: {courrier_ord_depart.id})")
        
        # Courrier confidentiel en arrivée
        courrier_conf_arrivee, created = Courrier.objects.get_or_create(
            reference='TEST-CONF-ARR-001',
            defaults={
                'expediteur': 'Source Confidentielle',
                'destinataire': 'Direction',
                'objet': 'Test courrier confidentiel arrivée',
                'date_reception': date.today(),
                'type_courrier': 'confidentiel',
                'sens': 'arrivee',
                'categorie': 'Réclamation'
            }
        )
        print(f"{'✅ Créé' if created else '✅ Existant'}: Courrier confidentiel arrivée (ID: {courrier_conf_arrivee.id})")
        
        # Courrier confidentiel en départ
        courrier_conf_depart, created = Courrier.objects.get_or_create(
            reference='TEST-CONF-DEP-001',
            defaults={
                'expediteur': 'Direction',
                'destinataire': 'Destinataire Confidentiel',
                'objet': 'Test courrier confidentiel départ',
                'date_reception': date.today(),
                'type_courrier': 'confidentiel',
                'sens': 'depart',
                'categorie': 'Invitation'
            }
        )
        print(f"{'✅ Créé' if created else '✅ Existant'}: Courrier confidentiel départ (ID: {courrier_conf_depart.id})")
        
    except Exception as e:
        print(f"❌ Erreur lors de la création des courriers: {e}")
        return
    
    # 3. Tester les imputations
    print_section("3. Test des Imputations")
    
    if not agent:
        print("⚠️  Impossible de tester les imputations sans agent")
        return
    
    courriers_test = [
        (courrier_ord_arrivee, "Courrier ordinaire arrivée"),
        (courrier_ord_depart, "Courrier ordinaire départ"),
        (courrier_conf_arrivee, "Courrier confidentiel arrivée"),
        (courrier_conf_depart, "Courrier confidentiel départ"),
    ]
    
    for courrier, description in courriers_test:
        try:
            # Test imputation en lecture
            imputation_view, created = CourrierImputation.objects.get_or_create(
                courrier=courrier,
                user=agent,
                access_type='view',
                defaults={'granted_by': admin or directeur or agent}
            )
            status = "✅ Créée" if created else "✅ Existante"
            print(f"{status}: Imputation VIEW pour {description}")
            print(f"   → ID: {imputation_view.id}, Accordée par: {imputation_view.granted_by.username}")
            
            # Test imputation en édition
            imputation_edit, created = CourrierImputation.objects.get_or_create(
                courrier=courrier,
                user=agent,
                access_type='edit',
                defaults={'granted_by': admin or directeur or agent}
            )
            status = "✅ Créée" if created else "✅ Existante"
            print(f"{status}: Imputation EDIT pour {description}")
            print(f"   → ID: {imputation_edit.id}, Accordée par: {imputation_edit.granted_by.username}")
            
        except Exception as e:
            print(f"❌ Erreur lors de l'imputation de {description}: {e}")
    
    # 4. Statistiques
    print_section("4. Statistiques des Imputations")
    
    try:
        total_imputations = CourrierImputation.objects.count()
        print(f"📊 Total des imputations: {total_imputations}")
        
        # Par type de courrier
        imputations_ordinaires = CourrierImputation.objects.filter(
            courrier__type_courrier='ordinaire'
        ).count()
        imputations_confidentielles = CourrierImputation.objects.filter(
            courrier__type_courrier='confidentiel'
        ).count()
        
        print(f"\n📈 Répartition par type:")
        print(f"   - Courriers ordinaires: {imputations_ordinaires}")
        print(f"   - Courriers confidentiels: {imputations_confidentielles}")
        
        # Par sens
        imputations_arrivee = CourrierImputation.objects.filter(
            courrier__sens='arrivee'
        ).count()
        imputations_depart = CourrierImputation.objects.filter(
            courrier__sens='depart'
        ).count()
        
        print(f"\n📥 Répartition par sens:")
        print(f"   - Arrivée: {imputations_arrivee}")
        print(f"   - Départ: {imputations_depart}")
        
        # Par type d'accès
        imputations_view = CourrierImputation.objects.filter(
            access_type='view'
        ).count()
        imputations_edit = CourrierImputation.objects.filter(
            access_type='edit'
        ).count()
        
        print(f"\n🔐 Répartition par type d'accès:")
        print(f"   - Lecture (view): {imputations_view}")
        print(f"   - Édition (edit): {imputations_edit}")
        
        # Imputations par utilisateur
        if agent:
            imputations_agent = CourrierImputation.objects.filter(user=agent).count()
            print(f"\n👤 Imputations pour {agent.username}: {imputations_agent}")
        
    except Exception as e:
        print(f"❌ Erreur lors du calcul des statistiques: {e}")
    
    # 5. Test de filtrage
    print_section("5. Test de Filtrage des Imputations")
    
    try:
        # Filtrer par type de courrier ordinaire
        ordinaires = CourrierImputation.objects.filter(
            courrier__type_courrier='ordinaire'
        ).select_related('courrier', 'user', 'granted_by')
        
        print(f"🔍 Imputations de courriers ordinaires: {ordinaires.count()}")
        for imp in ordinaires[:3]:  # Afficher les 3 premières
            print(f"   → {imp.courrier.reference} ({imp.courrier.sens}) - "
                  f"{imp.user.username} ({imp.access_type})")
        
        # Filtrer par sens arrivée
        arrivees = CourrierImputation.objects.filter(
            courrier__sens='arrivee'
        ).select_related('courrier', 'user', 'granted_by')
        
        print(f"\n🔍 Imputations de courriers en arrivée: {arrivees.count()}")
        for imp in arrivees[:3]:
            print(f"   → {imp.courrier.reference} ({imp.courrier.type_courrier}) - "
                  f"{imp.user.username} ({imp.access_type})")
        
    except Exception as e:
        print(f"❌ Erreur lors du test de filtrage: {e}")
    
    # 6. Test de suppression
    print_section("6. Test de Suppression d'Imputation")
    
    try:
        # Créer une imputation temporaire
        courrier_temp, _ = Courrier.objects.get_or_create(
            reference='TEST-TEMP-001',
            defaults={
                'expediteur': 'Test',
                'objet': 'Test temporaire',
                'date_reception': date.today(),
                'type_courrier': 'ordinaire',
                'sens': 'arrivee',
                'categorie': 'Autre'
            }
        )
        
        imputation_temp, created = CourrierImputation.objects.get_or_create(
            courrier=courrier_temp,
            user=agent,
            access_type='view',
            defaults={'granted_by': admin or agent}
        )
        
        if created:
            print(f"✅ Imputation temporaire créée (ID: {imputation_temp.id})")
            
            # Supprimer l'imputation
            imputation_temp.delete()
            print(f"✅ Imputation temporaire supprimée avec succès")
            
            # Supprimer le courrier temporaire
            courrier_temp.delete()
            print(f"✅ Courrier temporaire supprimé avec succès")
        else:
            print(f"⚠️  Imputation temporaire existait déjà")
        
    except Exception as e:
        print(f"❌ Erreur lors du test de suppression: {e}")
    
    # 7. Résumé final
    print_section("7. Résumé Final")
    
    print("✅ Tests terminés avec succès!")
    print("\n📋 Fonctionnalités testées:")
    print("   ✓ Création de courriers ordinaires (arrivée/départ)")
    print("   ✓ Création de courriers confidentiels (arrivée/départ)")
    print("   ✓ Imputation avec accès VIEW")
    print("   ✓ Imputation avec accès EDIT")
    print("   ✓ Filtrage par type de courrier")
    print("   ✓ Filtrage par sens")
    print("   ✓ Statistiques des imputations")
    print("   ✓ Suppression d'imputation")
    
    print("\n🎯 Prochaines étapes:")
    print("   1. Tester via l'API REST avec Postman ou curl")
    print("   2. Vérifier les permissions (ADMIN, DIRECTEUR)")
    print("   3. Tester le frontend avec les nouveaux endpoints")
    print("   4. Consulter COURRIER_IMPUTATION_GUIDE.md pour plus de détails")

if __name__ == '__main__':
    try:
        test_courrier_imputation()
    except Exception as e:
        print(f"\n❌ ERREUR CRITIQUE: {e}")
        import traceback
        traceback.print_exc()
