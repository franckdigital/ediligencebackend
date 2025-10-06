#!/bin/bash
# Script pour démarrer Celery Worker correctement

# Aller dans le bon répertoire
cd /var/www/numerix/ediligencebackend

# Activer l'environnement virtuel
source venv/bin/activate

# Exporter les variables d'environnement
export DJANGO_SETTINGS_MODULE=ediligencebackend.settings
export PYTHONPATH=/var/www/numerix/ediligencebackend:$PYTHONPATH

echo "🔄 Démarrage de Celery Worker..."
echo "Répertoire: $(pwd)"
echo "Python: $(which python)"
echo "DJANGO_SETTINGS_MODULE: $DJANGO_SETTINGS_MODULE"

# Démarrer Celery Worker
celery -A ediligencebackend worker --loglevel=info
