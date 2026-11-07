#!/bin/bash
# Mise à jour sur le VPS : bash deploy/deploy.sh
set -e
cd /var/www/numerix/ediligencebackend
source venv/bin/activate
git pull origin master
pip install -r requirements.txt gunicorn
python manage.py migrate --noinput
python manage.py collectstatic --noinput
mkdir -p logs media scan_entrant
sudo chown -R www-data:www-data /var/www/numerix/ediligencebackend
sudo systemctl restart ediligence ediligence-celery ediligence-beat
sudo nginx -t && sudo systemctl reload nginx
sudo systemctl status ediligence ediligence-celery ediligence-beat --no-pager | grep -E "●|Active"
