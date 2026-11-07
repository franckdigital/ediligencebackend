#!/bin/bash
# Installation initiale sur le VPS (après git clone dans /var/www/ediligence/backend)
set -e
APP=/var/www/ediligence/backend
sudo apt update && sudo apt install -y nginx certbot python3-certbot-nginx python3-venv python3-pip redis-server
sudo mkdir -p /var/www/ediligence/frontend
cd $APP
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt gunicorn
[ -f .env ] || { cp deploy/env.example .env; echo ">>> EDITE .env (SECRET_KEY, DB_PASSWORD) puis relance setup.sh"; exit 1; }
python manage.py migrate --noinput
python manage.py collectstatic --noinput
mkdir -p logs media scan_entrant
sudo chown -R www-data:www-data $APP /var/www/ediligence/frontend
sudo cp deploy/systemd/ediligence*.service /etc/systemd/system/
sudo cp deploy/nginx/ediligence /etc/nginx/sites-available/ediligence
sudo ln -sf /etc/nginx/sites-available/ediligence /etc/nginx/sites-enabled/ediligence
sudo systemctl daemon-reload
sudo systemctl enable --now redis-server ediligence ediligence-celery ediligence-beat
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d api-diligence.numerix.digital -d e-diligence.numerix.digital \
  --agree-tos -m franckalain.ai@gmail.com --redirect --non-interactive
sudo certbot renew --dry-run
