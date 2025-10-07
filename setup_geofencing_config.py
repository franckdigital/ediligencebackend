#!/usr/bin/env python3
"""
Script pour configurer les paramètres de géofencing
Usage: python setup_geofencing_config.py
"""
import os
import sys
import django
from datetime import time

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ediligence.settings')
django.setup()

from core.models import GeofenceSettings, Bureau

def setup_geofencing_config():
    """Configurer les paramètres de géofencing"""
    print("⚙️  CONFIGURATION DU GÉOFENCING")
    print("=" * 50)
    
    # Créer ou récupérer la configuration
    settings, created = GeofenceSettings.objects.get_or_create(
        defaults={
            # Heures de travail
            'heure_debut_matin': time(7, 30),
            'heure_fin_matin': time(12, 30),
            'heure_debut_apres_midi': time(13, 30),
            'heure_fin_apres_midi': time(16, 30),
            
            # Configuration des alertes
            'distance_alerte_metres': 200,
            'duree_minimale_hors_bureau_minutes': 5,  # 5 minutes au lieu de 60
            'frequence_verification_minutes': 5,
            
            # Jours de travail (lundi à vendredi)
            'lundi_travaille': True,
            'mardi_travaille': True,
            'mercredi_travaille': True,
            'jeudi_travaille': True,
            'vendredi_travaille': True,
            'samedi_travaille': False,
            'dimanche_travaille': False,
            
            # Notifications
            'notification_directeurs': True,
            'notification_superieurs': True,
            'notification_push_active': True,
        }
    )
    
    if created:
        print("✅ Nouvelle configuration créée")
    else:
        print("✅ Configuration existante trouvée")
        # Mettre à jour la durée minimale si elle est encore à 60 minutes
        if settings.duree_minimale_hors_bureau_minutes == 60:
            settings.duree_minimale_hors_bureau_minutes = 5
            settings.save()
            print("🔧 Durée minimale mise à jour: 60 → 5 minutes")
    
    print(f"\n📋 Configuration actuelle:")
    print(f"   Distance d'alerte: {settings.distance_alerte_metres}m")
    print(f"   Durée minimale hors bureau: {settings.duree_minimale_hors_bureau_minutes} minutes")
    print(f"   Fréquence de vérification: {settings.frequence_verification_minutes} minutes")
    print(f"   Heures de travail matin: {settings.heure_debut_matin} - {settings.heure_fin_matin}")
    print(f"   Heures de travail après-midi: {settings.heure_debut_apres_midi} - {settings.heure_fin_apres_midi}")
    
    # Vérifier les bureaux
    print(f"\n🏢 Vérification des bureaux:")
    bureaux = Bureau.objects.all()
    
    if bureaux.exists():
        for bureau in bureaux:
            print(f"   ✅ {bureau.nom}")
            print(f"      Coordonnées: {bureau.latitude_centre}, {bureau.longitude_centre}")
            print(f"      Rayon: {bureau.rayon_autorise_metres}m")
            
            # Vérifier que les coordonnées sont définies
            if not bureau.latitude_centre or not bureau.longitude_centre:
                print(f"      ⚠️  ATTENTION: Coordonnées manquantes!")
            
            if not bureau.rayon_autorise_metres:
                bureau.rayon_autorise_metres = settings.distance_alerte_metres
                bureau.save()
                print(f"      🔧 Rayon mis à jour: {settings.distance_alerte_metres}m")
    else:
        print("   ❌ Aucun bureau configuré")
        print("   💡 Créez au moins un bureau avec des coordonnées GPS")
    
    return settings

def test_configuration():
    """Tester la configuration"""
    print(f"\n🧪 TEST DE LA CONFIGURATION")
    print("=" * 50)
    
    settings = GeofenceSettings.objects.first()
    if not settings:
        print("❌ Aucune configuration trouvée")
        return
    
    # Tester les heures de travail
    from django.utils import timezone
    from datetime import datetime
    
    # Test pour hier à 16h12
    hier = timezone.now().date() - timezone.timedelta(days=1)
    test_time = timezone.make_aware(datetime.combine(hier, time(16, 12)))
    
    if settings.is_heure_travail(test_time):
        print(f"✅ 16h12 est bien dans les heures de travail")
    else:
        print(f"❌ 16h12 n'est PAS dans les heures de travail")
        print(f"   Heures configurées: {settings.heure_debut_apres_midi} - {settings.heure_fin_apres_midi}")
    
    # Test pour maintenant
    maintenant = timezone.now()
    if settings.is_heure_travail(maintenant):
        print(f"✅ L'heure actuelle ({maintenant.strftime('%H:%M')}) est dans les heures de travail")
    else:
        print(f"ℹ️  L'heure actuelle ({maintenant.strftime('%H:%M')}) n'est pas dans les heures de travail")

def main():
    """Fonction principale"""
    print("🔧 OUTIL DE CONFIGURATION GÉOFENCING")
    print("=" * 60)
    
    try:
        settings = setup_geofencing_config()
        test_configuration()
        
        print(f"\n💡 PROCHAINES ÉTAPES:")
        print("1. Redémarrez Celery Beat pour prendre en compte les nouvelles tâches")
        print("2. Vérifiez que Celery Worker fonctionne")
        print("3. Testez avec: python test_geofencing_manual.py")
        print("4. Surveillez les logs de Celery pour les erreurs")
        
        print(f"\n🚀 Commandes utiles:")
        print("   Celery Worker: celery -A ediligencebackend worker --loglevel=info")
        print("   Celery Beat: celery -A ediligencebackend beat --loglevel=info")
        print("   Test manuel: python manage.py shell -c \"from core.geofencing_tasks import check_geofence_violations; check_geofence_violations()\"")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
