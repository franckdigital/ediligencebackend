#!/bin/bash
# Script de déploiement de la hiérarchie Direction → Sous-direction → Service
# À exécuter sur le serveur de production

set -e  # Arrêter en cas d'erreur

echo "=========================================="
echo "Déploiement de la structure hiérarchique"
echo "=========================================="

# Couleurs pour les messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Répertoire du projet
PROJECT_DIR="/var/www/numerix/ediligencebackend"
cd $PROJECT_DIR

echo -e "${YELLOW}Étape 1: Activation de l'environnement virtuel${NC}"
source venv/bin/activate

echo -e "${YELLOW}Étape 2: Vérification de l'état des migrations${NC}"
python manage.py showmigrations core | tail -10

echo -e "${YELLOW}Étape 3: Application de la migration 0033 (SousDirection)${NC}"
python manage.py migrate core 0033
echo -e "${GREEN}✓ Migration 0033 appliquée${NC}"

echo -e "${YELLOW}Étape 4: Application de la migration 0034 (Nouveaux rôles)${NC}"
python manage.py migrate core 0034
echo -e "${GREEN}✓ Migration 0034 appliquée${NC}"

echo -e "${YELLOW}Étape 5: Migration des données existantes${NC}"
python migrate_services_to_sous_directions.py
echo -e "${GREEN}✓ Données migrées${NC}"

echo -e "${YELLOW}Étape 6: Sauvegarde de la base de données (optionnel)${NC}"
python manage.py dumpdata core.Service > backup_services_$(date +%Y%m%d_%H%M%S).json
python manage.py dumpdata core.Direction > backup_directions_$(date +%Y%m%d_%H%M%S).json
python manage.py dumpdata core.SousDirection > backup_sousdirections_$(date +%Y%m%d_%H%M%S).json
echo -e "${GREEN}✓ Sauvegarde terminée${NC}"

echo -e "${YELLOW}Étape 7: Vérification de la structure${NC}"
python manage.py shell << EOF
from core.models import Direction, SousDirection, Service
print(f"\nDirections: {Direction.objects.count()}")
print(f"Sous-directions: {SousDirection.objects.count()}")
print(f"Services: {Service.objects.count()}")
print(f"Services sans sous-direction: {Service.objects.filter(sous_direction__isnull=True).count()}")
EOF

echo -e "${YELLOW}Étape 8: Redémarrage des services${NC}"
sudo systemctl restart gunicorn
echo -e "${GREEN}✓ Gunicorn redémarré${NC}"

# Optionnel : redémarrer Celery si utilisé
if systemctl is-active --quiet celery; then
    sudo systemctl restart celery
    echo -e "${GREEN}✓ Celery redémarré${NC}"
fi

echo ""
echo -e "${GREEN}=========================================="
echo -e "✓ Déploiement terminé avec succès!"
echo -e "==========================================${NC}"
echo ""
echo "Vérifications à effectuer :"
echo "1. Accéder à l'interface web"
echo "2. Aller dans 'Gestion de la Structure Organisationnelle'"
echo "3. Vérifier l'onglet 'Sous-directions'"
echo "4. Créer un nouveau service et vérifier la sélection en cascade"
echo ""
