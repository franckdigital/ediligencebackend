#!/bin/bash
# Script de résolution finale pour les migrations géofencing

echo "🔧 Résolution finale des migrations géofencing..."

# 1. Marquer toutes les migrations géofencing comme appliquées
echo "📋 Étape 1: Marquage des migrations comme appliquées..."
python manage.py migrate core 0029_geofencesettings_pushnotificationtoken_geofencealert_and_more --fake
python manage.py migrate core 0030_merge_20251001_1244 --fake
python manage.py migrate core 0030_alter_pushnotificationtoken_token --fake
python manage.py migrate core 0031_merge_20251001_1251 --fake

# 2. Vérifier l'état des migrations
echo "📊 Étape 2: Vérification de l'état des migrations..."
python manage.py showmigrations core | tail -10

# 3. Corriger le champ token s'il est trop long
echo "🔧 Étape 3: Correction du champ token..."
mysql -u root -p ediligence -e "
ALTER TABLE core_pushnotificationtoken 
MODIFY COLUMN token VARCHAR(255) NOT NULL;
"

# 4. Initialiser les paramètres de géofencing
echo "⚙️ Étape 4: Initialisation des paramètres..."
python manage.py setup_geofencing

# 5. Redémarrer le service
echo "🔄 Étape 5: Redémarrage du service..."
sudo systemctl restart ediligencebackend

echo "✅ Résolution terminée!"
echo "🧪 Vérifiez avec: python manage.py showmigrations core"
