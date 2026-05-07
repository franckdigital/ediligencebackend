#!/usr/bin/env python
"""
Script pour tester les URLs de l'API des présences
"""
import os
import django
import sys

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ediligence.settings')
django.setup()

from django.urls import reverse, resolve
from django.test import Client
from django.contrib.auth.models import User
from core.models import Presence, Agent
from datetime import date

def test_presence_urls():
    """Tester les URLs des presences"""
    print("Test des URLs des presences...")
    
    # Test 1: URL du ViewSet des presences
    try:
        # Les ViewSets generent automatiquement les URLs
        print("ViewSet presences: /api/presences/")
        print("Detail presences: /api/presences/{id}/")
    except Exception as e:
        print(f"Erreur ViewSet: {e}")
    
    # Test 2: URL custom update-status
    try:
        url = reverse('update-presence-status', kwargs={'presence_id': 1})
        print(f"Update status URL: {url}")
    except Exception as e:
        print(f"Erreur update-status: {e}")
    
    # Test 3: Verifier si les presences existent
    try:
        presences_count = Presence.objects.count()
        print(f"Nombre de presences en base: {presences_count}")
        
        if presences_count > 0:
            first_presence = Presence.objects.first()
            print(f"Premiere presence ID: {first_presence.id}")
            
            # Tester l'URL avec un ID reel
            url = reverse('update-presence-status', kwargs={'presence_id': first_presence.id})
            print(f"URL reelle: {url}")
            
    except Exception as e:
        print(f"Erreur base de donnees: {e}")

if __name__ == "__main__":
    test_presence_urls()
