#!/usr/bin/env python
"""
Test manuel de la détection de sortie
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ediligence.settings')
django.setup()

from core.tasks_presence import check_agent_exits

print("=" * 60)
print("TEST MANUEL DE LA DÉTECTION DE SORTIE")
print("=" * 60)
print("\nExécution de check_agent_exits()...\n")

# Exécuter la tâche
result = check_agent_exits()

print("\n" + "=" * 60)
print("TEST TERMINÉ")
print("=" * 60)
