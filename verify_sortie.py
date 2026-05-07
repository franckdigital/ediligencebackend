#!/usr/bin/env python
"""
Vérifier que la sortie a été enregistrée
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

print("=" * 60)
print("VÉRIFICATION DE LA SORTIE")
print("=" * 60)
print(f"\n✅ Présence:")
print(f"   Heure arrivée: {presence.heure_arrivee}")
print(f"   Heure sortie: {presence.heure_sortie}")
print(f"   Sortie détectée: {presence.sortie_detectee}")
print(f"   Statut: {presence.statut}")
print(f"   Temps absence: {presence.temps_absence_minutes} minutes")
print("\n" + "=" * 60)
