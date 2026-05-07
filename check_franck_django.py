#!/usr/bin/env python3
"""
Vérifications Django pour franck.alain
Usage: python manage.py shell < check_franck_django.py
Ou copier-coller dans le shell Django
"""

# 1. Importer les modèles
from django.contrib.auth.models import User
from core.models import Agent, Bureau, Presence, AgentLocation
from django.utils import timezone
from core.geofencing_utils import calculate_distance
from datetime import datetime, timedelta

print("🔍 DIAGNOSTIC FRANCK.ALAIN")
print("=" * 50)

# 2. Vérifier l'utilisateur
try:
    user = User.objects.get(username='franck.alain')
    print(f"✅ Utilisateur: {user.username} (ID: {user.id})")
    print(f"   Email: {user.email}")
    print(f"   Actif: {user.is_active}")
except User.DoesNotExist:
    print("❌ Utilisateur 'franck.alain' non trouvé")
    print("Utilisateurs disponibles:")
    for u in User.objects.all()[:10]:
        print(f"   - {u.username}")
    exit()

# 3. Vérifier l'agent
try:
    agent = Agent.objects.get(user=user)
    print(f"✅ Agent: {agent.nom} {agent.prenom}")
    print(f"   Service ID: {agent.service_id}")
    print(f"   Bureau ID: {agent.bureau_id}")
    print(f"   Matricule: {agent.matricule}")
except Agent.DoesNotExist:
    print("❌ Agent non trouvé pour cet utilisateur")
    exit()

# 4. Vérifier le bureau
if agent.bureau:
    bureau = agent.bureau
    print(f"✅ Bureau: {bureau.nom}")
    print(f"   Latitude: {bureau.latitude_centre}")
    print(f"   Longitude: {bureau.longitude_centre}")
    print(f"   Adresse: {bureau.adresse}")
    
    if not bureau.latitude_centre or not bureau.longitude_centre:
        print("❌ PROBLÈME: Coordonnées GPS manquantes!")
else:
    print("❌ PROBLÈME: Aucun bureau assigné!")

# 5. Vérifier la présence d'aujourd'hui
today = timezone.now().date()
print(f"\n📅 PRÉSENCE DU {today}")
print("-" * 30)

try:
    presence = Presence.objects.get(agent=agent, date_presence=today)
    print(f"✅ Présence trouvée:")
    print(f"   Arrivée: {presence.heure_arrivee}")
    print(f"   Départ: {presence.heure_depart}")
    print(f"   Sortie: {presence.heure_sortie}")
    print(f"   Statut: {presence.statut}")
    print(f"   Sortie détectée: {presence.sortie_detectee}")
    print(f"   Commentaire: {presence.commentaire}")
except Presence.DoesNotExist:
    print("❌ Aucune présence pour aujourd'hui")
    # Vérifier les présences récentes
    recent = Presence.objects.filter(agent=agent).order_by('-date_presence')[:5]
    print("Présences récentes:")
    for p in recent:
        print(f"   {p.date_presence}: {p.statut}")

# 6. Vérifier les positions GPS
print(f"\n📍 POSITIONS GPS DU {today}")
print("-" * 30)

locations = AgentLocation.objects.filter(
    agent=user,  # AgentLocation utilise User
    timestamp__date=today
).order_by('timestamp')

print(f"Nombre de positions: {locations.count()}")

if locations.exists() and agent.bureau and agent.bureau.latitude_centre:
    print("\nAnalyse des positions:")
    for i, loc in enumerate(locations):
        distance = calculate_distance(
            float(loc.latitude),
            float(loc.longitude),
            float(agent.bureau.latitude_centre),
            float(agent.bureau.longitude_centre)
        )
        
        status = "🏢" if distance <= 200 else f"🚶 ({distance:.0f}m)"
        if distance > 10000:
            status = f"🤖 ÉMULATEUR ({distance:.0f}m)"
        
        print(f"  {i+1:2d}. {loc.timestamp.strftime('%H:%M:%S')} {status}")
        
        # Première position éloignée
        if i == 0 and distance > 200 and distance <= 10000:
            now = timezone.now()
            duration = now - loc.timestamp
            print(f"      ⏱️ Première sortie il y a {duration.total_seconds()/60:.1f} min")

# 7. Test manuel de la logique
print(f"\n🧪 TEST DE LA LOGIQUE")
print("-" * 30)

if locations.exists() and agent.bureau:
    last_location = locations.last()
    distance = calculate_distance(
        float(last_location.latitude),
        float(last_location.longitude),
        float(agent.bureau.latitude_centre),
        float(agent.bureau.longitude_centre)
    )
    
    print(f"Dernière position: {last_location.timestamp.strftime('%H:%M:%S')}")
    print(f"Distance: {distance:.1f}m")
    
    if distance > 200:
        # Chercher depuis combien de temps
        away_positions = locations.filter(timestamp__gte=timezone.now() - timedelta(minutes=10))
        all_away = True
        
        for pos in away_positions:
            pos_distance = calculate_distance(
                float(pos.latitude),
                float(pos.longitude),
                float(agent.bureau.latitude_centre),
                float(agent.bureau.longitude_centre)
            )
            if pos_distance <= 200:
                all_away = False
                break
        
        print(f"Toujours éloigné depuis 10 min: {all_away}")
        
        if all_away:
            print("✅ CONDITIONS REMPLIES pour détection automatique")
        else:
            print("❌ Agent revenu au bureau récemment")
    else:
        print("ℹ️ Agent actuellement au bureau")

print(f"\n🔧 COMMANDES UTILES:")
print("# Forcer la détection manuellement:")
print("from core.tasks_presence import check_agent_exits")
print("check_agent_exits()")
print("\n# Vérifier les tâches Celery:")
print("from django_celery_beat.models import PeriodicTask")
print("PeriodicTask.objects.filter(name__contains='check_agent')")
