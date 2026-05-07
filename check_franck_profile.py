import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ediligence.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import UserProfile

try:
    user = User.objects.get(username='franck')
    print(f'User: {user.username} (ID: {user.id})')
    print(f'Has profile: {hasattr(user, "profile")}')
    
    if hasattr(user, 'profile'):
        profile = user.profile
        print(f'Profile role: {profile.role}')
        print(f'Profile service: {profile.service}')
        print(f'Profile service direction: {profile.service.direction if profile.service else None}')
    else:
        print('No profile found - checking UserProfile table')
        profiles = UserProfile.objects.filter(user=user)
        print(f'UserProfile count for user: {profiles.count()}')
        if profiles.exists():
            profile = profiles.first()
            print(f'Found profile: role={profile.role}, service={profile.service}')
        
except User.DoesNotExist:
    print('User franck not found')
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
