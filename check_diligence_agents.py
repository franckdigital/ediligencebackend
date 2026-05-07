import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ediligence.settings')
django.setup()

from core.models import Diligence, User

d = Diligence.objects.get(id=1)
print('Diligence MF2025CA001 agents:')
for agent in d.agents.all():
    print(f'- {agent.username} (ID: {agent.id})')

print(f'\nTotal agents assignés: {d.agents.count()}')

# Assigner la diligence uniquement à franck (ID 9)
franck = User.objects.get(id=9)
print(f'\nAssignation de la diligence uniquement à {franck.username}...')

# Vider les agents actuels et assigner seulement franck
d.agents.clear()
d.agents.add(franck)

print('Nouveaux agents assignés:')
for agent in d.agents.all():
    print(f'- {agent.username} (ID: {agent.id})')
