#!/usr/bin/env python
"""
Script pour résoudre le problème d'historique de migration incohérent.
Migration core.0030 appliquée avant core.0029.
"""

import os
import django
import sys

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ediligence.settings')
django.setup()

from django.db import connection

def fix_migration_history():
    """Corrige l'historique des migrations en supprimant et réappliquant les migrations problématiques."""
    
    print("🔧 Correction de l'historique des migrations...")
    
    with connection.cursor() as cursor:
        # Vérifier les migrations actuelles
        cursor.execute("""
            SELECT id, app, name, applied 
            FROM django_migrations 
            WHERE app = 'core' AND name IN ('0029_geofencesettings_pushnotificationtoken_geofencealert_and_more', '0030_alter_pushnotificationtoken_token')
            ORDER BY applied DESC
        """)
        
        migrations = cursor.fetchall()
        print(f"\n📋 Migrations trouvées : {len(migrations)}")
        for mig in migrations:
            print(f"   - ID: {mig[0]}, App: {mig[1]}, Name: {mig[2]}, Applied: {mig[3]}")
        
        if len(migrations) == 0:
            print("\n✅ Aucune migration problématique trouvée.")
            return
        
        # Supprimer la migration 0030 de l'historique
        print("\n🗑️  Suppression de la migration 0030 de l'historique...")
        cursor.execute("""
            DELETE FROM django_migrations 
            WHERE app = 'core' AND name = '0030_alter_pushnotificationtoken_token'
        """)
        deleted_count = cursor.rowcount
        print(f"   ✅ {deleted_count} enregistrement(s) supprimé(s)")
        
        # Vérifier si 0029 existe
        cursor.execute("""
            SELECT COUNT(*) 
            FROM django_migrations 
            WHERE app = 'core' AND name = '0029_geofencesettings_pushnotificationtoken_geofencealert_and_more'
        """)
        count_0029 = cursor.fetchone()[0]
        
        if count_0029 == 0:
            print("\n⚠️  La migration 0029 n'est pas dans l'historique.")
            print("   Vous devrez exécuter : python manage.py migrate core 0029")
        else:
            print("\n✅ La migration 0029 est présente dans l'historique.")
        
        print("\n✅ Correction terminée !")
        print("\n📝 Prochaines étapes :")
        print("   1. python manage.py makemigrations")
        print("   2. python manage.py migrate")

if __name__ == '__main__':
    try:
        fix_migration_history()
    except Exception as e:
        print(f"\n❌ Erreur : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
