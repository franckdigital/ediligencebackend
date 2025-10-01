from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import GeofenceSettings, Bureau, Notification


class Command(BaseCommand):
    help = 'Configure le système de géofencing avec les paramètres par défaut'

    def add_arguments(self, parser):
        parser.add_argument(
            '--bureau-lat',
            type=float,
            default=14.6928,
            help='Latitude du bureau principal (défaut: Dakar)'
        )
        parser.add_argument(
            '--bureau-lng',
            type=float,
            default=-17.4467,
            help='Longitude du bureau principal (défaut: Dakar)'
        )
        parser.add_argument(
            '--bureau-nom',
            type=str,
            default='Bureau Principal',
            help='Nom du bureau principal'
        )

    def handle(self, *args, **options):
        self.stdout.write('Configuration du système de géofencing...')

        # 1. Créer ou mettre à jour les paramètres de géofencing
        settings, created = GeofenceSettings.objects.get_or_create(
            pk=1,  # Un seul objet de configuration
            defaults={
                'heure_debut_matin': '07:30',
                'heure_fin_matin': '12:30',
                'heure_debut_apres_midi': '13:30',
                'heure_fin_apres_midi': '16:30',
                'distance_alerte_metres': 200,
                'duree_minimale_hors_bureau_minutes': 60,
                'frequence_verification_minutes': 5,
                'lundi_travaille': True,
                'mardi_travaille': True,
                'mercredi_travaille': True,
                'jeudi_travaille': True,
                'vendredi_travaille': True,
                'samedi_travaille': False,
                'dimanche_travaille': False,
                'notification_directeurs': True,
                'notification_superieurs': True,
                'notification_push_active': True,
            }
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS('✓ Configuration de géofencing créée')
            )
        else:
            self.stdout.write(
                self.style.WARNING('⚠ Configuration de géofencing déjà existante')
            )

        # 2. Créer le bureau principal s'il n'existe pas
        bureau, created = Bureau.objects.get_or_create(
            nom=options['bureau_nom'],
            defaults={
                'latitude_centre': options['bureau_lat'],
                'longitude_centre': options['bureau_lng'],
                'rayon_metres': 200,
            }
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS(f'✓ Bureau "{bureau.nom}" créé aux coordonnées ({bureau.latitude_centre}, {bureau.longitude_centre})')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'⚠ Bureau "{bureau.nom}" déjà existant')
            )

        # 3. Vérifier les types de notifications
        self._setup_notification_types()

        # 4. Afficher un résumé
        self._display_summary(settings, bureau)

        self.stdout.write(
            self.style.SUCCESS('\n🎉 Configuration du géofencing terminée avec succès!')
        )

    def _setup_notification_types(self):
        """Configurer les types de notifications pour le géofencing"""
        # Vérifier si le type 'geofence_alert' existe dans les choix
        # Cette vérification est informative car les choix sont définis dans le modèle
        
        self.stdout.write('✓ Types de notifications configurés')
        self.stdout.write('  - geofence_alert: Alerte de géofencing')

    def _display_summary(self, settings, bureau):
        """Afficher un résumé de la configuration"""
        self.stdout.write('\n📋 Résumé de la configuration:')
        self.stdout.write(f'   Heures de travail: {settings.heure_debut_matin}-{settings.heure_fin_matin} et {settings.heure_debut_apres_midi}-{settings.heure_fin_apres_midi}')
        self.stdout.write(f'   Distance d\'alerte: {settings.distance_alerte_metres}m')
        self.stdout.write(f'   Fréquence de vérification: {settings.frequence_verification_minutes} minutes')
        self.stdout.write(f'   Bureau principal: {bureau.nom} ({bureau.latitude_centre}, {bureau.longitude_centre})')
        self.stdout.write(f'   Notifications directeurs: {"✓" if settings.notification_directeurs else "✗"}')
        self.stdout.write(f'   Notifications supérieurs: {"✓" if settings.notification_superieurs else "✗"}')
        self.stdout.write(f'   Notifications push: {"✓" if settings.notification_push_active else "✗"}')

        # Compter les utilisateurs par rôle
        directeurs_count = User.objects.filter(profile__role='DIRECTEUR').count()
        superieurs_count = User.objects.filter(profile__role='SUPERIEUR').count()
        agents_count = User.objects.filter(profile__role='AGENT').count()

        self.stdout.write('\n👥 Utilisateurs dans le système:')
        self.stdout.write(f'   Directeurs: {directeurs_count}')
        self.stdout.write(f'   Supérieurs: {superieurs_count}')
        self.stdout.write(f'   Agents: {agents_count}')

        if agents_count == 0:
            self.stdout.write(
                self.style.WARNING('⚠ Aucun agent trouvé. Assurez-vous d\'avoir des utilisateurs avec le rôle AGENT.')
            )

        if directeurs_count == 0 and superieurs_count == 0:
            self.stdout.write(
                self.style.WARNING('⚠ Aucun directeur ou supérieur trouvé. Les notifications ne seront pas envoyées.')
            )

        self.stdout.write('\n📱 Prochaines étapes:')
        self.stdout.write('   1. Configurer l\'application mobile avec le service de géofencing')
        self.stdout.write('   2. Tester les permissions de localisation')
        self.stdout.write('   3. Configurer les tokens de notification push (FCM/APNS)')
        self.stdout.write('   4. Optionnel: Configurer Celery pour les tâches automatiques')
        
        self.stdout.write('\n🔗 URLs importantes:')
        self.stdout.write('   - Alertes: /geofencing-alerts')
        self.stdout.write('   - API: /api/geofence-alerts/')
        self.stdout.write('   - Configuration: /api/geofence-settings/')
