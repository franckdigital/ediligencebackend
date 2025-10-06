#!/bin/bash
# Script pour démarrer Celery correctement

# Aller dans le bon répertoire
cd /var/www/numerix/ediligencebackend

# Activer l'environnement virtuel
source venv/bin/activate

# Exporter les variables d'environnement
export DJANGO_SETTINGS_MODULE=ediligencebackend.settings
export PYTHONPATH=/var/www/numerix/ediligencebackend:$PYTHONPATH

echo "🔄 Démarrage de Celery Beat..."
echo "Répertoire: $(pwd)"
echo "Python: $(which python)"
echo "DJANGO_SETTINGS_MODULE: $DJANGO_SETTINGS_MODULE"

# Démarrer Celery Beat
celery -A ediligencebackend beat --loglevel=info
