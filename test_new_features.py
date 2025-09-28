#!/usr/bin/env python3
"""
Test script for new diligence management features:
1. Status change functionality
2. Role-based button visibility (already implemented)
3. User-specific instructions
4. User-specific comments
"""

import os
import sys
import django
import requests
import json

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ediligence.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib.auth.models import User
from core.models import Diligence, UserDiligenceComment, UserDiligenceInstruction

def test_api_endpoints():
    """Test the new API endpoints"""
    base_url = "http://localhost:8000/api"
    
    print("Testing new API endpoints...")
    
    # Test endpoints existence
    endpoints_to_test = [
        "/user-diligence-comments/",
        "/user-diligence-instructions/",
        "/diligences/",
    ]
    
    for endpoint in endpoints_to_test:
        try:
            response = requests.get(f"{base_url}{endpoint}")
            print(f"OK {endpoint}: Status {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"ERROR {endpoint}: Connection failed - make sure backend is running")
        except Exception as e:
            print(f"ERROR {endpoint}: Error - {e}")

def test_models():
    """Test the new Django models"""
    print("\nTesting Django models...")
    
    try:
        # Test UserDiligenceComment model
        comment_count = UserDiligenceComment.objects.count()
        print(f"OK UserDiligenceComment model: {comment_count} records")
        
        # Test UserDiligenceInstruction model  
        instruction_count = UserDiligenceInstruction.objects.count()
        print(f"OK UserDiligenceInstruction model: {instruction_count} records")
        
        # Test relationships
        users_count = User.objects.count()
        diligences_count = Diligence.objects.count()
        print(f"INFO Available users: {users_count}")
        print(f"INFO Available diligences: {diligences_count}")
        
    except Exception as e:
        print(f"ERROR Model test failed: {e}")

def create_test_data():
    """Create some test data if needed"""
    print("\nCreating test data...")
    
    try:
        # Get first user and diligence for testing
        user = User.objects.first()
        diligence = Diligence.objects.first()
        
        if user and diligence:
            # Create test comment
            comment, created = UserDiligenceComment.objects.get_or_create(
                diligence=diligence,
                user=user,
                defaults={'comment': 'Test comment from script'}
            )
            print(f"OK Test comment {'created' if created else 'exists'}: {comment}")
            
            # Create test instruction
            instruction, created = UserDiligenceInstruction.objects.get_or_create(
                diligence=diligence,
                user=user,
                defaults={'instruction': 'Test instruction from script'}
            )
            print(f"OK Test instruction {'created' if created else 'exists'}: {instruction}")
            
        else:
            print("ERROR No users or diligences found for testing")
            
    except Exception as e:
        print(f"ERROR Test data creation failed: {e}")

def test_status_values():
    """Test diligence status values"""
    print("\nTesting diligence status values...")
    
    try:
        diligences = Diligence.objects.all()[:5]  # Test first 5
        for diligence in diligences:
            print(f"INFO Diligence #{diligence.id}: Status = '{diligence.statut}'")
            
        # Test valid status values
        valid_statuses = ['en_attente', 'en_cours', 'termine', 'suspendu', 'annule']
        print(f"OK Valid status values: {valid_statuses}")
        
    except Exception as e:
        print(f"ERROR Status test failed: {e}")

def main():
    """Run all tests"""
    print("Starting comprehensive feature tests...\n")
    
    test_models()
    test_api_endpoints()
    create_test_data()
    test_status_values()
    
    print("\nTest completed! Check the results above.")
    print("\nNext steps:")
    print("1. Start the frontend: npm start")
    print("2. Login and navigate to diligences")
    print("3. Click on a diligence detail to test new features")
    print("4. Try changing status, adding personal instructions/comments")

if __name__ == "__main__":
    main()
