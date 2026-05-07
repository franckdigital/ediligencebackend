from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Agent, Bureau

class Command(BaseCommand):
    help = 'Corriger l\'assignation des bureaux aux agents'

    def handle(self, *args, **options):
        self.stdout.write("=== CORRECTION BUREAUX AGENTS ===")
        
        # 1. Lister les bureaux
        bureaux = Bureau.objects.all()
        self.stdout.write(f"Bureaux disponibles: {bureaux.count()}")
        for bureau in bureaux:
            self.stdout.write(f"  - {bureau.nom}")
        
        # 2. Vérifier les agents sans bureau
        agents_sans_bureau = Agent.objects.filter(bureau__isnull=True)
        self.stdout.write(f"\nAgents sans bureau: {agents_sans_bureau.count()}")
        for agent in agents_sans_bureau:
            self.stdout.write(f"  - {agent.user.username}")
        
        # 3. Corriger si nécessaire
        if agents_sans_bureau.exists() and bureaux.exists():
            bureau_principal = bureaux.first()
            self.stdout.write(f"\nAssignation du bureau '{bureau_principal.nom}'...")
            
            for agent in agents_sans_bureau:
                agent.bureau = bureau_principal
                agent.save()
                self.stdout.write(f"  ✅ {agent.user.username} -> {bureau_principal.nom}")
            
            self.stdout.write(self.style.SUCCESS("✅ Correction terminée"))
        else:
            self.stdout.write(self.style.SUCCESS("✅ Aucune correction nécessaire"))
        
        # 4. Vérification finale
        self.stdout.write(f"\n=== VERIFICATION FINALE ===")
        agents = Agent.objects.all()
        for agent in agents:
            bureau_nom = agent.bureau.nom if agent.bureau else "AUCUN"
            self.stdout.write(f"  {agent.user.username}: {bureau_nom}")
        
        self.stdout.write("=== FIN ===")
