#!/bin/bash
"""
Script pour démarrer Celery correctement avec logs
Usage: bash start_celery_proper.sh
"""

echo "🚀 DÉMARRAGE DE CELERY"
echo "====================="

# Vérifier que nous sommes dans le bon répertoire
if [ ! -f "manage.py" ]; then
    echo "❌ Erreur: manage.py non trouvé. Assurez-vous d'être dans le répertoire ediligencebackend"
    exit 1
fi

# Créer le répertoire de logs s'il n'existe pas
mkdir -p logs

# Arrêter tous les processus Celery existants
echo "🛑 Arrêt des processus Celery existants..."
pkill -f "celery.*beat" 2>/dev/null || echo "Aucun processus beat à arrêter"
pkill -f "celery.*worker" 2>/dev/null || echo "Aucun processus worker à arrêter"

# Attendre un peu
sleep 2

echo "🚀 Démarrage de Celery Worker..."
nohup celery -A ediligence worker --loglevel=info > logs/celery_worker.log 2>&1 &
WORKER_PID=$!
echo "Worker PID: $WORKER_PID"

echo "🚀 Démarrage de Celery Beat..."
nohup celery -A ediligence beat --loglevel=info > logs/celery_beat.log 2>&1 &
BEAT_PID=$!
echo "Beat PID: $BEAT_PID"

# Attendre un peu pour que les processus démarrent
sleep 3

# Vérifier que les processus sont démarrés
echo "📋 Vérification des processus..."
if ps -p $WORKER_PID > /dev/null; then
    echo "✅ Celery Worker démarré (PID: $WORKER_PID)"
else
    echo "❌ Erreur: Celery Worker n'a pas démarré"
fi

if ps -p $BEAT_PID > /dev/null; then
    echo "✅ Celery Beat démarré (PID: $BEAT_PID)"
else
    echo "❌ Erreur: Celery Beat n'a pas démarré"
fi

echo ""
echo "📝 Commandes utiles:"
echo "   Voir les logs Worker: tail -f logs/celery_worker.log"
echo "   Voir les logs Beat: tail -f logs/celery_beat.log"
echo "   Arrêter Worker: kill $WORKER_PID"
echo "   Arrêter Beat: kill $BEAT_PID"
echo "   Arrêter tous: pkill -f celery"
echo ""
echo "🧪 Tests disponibles:"
echo "   Debug logique: python debug_geofencing_logic.py"
echo "   Test forcé: python test_geofencing_now.py"
echo ""
echo "✅ Celery démarré avec succès!"

# Afficher les premières lignes des logs
echo ""
echo "📋 Premières lignes des logs:"
echo "--- Worker ---"
head -n 5 logs/celery_worker.log 2>/dev/null || echo "Pas encore de logs worker"
echo "--- Beat ---"
head -n 5 logs/celery_beat.log 2>/dev/null || echo "Pas encore de logs beat"
