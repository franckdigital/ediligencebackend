#!/usr/bin/env python
"""
Script de test pour le système de suivi des sorties automatiques
"""
import os
import django
import sys
from datetime import datetime, timedelta, time
from decimal import Decimal

# Configuration Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ediligence.settings')
django.setup()

from django.utils import timezone
from core.models import Presence, Agent, Bureau, AgentLocation, User
from core.geofencing_utils import calculate_distance

def create_test_data():
    """Créer des données de test pour le système de sortie"""
    print("🔧 Création des données de test...")
    
    # Créer un bureau de test
    bureau, created = Bureau.objects.get_or_create(
        nom="Bureau Test",
        defaults={
            'latitude_centre': Decimal('5.396534'),
            'longitude_centre': Decimal('-3.981554'),
            'rayon_metres': 200
        }
    )
    
    if created:
        print(f"✅ Bureau créé: {bureau.nom}")
    else:
        print(f"📍 Bureau existant: {bureau.nom}")
    
    # Créer un utilisateur de test
    user, created = User.objects.get_or_create(
        username="agent_test",
        defaults={
            'email': 'agent.test@example.com',
            'first_name': 'Agent',
            'last_name': 'Test'
        }
    )
    
    if created:
        print(f"✅ Utilisateur créé: {user.username}")
    else:
        print(f"👤 Utilisateur existant: {user.username}")
    
    # Créer un agent de test
    agent, created = Agent.objects.get_or_create(
        user=user,
        defaults={
            'nom': 'Test',
            'prenom': 'Agent',
            'matricule': 'T001',
            'bureau': bureau
        }
    )
    
    if created:
        print(f"✅ Agent créé: {agent.nom} {agent.prenom}")
    else:
        print(f"👨‍💼 Agent existant: {agent.nom} {agent.prenom}")
    
    return bureau, agent

def simulate_agent_movement(agent, bureau):
    """Simuler le mouvement d'un agent qui s'éloigne du bureau"""
    print("\n🚶 Simulation du mouvement de l'agent...")
    
    current_time = timezone.now()
    current_date = current_time.date()
    
    # Créer une présence pour aujourd'hui
    presence, created = Presence.objects.get_or_create(
        agent=agent,
        date_presence=current_date,
        defaults={
            'heure_arrivee': time(8, 0),  # Arrivée à 8h00
            'statut': 'présent',
            'latitude': bureau.latitude_centre,
            'longitude': bureau.longitude_centre,
            'localisation_valide': True
        }
    )
    
    if created:
        print(f"✅ Présence créée pour {agent.nom}")
    else:
        print(f"📅 Présence existante pour {agent.nom}")
    
    # Simuler des positions de l'agent
    positions = [
        # Position au bureau (0m)
        {
            'lat': float(bureau.latitude_centre),
            'lon': float(bureau.longitude_centre),
            'time_offset': -120,  # Il y a 2 heures
            'description': 'Au bureau'
        },
        # Position légèrement éloignée (50m)
        {
            'lat': float(bureau.latitude_centre) + 0.0005,
            'lon': float(bureau.longitude_centre) + 0.0005,
            'time_offset': -90,  # Il y a 1h30
            'description': 'Proche du bureau (50m)'
        },
        # Position éloignée (300m) - début de sortie
        {
            'lat': float(bureau.latitude_centre) + 0.003,
            'lon': float(bureau.longitude_centre) + 0.003,
            'time_offset': -70,  # Il y a 1h10
            'description': 'Éloigné du bureau (300m)'
        },
        # Position très éloignée (500m) - sortie confirmée
        {
            'lat': float(bureau.latitude_centre) + 0.005,
            'lon': float(bureau.longitude_centre) + 0.005,
            'time_offset': -60,  # Il y a 1h
            'description': 'Très éloigné du bureau (500m)'
        },
        # Position actuelle - toujours éloigné
        {
            'lat': float(bureau.latitude_centre) + 0.005,
            'lon': float(bureau.longitude_centre) + 0.005,
            'time_offset': 0,  # Maintenant
            'description': 'Position actuelle (500m)'
        }
    ]
    
    print("\n📍 Création des positions de l'agent:")
    for pos in positions:
        timestamp = current_time + timedelta(minutes=pos['time_offset'])
        
        # Calculer la distance
        distance = calculate_distance(
            pos['lat'], pos['lon'],
            float(bureau.latitude_centre), float(bureau.longitude_centre)
        )
        
        # Créer la position (AgentLocation attend un User, pas un Agent)
        location = AgentLocation.objects.create(
            agent=agent.user,  # Utiliser agent.user au lieu de agent
            latitude=Decimal(str(pos['lat'])),
            longitude=Decimal(str(pos['lon'])),
            timestamp=timestamp
        )
        
        print(f"   {timestamp.strftime('%H:%M')} - {pos['description']} - Distance: {distance:.1f}m")
    
    return presence

def test_sortie_detection(presence, bureau):
    """Tester la détection de sortie"""
    print("\n🔍 Test de la détection de sortie...")
    
    # Importer la tâche de vérification
    from core.tasks_presence import check_agent_exits
    
    # Exécuter la tâche de vérification
    print("⚙️ Exécution de la tâche check_agent_exits...")
    check_agent_exits()
    
    # Vérifier le résultat
    presence.refresh_from_db()
    
    print(f"\n📊 Résultats après vérification:")
    print(f"   Statut: {presence.statut}")
    print(f"   Sortie détectée: {presence.sortie_detectee}")
    print(f"   Heure de sortie: {presence.heure_sortie}")
    print(f"   Temps d'absence: {presence.temps_absence_minutes} minutes")
    print(f"   Commentaire: {presence.commentaire}")
    
    if presence.sortie_detectee:
        print("✅ Sortie détectée avec succès!")
        print("🔒 Le bouton 'Pointer Départ' devrait être grisé sur l'application mobile")
    else:
        print("❌ Sortie non détectée")
    
    return presence.sortie_detectee

def test_status_change(presence):
    """Tester le changement de statut par un supérieur"""
    print("\n👨‍💼 Test du changement de statut par un supérieur...")
    
    # Simuler un changement de statut de 'absent' vers 'présent'
    if presence.statut == 'absent':
        presence.statut = 'présent'
        presence.sortie_detectee = False
        presence.heure_sortie = None
        presence.temps_absence_minutes = None
        presence.save()
        
        print("✅ Statut changé de 'absent' vers 'présent'")
        print("🔓 Le bouton 'Pointer Départ' devrait être réactivé sur l'application mobile")
    else:
        print("ℹ️ L'agent n'était pas marqué comme absent")

def main():
    """Fonction principale de test"""
    print("🚀 DÉBUT DU TEST DU SYSTÈME DE SUIVI DES SORTIES")
    print("=" * 60)
    
    try:
        # 1. Créer les données de test
        bureau, agent = create_test_data()
        
        # 2. Simuler le mouvement de l'agent
        presence = simulate_agent_movement(agent, bureau)
        
        # 3. Tester la détection de sortie
        sortie_detectee = test_sortie_detection(presence, bureau)
        
        # 4. Tester le changement de statut
        if sortie_detectee:
            test_status_change(presence)
        
        print("\n" + "=" * 60)
        print("✅ TEST TERMINÉ AVEC SUCCÈS")
        
    except Exception as e:
        print(f"\n❌ ERREUR LORS DU TEST: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
