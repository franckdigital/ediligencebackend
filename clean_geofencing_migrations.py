#!/usr/bin/env python
"""
Script de nettoyage complet des migrations géofencing
"""
import os
import sys
import glob
import django
from django.conf import settings

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ediligencebackend.settings')
django.setup()

from django.db import connection

def clean_migration_files():
    """Supprimer tous les fichiers de migration géofencing"""
    print("🗑️  Suppression des fichiers de migration géofencing...")
    
    migration_patterns = [
        'core/migrations/*geofence*',
        'core/migrations/*pushnotification*', 
        'core/migrations/*agentlocation*',
        'core/migrations/0029_*',
        'core/migrations/0030_*',
        'core/migrations/0031_*'
    ]
    
    deleted_files = []
    for pattern in migration_patterns:
        files = glob.glob(pattern)
        for file in files:
            if os.path.exists(file):
                print(f"🗑️  Suppression: {file}")
                os.remove(file)
                deleted_files.append(file)
    
    return deleted_files

def clean_migration_records():
    """Nettoyer les enregistrements de migration dans la base"""
    print("🧹 Nettoyage des enregistrements de migration...")
    
    with connection.cursor() as cursor:
        # Supprimer les enregistrements de migration géofencing
        cursor.execute("""
            DELETE FROM django_migrations 
            WHERE app = 'core' 
            AND (
                name LIKE '%geofence%' 
                OR name LIKE '%pushnotification%'
                OR name LIKE '%agentlocation%'
                OR name LIKE '0029_%'
                OR name LIKE '0030_%'
                OR name LIKE '0031_%'
            )
        """)
        deleted_count = cursor.rowcount
        print(f"🗑️  {deleted_count} enregistrements de migration supprimés")

def check_tables():
    """Vérifier quelles tables géofencing existent"""
    print("📊 Vérification des tables existantes...")
    
    tables_to_check = [
        'core_geofencesettings',
        'core_geofencealert',
        'core_agentlocation', 
        'core_pushnotificationtoken'
    ]
    
    existing_tables = []
    with connection.cursor() as cursor:
        for table in tables_to_check:
            cursor.execute("""
                SELECT COUNT(*)
                FROM information_schema.tables 
                WHERE table_schema = %s 
                AND table_name = %s
            """, [connection.settings_dict['NAME'], table])
            
            if cursor.fetchone()[0] > 0:
                existing_tables.append(table)
                print(f"✅ Table {table} existe")
            else:
                print(f"❌ Table {table} n'existe pas")
    
    return existing_tables

def drop_tables(tables):
    """Supprimer les tables géofencing"""
    print("🗑️  Suppression des tables géofencing...")
    
    with connection.cursor() as cursor:
        # Désactiver les contraintes de clés étrangères temporairement
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        
        for table in tables:
            try:
                cursor.execute(f"DROP TABLE IF EXISTS {table}")
                print(f"🗑️  Table {table} supprimée")
            except Exception as e:
                print(f"❌ Erreur lors de la suppression de {table}: {e}")
        
        # Réactiver les contraintes
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

def main():
    print("🚨 NETTOYAGE COMPLET DES MIGRATIONS GÉOFENCING")
    print("=" * 50)
    
    # 1. Vérifier les tables existantes
    existing_tables = check_tables()
    
    # 2. Demander confirmation
    if existing_tables:
        print(f"\n⚠️  {len(existing_tables)} tables géofencing trouvées")
        print("Cette opération va:")
        print("- Supprimer tous les fichiers de migration géofencing")
        print("- Nettoyer les enregistrements de migration dans la base")
        print("- Supprimer toutes les tables géofencing existantes")
        
        confirm = input("\n🔴 Êtes-vous sûr de vouloir continuer? (tapez 'CONFIRMER'): ")
        if confirm != 'CONFIRMER':
            print("❌ Opération annulée")
            return
    
    # 3. Nettoyer les fichiers de migration
    deleted_files = clean_migration_files()
    
    # 4. Nettoyer les enregistrements de migration
    clean_migration_records()
    
    # 5. Supprimer les tables si elles existent
    if existing_tables:
        drop_tables(existing_tables)
    
    print("\n✅ NETTOYAGE TERMINÉ!")
    print("\n📋 Prochaines étapes:")
    print("1. python manage.py makemigrations")
    print("2. python manage.py migrate")
    print("3. python manage.py setup_geofencing")
    print("4. sudo systemctl restart ediligencebackend")

if __name__ == "__main__":
    main()
