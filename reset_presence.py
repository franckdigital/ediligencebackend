#!/usr/bin/env python
"""
Réinitialiser la présence pour retester
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ediligence.settings')
django.setup()

from core.models import Presence
from django.utils import timezone

presence = Presence.objects.filter(
    agent__user__username='franckalain',
    date_presence=timezone.now().date()
).first()

if presence:
    print("Réinitialisation de la présence...")
    presence.heure_sortie = None
    presence.sortie_detectee = False
    presence.statut = 'présent'
    presence.temps_absence_minutes = None
    presence.save()
    print("✅ Présence réinitialisée")
else:
    print("❌ Aucune présence trouvée")
