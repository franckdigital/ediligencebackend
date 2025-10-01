#!/usr/bin/env python
"""
Script pour résoudre le conflit de migration géofencing
"""
import os
import sys
import django
from django.conf import settings
from django.core.management import execute_from_command_line

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ediligencebackend.settings')
django.setup()

from django.db import connection
from django.core.management.commands.migrate import Command as MigrateCommand

def check_table_exists(table_name):
    """Vérifier si une table existe"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*)
            FROM information_schema.tables 
            WHERE table_schema = %s 
            AND table_name = %s
        """, [connection.settings_dict['NAME'], table_name])
        return cursor.fetchone()[0] > 0

def main():
    print("🔍 Vérification des tables géofencing...")
    
    tables_to_check = [
        'core_geofencesettings',
        'core_geofencealert', 
        'core_agentlocation',
        'core_pushnotificationtoken'
    ]
    
    existing_tables = []
    for table in tables_to_check:
        if check_table_exists(table):
            existing_tables.append(table)
            print(f"✅ Table {table} existe déjà")
        else:
            print(f"❌ Table {table} n'existe pas")
    
    if existing_tables:
        print(f"\n⚠️  {len(existing_tables)} tables existent déjà dans la base de données")
        print("📋 Solutions possibles:")
        print("1. Marquer les migrations comme appliquées (fake)")
        print("2. Supprimer les tables et refaire la migration")
        print("3. Créer une migration personnalisée")
        
        choice = input("\nChoisissez une option (1/2/3): ").strip()
        
        if choice == "1":
            print("🔄 Marquage des migrations comme appliquées...")
            os.system("python manage.py migrate core 0030 --fake")
            print("✅ Migrations marquées comme appliquées")
            
        elif choice == "2":
            confirm = input("⚠️  Êtes-vous sûr de vouloir supprimer les tables ? (oui/non): ")
            if confirm.lower() == 'oui':
                print("🗑️  Suppression des tables...")
                with connection.cursor() as cursor:
                    for table in existing_tables:
                        cursor.execute(f"DROP TABLE IF EXISTS {table}")
                        print(f"🗑️  Table {table} supprimée")
                print("🔄 Relancement de la migration...")
                os.system("python manage.py migrate")
            else:
                print("❌ Opération annulée")
                
        elif choice == "3":
            print("📝 Création d'une migration personnalisée...")
            print("Vous devrez créer manuellement une migration qui vérifie l'existence des tables")
        
    else:
        print("✅ Aucune table n'existe, migration normale possible")
        os.system("python manage.py migrate")

if __name__ == "__main__":
    main()
