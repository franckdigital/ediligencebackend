from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from core.models import Diligence, DiligenceNotification
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Envoie des rappels automatiques pour les échéances de diligences'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche les rappels qui seraient envoyés sans les créer',
        )

    def handle(self, *args, **options):
        today = timezone.now().date()
        dry_run = options['dry_run']
        
        # Rappels 7 jours avant échéance
        rappel_1_date = today + timedelta(days=7)
        diligences_rappel_1 = Diligence.objects.filter(
            date_limite=rappel_1_date,
            statut__in=['en_attente', 'en_cours']
        )
        
        # Rappels 3 jours avant échéance
        rappel_2_date = today + timedelta(days=3)
        diligences_rappel_2 = Diligence.objects.filter(
            date_limite=rappel_2_date,
            statut__in=['en_attente', 'en_cours']
        )
        
        # Rappels pour échéances dépassées
        diligences_overdue = Diligence.objects.filter(
            date_limite__lt=today,
            statut__in=['en_attente', 'en_cours']
        )
        
        rappels_crees = 0
        
        # Traiter les rappels 7 jours
        for diligence in diligences_rappel_1:
            for agent in diligence.agents.all():
                # Vérifier si le rappel n'existe pas déjà
                existing = DiligenceNotification.objects.filter(
                    user=agent,
                    diligence=diligence,
                    type_notification='rappel_delai',
                    created_at__date=today
                ).exists()
                
                if not existing:
                    if dry_run:
                        self.stdout.write(
                            f"[DRY RUN] Rappel 7j pour {agent.username} - Diligence {diligence.reference_courrier}"
                        )
                    else:
                        DiligenceNotification.objects.create(
                            user=agent,
                            diligence=diligence,
                            type_notification='rappel_delai',
                            message=f'Rappel: Échéance dans 7 jours pour {diligence.reference_courrier}'
                        )
                        rappels_crees += 1
        
        # Traiter les rappels 3 jours
        for diligence in diligences_rappel_2:
            for agent in diligence.agents.all():
                # Vérifier si le rappel n'existe pas déjà
                existing = DiligenceNotification.objects.filter(
                    user=agent,
                    diligence=diligence,
                    type_notification='rappel_delai',
                    created_at__date=today
                ).exists()
                
                if not existing:
                    if dry_run:
                        self.stdout.write(
                            f"[DRY RUN] Rappel 3j URGENT pour {agent.username} - Diligence {diligence.reference_courrier}"
                        )
                    else:
                        DiligenceNotification.objects.create(
                            user=agent,
                            diligence=diligence,
                            type_notification='rappel_delai',
                            message=f'URGENT: Échéance dans 3 jours pour {diligence.reference_courrier}'
                        )
                        rappels_crees += 1
        
        # Traiter les échéances dépassées
        for diligence in diligences_overdue:
            for agent in diligence.agents.all():
                # Vérifier si le rappel n'existe pas déjà aujourd'hui
                existing = DiligenceNotification.objects.filter(
                    user=agent,
                    diligence=diligence,
                    type_notification='rappel_delai',
                    created_at__date=today
                ).exists()
                
                if not existing:
                    days_overdue = (today - diligence.date_limite).days
                    if dry_run:
                        self.stdout.write(
                            f"[DRY RUN] Échéance DÉPASSÉE ({days_overdue}j) pour {agent.username} - Diligence {diligence.reference_courrier}"
                        )
                    else:
                        DiligenceNotification.objects.create(
                            user=agent,
                            diligence=diligence,
                            type_notification='rappel_delai',
                            message=f'ÉCHÉANCE DÉPASSÉE de {days_overdue} jour(s) pour {diligence.reference_courrier}'
                        )
                        rappels_crees += 1
        
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'[DRY RUN] {diligences_rappel_1.count()} rappels 7j, '
                    f'{diligences_rappel_2.count()} rappels 3j, '
                    f'{diligences_overdue.count()} échéances dépassées'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'{rappels_crees} rappels créés avec succès')
            )
