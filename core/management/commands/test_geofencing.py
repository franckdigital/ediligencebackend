from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Agent, Bureau, Presence, AgentLocation
from django.utils import timezone
from datetime import date, datetime, time

class Command(BaseCommand):
    help = 'Test complet du système de géofencing'

    def handle(self, *args, **options):
        self.stdout.write("🧪 TEST COMPLET GÉOFENCING APRÈS CORRECTION")
        self.stdout.write("=" * 60)
        
        # 1. Vérifier le bureau créé
        self.stdout.write("\n1. VERIFICATION BUREAU")
        self.stdout.write("-" * 30)
        
        bureaux = Bureau.objects.all()
        if bureaux.exists():
            bureau = bureaux.first()
            self.stdout.write(f"✅ Bureau trouvé: {bureau.nom}")
            self.stdout.write(f"   Coordonnées: {bureau.latitude_centre}, {bureau.longitude_centre}")
            self.stdout.write(f"   Rayon: {bureau.rayon_metres}m")
        else:
            self.stdout.write("❌ Aucun bureau trouvé")
            return
        
        # 2. Vérifier les utilisateurs
        self.stdout.write("\n2. VERIFICATION UTILISATEURS")
        self.stdout.write("-" * 30)
        
        users = ['angealain', 'franckalain']
        for username in users:
            try:
                user = User.objects.get(username=username)
                self.stdout.write(f"✅ Utilisateur {username} trouvé")
                
                # Vérifier l'agent
                try:
                    agent = Agent.objects.get(user=user)
                    bureau_nom = agent.bureau.nom if agent.bureau else "AUCUN"
                    self.stdout.write(f"   Agent: {agent.nom} {agent.prenom}")
                    self.stdout.write(f"   Bureau: {bureau_nom}")
                except Agent.DoesNotExist:
                    self.stdout.write(f"   ❌ Agent non trouvé pour {username}")
                    
            except User.DoesNotExist:
                self.stdout.write(f"❌ Utilisateur {username} non trouvé")
        
        # 3. Tester la tâche de détection
        self.stdout.write("\n3. TEST TACHE DETECTION")
        self.stdout.write("-" * 30)
        
        # Vérifier l'heure actuelle
        now = timezone.now()
        current_time = now.time()
        
        morning_start = time(7, 30)
        morning_end = time(12, 30)
        afternoon_start = time(13, 30)
        afternoon_end = time(23, 59)
        
        is_morning = morning_start <= current_time <= morning_end
        is_afternoon = afternoon_start <= current_time <= afternoon_end
        is_work_hours = is_morning or is_afternoon
        
        self.stdout.write(f"Heure actuelle: {current_time.strftime('%H:%M:%S')}")
        self.stdout.write(f"Heures de travail: {is_work_hours}")
        
        if is_work_hours:
            self.stdout.write("✅ Dans les heures de travail - Test de la tâche...")
            
            try:
                from core.tasks_presence import check_agent_exits
                
                # Exécuter la tâche
                self.stdout.write("Exécution de check_agent_exits()...")
                result = check_agent_exits()
                self.stdout.write("✅ Tâche exécutée avec succès")
                
            except Exception as e:
                self.stdout.write(f"❌ Erreur lors de l'exécution: {e}")
                import traceback
                traceback.print_exc()
        else:
            self.stdout.write("⏰ Hors heures de travail - Tâche non testée")
        
        # 4. Vérifier les présences d'aujourd'hui
        self.stdout.write("\n4. PRESENCES AUJOURD'HUI")
        self.stdout.write("-" * 30)
        
        today = date.today()
        presences = Presence.objects.filter(date_presence=today)
        
        if presences.exists():
            self.stdout.write(f"Présences trouvées: {presences.count()}")
            for presence in presences:
                agent = presence.agent
                bureau_info = f"Bureau: {agent.bureau.nom}" if agent.bureau else "AUCUN BUREAU"
                self.stdout.write(f"   {agent.user.username}: {presence.statut} - {bureau_info}")
                self.stdout.write(f"      Arrivée: {presence.heure_arrivee}")
                self.stdout.write(f"      Sortie détectée: {presence.sortie_detectee}")
        else:
            self.stdout.write("Aucune présence aujourd'hui")
        
        # 5. Instructions pour le test réel
        self.stdout.write("\n5. INSTRUCTIONS POUR TEST REEL")
        self.stdout.write("-" * 30)
        
        self.stdout.write("Pour tester avec angealain:")
        self.stdout.write("1. Connectez-vous avec angealain sur l'app mobile")
        self.stdout.write("2. Pointez votre arrivée (le bureau sera assigné automatiquement)")
        self.stdout.write("3. Éloignez-vous de plus de 200m du bureau")
        self.stdout.write("4. Attendez 5 minutes (mode test)")
        self.stdout.write("5. Vérifiez que la sortie est détectée automatiquement")
        
        self.stdout.write(f"\n📍 Coordonnées du bureau pour référence:")
        self.stdout.write(f"   Latitude: {bureau.latitude_centre}")
        self.stdout.write(f"   Longitude: {bureau.longitude_centre}")
        self.stdout.write(f"   Rayon autorisé: {bureau.rayon_metres}m")
        
        self.stdout.write(self.style.SUCCESS("\n✅ SYSTÈME PRÊT POUR LE TEST RÉEL"))
