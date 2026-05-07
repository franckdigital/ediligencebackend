"""
Script pour corriger la dépendance de la migration 0033.
Change la dépendance de 0032_add_new_roles vers 0031_add_sortie_fields
"""

import os

migration_file = 'core/migrations/0033_alter_service_options_alter_service_direction_and_more.py'

print(f"Correction de la migration {migration_file}...")

# Lire le fichier
with open(migration_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Remplacer la dépendance
old_dependency = "('core', '0032_add_new_roles')"
new_dependency = "('core', '0031_add_sortie_fields')"

if old_dependency in content:
    content = content.replace(old_dependency, new_dependency)
    
    # Écrire le fichier modifié
    with open(migration_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Migration corrigee avec succes!")
    print(f"Ancienne dependance: {old_dependency}")
    print(f"Nouvelle dependance: {new_dependency}")
else:
    print("La dependance a deja ete corrigee ou n'existe pas.")
