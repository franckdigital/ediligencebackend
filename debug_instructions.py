#!/usr/bin/env python3
"""
Script pour déboguer les instructions personnelles
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ediligence.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib.auth.models import User
from core.models import UserDiligenceInstruction, Diligence

def debug_instructions():
    print("=== DEBUG INSTRUCTIONS PERSONNELLES ===\n")
    
    # Vérifier les objets UserDiligenceInstruction
    instructions = UserDiligenceInstruction.objects.all()
    print(f"Nombre d'instructions en base: {instructions.count()}")
    
    for instruction in instructions[:5]:
        print(f"ID: {instruction.id}")
        print(f"User: {instruction.user.username}")
        print(f"Diligence: {instruction.diligence.id}")
        print(f"Instruction: {instruction.instruction[:100]}...")
        print("---")
    
    # Vérifier les utilisateurs
    users = User.objects.all()
    print(f"\nUtilisateurs disponibles: {users.count()}")
    for user in users[:3]:
        print(f"- {user.username} (ID: {user.id})")
    
    # Vérifier les diligences
    diligences = Diligence.objects.all()
    print(f"\nDiligences disponibles: {diligences.count()}")
    for diligence in diligences[:3]:
        print(f"- Diligence #{diligence.id} - {diligence.reference_courrier}")

if __name__ == "__main__":
    debug_instructions()
