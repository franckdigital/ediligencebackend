import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ediligence.settings')
django.setup()

from django.contrib.auth.models import User
from core.views import DiligenceViewSet
from django.test import RequestFactory
from rest_framework_simplejwt.tokens import RefreshToken
import traceback

try:
    # Create a mock request
    factory = RequestFactory()
    user = User.objects.get(username='franck')
    
    # Create a GET request to /api/diligences/
    request = factory.get('/api/diligences/')
    request.user = user
    
    # Create the viewset instance
    viewset = DiligenceViewSet()
    viewset.request = request
    viewset.format_kwarg = None
    
    print(f"Testing DiligenceViewSet.get_queryset() for user: {user.username}")
    
    # Call get_queryset directly to see what happens
    queryset = viewset.get_queryset()
    print(f"Queryset returned successfully with {queryset.count()} items")
    
    # Try to evaluate the queryset
    list(queryset)
    print("Queryset evaluation successful")
    
except Exception as e:
    print(f"Error in get_queryset: {e}")
    traceback.print_exc()
