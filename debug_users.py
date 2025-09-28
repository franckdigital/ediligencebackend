import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ediligence.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import UserProfile

users = User.objects.all()
for u in users:
    print(f'User {u.id} ({u.username}):')
    print(f'  - has profile: {hasattr(u, "profile")}')
    if hasattr(u, 'profile'):
        print(f'  - role: {u.profile.role}')
        print(f'  - service: {u.profile.service.id if u.profile.service else "NO_SERVICE"}')
        print(f'  - service name: {u.profile.service.nom if u.profile.service else "NO_SERVICE"}')
        if u.profile.service and u.profile.service.direction:
            print(f'  - direction: {u.profile.service.direction.id} ({u.profile.service.direction.nom})')
        else:
            print(f'  - direction: NO_DIRECTION')
    else:
        print('  - NO PROFILE')
    print()
