from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Agent, Bureau

class Command(BaseCommand):
    help = 'Créer un bureau principal et assigner tous les agents'

    def handle(self, *args, **options):
        self.stdout.write("=== SETUP BUREAU PRINCIPAL ===")
        
        # 1. Vérifier les bureaux existants
        bureaux = Bureau.objects.all()
        self.stdout.write(f"Bureaux existants: {bureaux.count()}")
        
        if bureaux.exists():
            for bureau in bureaux:
                self.stdout.write(f"  - {bureau.nom} ({bureau.latitude_centre}, {bureau.longitude_centre})")
        
        # 2. Créer un bureau principal si aucun n'existe
        if not bureaux.exists():
            self.stdout.write("Création du bureau principal...")
            
            bureau_principal = Bureau.objects.create(
                nom="Bureau Principal",
                latitude_centre=5.396534,  # Coordonnées d'Abidjan
                longitude_centre=-3.981554,
                rayon_metres=200
            )
            
            self.stdout.write(f"✅ Bureau créé: {bureau_principal.nom}")
        else:
            bureau_principal = bureaux.first()
            self.stdout.write(f"✅ Bureau existant utilisé: {bureau_principal.nom}")
        
        # 3. Lister tous les agents
        agents = Agent.objects.all()
        self.stdout.write(f"\nAgents trouvés: {agents.count()}")
        
        if not agents.exists():
            self.stdout.write("⚠️ Aucun agent trouvé")
            return
        
        # 4. Assigner le bureau à tous les agents sans bureau
        agents_sans_bureau = agents.filter(bureau__isnull=True)
        self.stdout.write(f"Agents sans bureau: {agents_sans_bureau.count()}")
        
        if agents_sans_bureau.exists():
            self.stdout.write(f"Assignation du bureau '{bureau_principal.nom}'...")
            
            for agent in agents_sans_bureau:
                agent.bureau = bureau_principal
                agent.save()
                self.stdout.write(f"  ✅ {agent.user.username} -> {bureau_principal.nom}")
        
        # 5. Vérification finale
        self.stdout.write(f"\n=== VERIFICATION FINALE ===")
        agents = Agent.objects.all()
        
        for agent in agents:
            bureau_nom = agent.bureau.nom if agent.bureau else "AUCUN"
            self.stdout.write(f"  {agent.user.username}: {bureau_nom}")
        
        # 6. Statistiques
        total_agents = agents.count()
        agents_avec_bureau = agents.filter(bureau__isnull=False).count()
        
        self.stdout.write(f"\n📊 STATISTIQUES:")
        self.stdout.write(f"  Total agents: {total_agents}")
        self.stdout.write(f"  Avec bureau: {agents_avec_bureau}")
        self.stdout.write(f"  Sans bureau: {total_agents - agents_avec_bureau}")
        
        if agents_avec_bureau == total_agents:
            self.stdout.write(self.style.SUCCESS("🎯 SUCCÈS: Tous les agents ont un bureau !"))
        else:
            self.stdout.write(self.style.WARNING("⚠️ ATTENTION: Certains agents n'ont pas de bureau"))
        
        self.stdout.write("=== FIN ===")
