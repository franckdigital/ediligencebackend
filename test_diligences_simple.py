import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ediligence.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import Diligence, ImputationAccess
import traceback

try:
    user = User.objects.get(username='franck')
    print(f"User: {user.username} (ID: {user.id})")
    print(f"Profile role: {user.profile.role}")
    
    # Test basic diligence query
    print("\n=== Testing basic Diligence query ===")
    diligences = Diligence.objects.all()
    print(f"Total diligences: {diligences.count()}")
    
    # Test ImputationAccess query
    print("\n=== Testing ImputationAccess query ===")
    imputation_access = ImputationAccess.objects.filter(user=user)
    print(f"ImputationAccess for user: {imputation_access.count()}")
    
    # Test the specific query that might be causing issues
    print("\n=== Testing complex query ===")
    base_qs = Diligence.objects.select_related(
        'courrier',
        'courrier__service',
        'courrier__service__direction',
        'direction'
    ).prefetch_related(
        'agents',
        'services_concernes',
        'services_concernes__direction'
    ).all().order_by('-created_at')
    
    print(f"Base queryset count: {base_qs.count()}")
    
    # Test ImputationAccess filtering
    imputation_qs = base_qs.filter(imputation_access__user=user)
    print(f"ImputationAccess filtered count: {imputation_qs.count()}")
    
    # Test assigned diligences
    assigned_qs = base_qs.filter(agents=user)
    print(f"Assigned diligences count: {assigned_qs.count()}")
    
    print("\nAll queries executed successfully!")
    
except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()
