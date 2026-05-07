# Commandes à exécuter dans le shell Django
# Utilisez: python manage.py shell < debug_shell_commands.py

from core.models import Bureau, Agent
from django.contrib.auth.models import User
from decimal import Decimal

print("🔍 DIAGNOSTIC ASSIGNATION BUREAUX")
print("=" * 50)

# 1. Lister tous les bureaux
print("\n📍 TOUS LES BUREAUX:")
bureaux = Bureau.objects.all()
print(f"Nombre de bureaux: {bureaux.count()}")

for bureau in bureaux:
    print(f"   ID: {bureau.id}")
    print(f"   Nom: {bureau.nom}")
    print(f"   Lat: {bureau.latitude_centre}")
    print(f"   Lon: {bureau.longitude_centre}")
    print(f"   Rayon: {bureau.rayon_metres}m")
    print(f"   ---")

# 2. Trouver le bureau "Principal"
print("\n🏢 RECHERCHE BUREAU PRINCIPAL:")
bureau_principal = Bureau.objects.filter(nom__icontains='Principal').first()
if bureau_principal:
    print(f"   ✅ Trouvé: {bureau_principal.nom}")
    print(f"   Coordonnées: {bureau_principal.latitude_centre}, {bureau_principal.longitude_centre}")
else:
    print("   ❌ Aucun bureau 'Principal' trouvé")
    premier_bureau = Bureau.objects.first()
    if premier_bureau:
        print(f"   📍 Premier bureau: {premier_bureau.nom}")
        print(f"   Coordonnées: {premier_bureau.latitude_centre}, {premier_bureau.longitude_centre}")

# 3. Vérifier les agents et leurs bureaux assignés
print("\n👥 AGENTS ET LEURS BUREAUX:")
agents = Agent.objects.all()
for agent in agents:
    print(f"   Agent: {agent.nom} {agent.prenom}")
    if agent.bureau:
        print(f"   Bureau assigné: {agent.bureau.nom}")
        print(f"   Coordonnées: {agent.bureau.latitude_centre}, {agent.bureau.longitude_centre}")
    else:
        print(f"   ❌ Aucun bureau assigné")
    print(f"   ---")

# 4. Simuler la logique du serveur pour un utilisateur spécifique
print("\n🧪 SIMULATION LOGIQUE SERVEUR:")

# Prendre le premier utilisateur pour test
user = User.objects.first()
if user:
    print(f"   Utilisateur test: {user.username}")
    
    # Récupérer ou créer l'agent
    try:
        agent = Agent.objects.get(user=user)
        print(f"   Agent existant: {agent.nom}")
    except Agent.DoesNotExist:
        print(f"   ❌ Agent n'existe pas pour {user.username}")
        agent = None
    
    # Appliquer la logique du serveur
    if agent and agent.bureau:
        bureau_utilise = agent.bureau
        print(f"   🎯 Bureau utilisé: {bureau_utilise.nom} (bureau de l'agent)")
    else:
        bureau_utilise = Bureau.objects.filter(nom__icontains='Principal').first()
        if not bureau_utilise:
            bureau_utilise = Bureau.objects.first()
        print(f"   🎯 Bureau utilisé: {bureau_utilise.nom if bureau_utilise else 'AUCUN'} (fallback)")
    
    if bureau_utilise:
        print(f"   📍 Coordonnées utilisées: {bureau_utilise.latitude_centre}, {bureau_utilise.longitude_centre}")
        
        # Vérifier si ce sont les bonnes coordonnées
        expected_lat = Decimal('5.396534')
        expected_lon = Decimal('-3.981554')
        
        if (abs(bureau_utilise.latitude_centre - expected_lat) < Decimal('0.001') and 
            abs(bureau_utilise.longitude_centre - expected_lon) < Decimal('0.001')):
            print("   ✅ COORDONNÉES CORRECTES")
        else:
            print("   ❌ COORDONNÉES INCORRECTES")
            print(f"   📍 Attendu: {expected_lat}, {expected_lon}")
            print(f"   📍 Trouvé:  {bureau_utilise.latitude_centre}, {bureau_utilise.longitude_centre}")

print(f"\n🎯 RÉSUMÉ:")
print("Diagnostic terminé.")
