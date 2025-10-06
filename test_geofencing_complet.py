#!/usr/bin/env python3
"""
Test complet du système de géofencing après correction des bureaux
"""
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ediligencebackend.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import Agent, Bureau, Presence, AgentLocation
from django.utils import timezone
from datetime import date, datetime, time

def test_geofencing_complet():
    """Test complet du système de géofencing"""
    
    print("🧪 TEST COMPLET GÉOFENCING APRÈS CORRECTION")
    print("=" * 60)
    
    # 1. Vérifier le bureau créé
    print("\n1. VERIFICATION BUREAU")
    print("-" * 30)
    
    bureaux = Bureau.objects.all()
    if bureaux.exists():
        bureau = bureaux.first()
        print(f"✅ Bureau trouvé: {bureau.nom}")
        print(f"   Coordonnées: {bureau.latitude_centre}, {bureau.longitude_centre}")
        print(f"   Rayon: {bureau.rayon_metres}m")
    else:
        print("❌ Aucun bureau trouvé")
        return
    
    # 2. Vérifier les utilisateurs
    print("\n2. VERIFICATION UTILISATEURS")
    print("-" * 30)
    
    users = ['angealain', 'franckalain']
    for username in users:
        try:
            user = User.objects.get(username=username)
            print(f"✅ Utilisateur {username} trouvé")
            
            # Vérifier l'agent
            try:
                agent = Agent.objects.get(user=user)
                bureau_nom = agent.bureau.nom if agent.bureau else "AUCUN"
                print(f"   Agent: {agent.nom} {agent.prenom}")
                print(f"   Bureau: {bureau_nom}")
            except Agent.DoesNotExist:
                print(f"   ❌ Agent non trouvé pour {username}")
                
        except User.DoesNotExist:
            print(f"❌ Utilisateur {username} non trouvé")
    
    # 3. Tester la tâche de détection
    print("\n3. TEST TACHE DETECTION")
    print("-" * 30)
    
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
    
    print(f"Heure actuelle: {current_time.strftime('%H:%M:%S')}")
    print(f"Heures de travail: {is_work_hours}")
    
    if is_work_hours:
        print("✅ Dans les heures de travail - Test de la tâche...")
        
        try:
            from core.tasks_presence import check_agent_exits
            
            # Exécuter la tâche
            print("Exécution de check_agent_exits()...")
            result = check_agent_exits()
            print(f"✅ Tâche exécutée avec succès")
            
        except Exception as e:
            print(f"❌ Erreur lors de l'exécution: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("⏰ Hors heures de travail - Tâche non testée")
    
    # 4. Vérifier les présences d'aujourd'hui
    print("\n4. PRESENCES AUJOURD'HUI")
    print("-" * 30)
    
    today = date.today()
    presences = Presence.objects.filter(date_presence=today)
    
    if presences.exists():
        print(f"Présences trouvées: {presences.count()}")
        for presence in presences:
            agent = presence.agent
            bureau_info = f"Bureau: {agent.bureau.nom}" if agent.bureau else "AUCUN BUREAU"
            print(f"   {agent.user.username}: {presence.statut} - {bureau_info}")
            print(f"      Arrivée: {presence.heure_arrivee}")
            print(f"      Sortie détectée: {presence.sortie_detectee}")
    else:
        print("Aucune présence aujourd'hui")
    
    # 5. Instructions pour le test réel
    print("\n5. INSTRUCTIONS POUR TEST REEL")
    print("-" * 30)
    
    print("Pour tester avec angealain:")
    print("1. Connectez-vous avec angealain sur l'app mobile")
    print("2. Pointez votre arrivée (le bureau sera assigné automatiquement)")
    print("3. Éloignez-vous de plus de 200m du bureau")
    print("4. Attendez 5 minutes (mode test)")
    print("5. Vérifiez que la sortie est détectée automatiquement")
    
    print(f"\n📍 Coordonnées du bureau pour référence:")
    print(f"   Latitude: {bureau.latitude_centre}")
    print(f"   Longitude: {bureau.longitude_centre}")
    print(f"   Rayon autorisé: {bureau.rayon_metres}m")
    
    print("\n✅ SYSTÈME PRÊT POUR LE TEST RÉEL")

if __name__ == "__main__":
    test_geofencing_complet()
