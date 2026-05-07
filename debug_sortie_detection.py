#!/usr/bin/env python
"""
Debug de la détection de sortie
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ediligence.settings')
django.setup()

from core.models import Presence, Agent, AgentLocation, Bureau
from django.utils import timezone
from datetime import timedelta

def debug_sortie():
    print("=" * 60)
    print("DEBUG DÉTECTION DE SORTIE")
    print("=" * 60)
    
    # 1. Vérifier la présence
    today = timezone.now().date()
    presence = Presence.objects.filter(
        agent__user__username='franckalain',
        date_presence=today
    ).first()
    
    if not presence:
        print("\n❌ Aucune présence trouvée pour franckalain aujourd'hui")
        return
    
    print(f"\n✅ Présence trouvée:")
    print(f"   Date: {presence.date_presence}")
    print(f"   Heure arrivée: {presence.heure_arrivee}")
    print(f"   Heure départ: {presence.heure_depart}")
    print(f"   Sortie détectée: {presence.sortie_detectee}")
    print(f"   Statut: {presence.statut}")
    
    # 2. Vérifier l'agent
    agent = presence.agent
    print(f"\n✅ Agent: {agent.user.username}")
    print(f"   Nom: {agent.nom} {agent.prenom}")
    print(f"   Bureau: {agent.bureau}")
    
    if not agent.bureau:
        print("\n❌ PROBLÈME: Agent n'a pas de bureau assigné!")
        print("   Solution: Assigner un bureau à l'agent")
        return
    
    bureau = agent.bureau
    print(f"\n✅ Bureau: {bureau.nom}")
    print(f"   Coordonnées: {bureau.latitude_centre}, {bureau.longitude_centre}")
    print(f"   Rayon: {bureau.rayon_metres}m")
    
    # 3. Vérifier les positions GPS
    locations = AgentLocation.objects.filter(
        agent__username='franckalain',
        timestamp__date=today
    ).order_by('timestamp')
    
    print(f"\n✅ Positions GPS aujourd'hui: {locations.count()}")
    
    if locations.count() == 0:
        print("\n❌ PROBLÈME: Aucune position GPS enregistrée!")
        return
    
    # 4. Analyser les positions
    from core.geofencing_utils import calculate_distance
    
    print("\n📍 Analyse des positions:")
    for loc in locations:
        distance = calculate_distance(
            float(loc.latitude),
            float(loc.longitude),
            float(bureau.latitude_centre),
            float(bureau.longitude_centre)
        )
        status = "✅ PROCHE" if distance <= 200 else "❌ LOIN"
        print(f"   {loc.timestamp.strftime('%H:%M:%S')} - {distance:.1f}m - {status}")
    
    # 5. Vérifier si Celery tourne
    print("\n🔍 Vérification Celery:")
    print("   Exécutez: sudo systemctl status celery")
    print("   Ou: celery -A ediligence inspect active")
    
    # 6. Tester manuellement la tâche
    print("\n🧪 Test manuel de la tâche:")
    print("   from core.tasks_presence import check_agent_exits")
    print("   check_agent_exits()")
    
    print("\n" + "=" * 60)

if __name__ == '__main__':
    debug_sortie()
