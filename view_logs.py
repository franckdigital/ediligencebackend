import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ediligencebackend.settings')
django.setup()

from core.models import Presence
from datetime import datetime, timedelta

print("=== DERNIÈRES PRÉSENCES ===")
for p in Presence.objects.all().order_by('-created_at')[:10]:
    print(f"{p.date_presence} | {p.agent.username} | Arrivée: {p.heure_arrivee} | Départ: {p.heure_depart} | Sortie: {'OUI' if p.sortie_detectee else 'NON'}")

print("\n=== SORTIES DÉTECTÉES ===")
for s in Presence.objects.filter(sortie_detectee=True).order_by('-created_at')[:10]:
    print(f"{s.date_presence} | {s.agent.username} | Sortie à: {s.heure_sortie}")