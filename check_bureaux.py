from django.contrib.auth.models import User
from core.models import Agent, Bureau, Presence
from datetime import date

print("=== DIAGNOSTIC BUREAUX ET AGENTS ===")

# 1. Bureaux disponibles
print("\n1. BUREAUX DISPONIBLES:")
bureaux = Bureau.objects.all()
for bureau in bureaux:
    print(f"   {bureau.id}: {bureau.nom} - Coord: {bureau.latitude_centre}, {bureau.longitude_centre}")

# 2. Agents et leurs bureaux
print(f"\n2. AGENTS ET BUREAUX:")
agents = Agent.objects.all()
agents_sans_bureau = []

for agent in agents:
    if agent.bureau:
        print(f"   ✅ {agent.user.username} -> {agent.bureau.nom}")
    else:
        print(f"   ❌ {agent.user.username} -> AUCUN BUREAU")
        agents_sans_bureau.append(agent)

print(f"\nAgents sans bureau: {len(agents_sans_bureau)}")

# 3. Corriger les assignations si nécessaire
if agents_sans_bureau and bureaux.exists():
    bureau_principal = bureaux.first()
    print(f"\n3. CORRECTION - Assignation bureau '{bureau_principal.nom}':")
    
    for agent in agents_sans_bureau:
        agent.bureau = bureau_principal
        agent.save()
        print(f"   ✅ {agent.user.username} assigné à {bureau_principal.nom}")
    
    print(f"✅ {len(agents_sans_bureau)} agents corrigés")
else:
    print("\n3. Aucune correction nécessaire")

# 4. Vérification finale
print(f"\n4. VERIFICATION FINALE:")
agents_sans_bureau_final = Agent.objects.filter(bureau__isnull=True)
if agents_sans_bureau_final.exists():
    print(f"❌ {agents_sans_bureau_final.count()} agents encore sans bureau")
else:
    print("✅ Tous les agents ont maintenant un bureau")

print("\n=== FIN DIAGNOSTIC ===")
