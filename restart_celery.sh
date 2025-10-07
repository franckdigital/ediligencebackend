#!/bin/bash
"""
Script pour redémarrer Celery avec la configuration corrigée
Usage: bash restart_celery.sh
"""

echo "🔄 REDÉMARRAGE DE CELERY"
echo "========================"

# Arrêter tous les processus Celery existants
echo "🛑 Arrêt des processus Celery existants..."
pkill -f "celery.*beat" 2>/dev/null || echo "Aucun processus beat à arrêter"
pkill -f "celery.*worker" 2>/dev/null || echo "Aucun processus worker à arrêter"

# Attendre un peu pour s'assurer que les processus sont arrêtés
sleep 2

# Vérifier que nous sommes dans le bon répertoire
if [ ! -f "manage.py" ]; then
    echo "❌ Erreur: manage.py non trouvé. Assurez-vous d'être dans le répertoire ediligencebackend"
    exit 1
fi

# Vérifier que l'environnement virtuel est activé
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Avertissement: Aucun environnement virtuel détecté"
    echo "   Activez votre venv avec: source venv/bin/activate"
fi

echo "🚀 Démarrage de Celery Worker..."
celery -A ediligence worker --loglevel=info --detach --pidfile=/tmp/celery_worker.pid --logfile=/tmp/celery_worker.log

echo "🚀 Démarrage de Celery Beat..."
celery -A ediligence beat --loglevel=info --detach --pidfile=/tmp/celery_beat.pid --logfile=/tmp/celery_beat.log

# Attendre un peu pour que les processus démarrent
sleep 3

# Vérifier que les processus sont démarrés
echo "📋 Vérification des processus..."
if pgrep -f "celery.*worker" > /dev/null; then
    echo "✅ Celery Worker démarré"
else
    echo "❌ Erreur: Celery Worker n'a pas démarré"
fi

if pgrep -f "celery.*beat" > /dev/null; then
    echo "✅ Celery Beat démarré"
else
    echo "❌ Erreur: Celery Beat n'a pas démarré"
fi

echo ""
echo "📝 Commandes utiles:"
echo "   Voir les logs Worker: tail -f /tmp/celery_worker.log"
echo "   Voir les logs Beat: tail -f /tmp/celery_beat.log"
echo "   Arrêter Worker: kill \$(cat /tmp/celery_worker.pid)"
echo "   Arrêter Beat: kill \$(cat /tmp/celery_beat.pid)"
echo ""
echo "🧪 Test manuel:"
echo "   python setup_geofencing_config.py"
echo "   python test_geofencing_manual.py"
echo ""
echo "✅ Redémarrage terminé!"
