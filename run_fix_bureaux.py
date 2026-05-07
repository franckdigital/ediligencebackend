import os
import sys
import django

# Ajouter le répertoire du projet au path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ediligencebackend.settings')
django.setup()

# Maintenant importer les modèles
from django.contrib.auth.models import User
from core.models import Agent, Bureau

print("=== CORRECTION BUREAUX AGENTS ===")

# 1. Lister les bureaux
bureaux = Bureau.objects.all()
print(f"Bureaux disponibles: {bureaux.count()}")
for bureau in bureaux:
    print(f"  - {bureau.nom}")

# 2. Vérifier les agents sans bureau
agents_sans_bureau = Agent.objects.filter(bureau__isnull=True)
print(f"\nAgents sans bureau: {agents_sans_bureau.count()}")
for agent in agents_sans_bureau:
    print(f"  - {agent.user.username}")

# 3. Corriger si nécessaire
if agents_sans_bureau.exists() and bureaux.exists():
    bureau_principal = bureaux.first()
    print(f"\nAssignation du bureau '{bureau_principal.nom}'...")
    
    for agent in agents_sans_bureau:
        agent.bureau = bureau_principal
        agent.save()
        print(f"  ✅ {agent.user.username} -> {bureau_principal.nom}")
    
    print("✅ Correction terminée")
else:
    print("✅ Aucune correction nécessaire")

# 4. Vérification finale
print(f"\n=== VERIFICATION FINALE ===")
agents = Agent.objects.all()
for agent in agents:
    bureau_nom = agent.bureau.nom if agent.bureau else "AUCUN"
    print(f"  {agent.user.username}: {bureau_nom}")

print("=== FIN ===")
