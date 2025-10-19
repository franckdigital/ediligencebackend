#!/bin/bash

# Script pour corriger la configuration Nginx et servir les fichiers media

echo "🔧 Correction de la configuration Nginx pour servir les fichiers media..."

# Backup de la configuration actuelle
sudo cp /etc/nginx/sites-available/default /etc/nginx/sites-available/default.backup.$(date +%Y%m%d_%H%M%S)

# Créer le fichier de configuration corrigé
sudo tee /etc/nginx/sites-available/default > /dev/null << 'EOF'
# ========================
# REDIRECTION HTTP -> HTTPS
# ========================
server {
    listen 80;
    server_name xamila.finance www.xamila.finance api.xamila.finance;
    return 301 https://$host$request_uri;
}

server {
    listen 80;
    server_name numerix.digital www.numerix.digital e-diligence.numerix.digital api-diligence.numerix.digital;
    return 301 https://$host$request_uri;
}

# ===================================
# FRONTEND React + phpMyAdmin (xamila)
# ===================================
server {
    listen 443 ssl http2;
    server_name xamila.finance www.xamila.finance;

    ssl_certificate /etc/letsencrypt/live/xamila.finance/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/xamila.finance/privkey.pem;

    root /var/www/xamila/front;
    index index.html;

    location ^~ /.well-known/acme-challenge/ {
        allow all;
        root /var/www/html;
    }

    location / {
        try_files $uri /index.html;
    }

    location ~* \.(?:ico|css|js|gif|jpe?g|png|woff2?|eot|ttf|svg|mp4|webm)$ {
        expires 6M;
        access_log off;
        add_header Cache-Control "public";
        try_files $uri /index.html;
    }

    location /phpmyadmin {
        alias /usr/share/phpmyadmin/;
        index index.php index.html index.htm;

        location ~ ^/phpmyadmin/(.+\.php)$ {
            alias /usr/share/phpmyadmin/$1;
            fastcgi_pass unix:/var/run/php/php-fpm.sock;
            fastcgi_index index.php;
            fastcgi_param SCRIPT_FILENAME $request_filename;
            include fastcgi_params;
        }

        location ~* ^/phpmyadmin/(.+\.(jpg|jpeg|gif|css|png|js|ico|html|xml|txt))$ {
            alias /usr/share/phpmyadmin/$1;
        }
    }
}

# API Django sur api.xamila.finance (HTTPS)
server {
    listen 443 ssl http2;
    server_name api.xamila.finance;

    ssl_certificate /etc/letsencrypt/live/xamila.finance/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/xamila.finance/privkey.pem;

    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';" always;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# ==========================
# API Django (ediligence) - AVEC MEDIA FILES
# ==========================
server {
    listen 443 ssl http2;
    server_name api-diligence.numerix.digital;

    ssl_certificate /etc/letsencrypt/live/numerix.digital/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/numerix.digital/privkey.pem;
    
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';" always;

    # Servir les fichiers media (uploads)
    location /media/ {
        alias /var/www/numerix/ediligencebackend/media/;
        expires 30d;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # Servir les fichiers static (CSS, JS, images du Django admin)
    location /static/ {
        alias /var/www/numerix/ediligencebackend/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # Proxy vers Django pour toutes les autres requêtes
    location / {
        proxy_pass http://127.0.0.1:9000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;
    }
}

# ======================
# FRONTEND (numerix.digital)
# ======================
server {
    listen 443 ssl http2;
    server_name numerix.digital www.numerix.digital;

    ssl_certificate /etc/letsencrypt/live/numerix.digital/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/numerix.digital/privkey.pem;

    root /var/www/numerix/front;
    index index.html;

    location ^~ /.well-known/acme-challenge/ {
        allow all;
        root /var/www/html;
    }

    location / {
        try_files $uri /index.html;
    }

    location ~* \.(?:ico|css|js|gif|jpe?g|png|woff2?|eot|ttf|svg|mp4|webm)$ {
        expires 6M;
        access_log off;
        add_header Cache-Control "public";
        try_files $uri /index.html;
    }
}

# =======================
# FRONTEND React (e-diligence.numerix.digital)
# =======================
server {
    listen 443 ssl http2;
    server_name e-diligence.numerix.digital;

    ssl_certificate /etc/letsencrypt/live/numerix.digital/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/numerix.digital/privkey.pem;

    root /var/www/numerix/frontend;
    index index.html;

    location ^~ /.well-known/acme-challenge/ {
        allow all;
        root /var/www/html;
    }

    location / {
        try_files $uri /index.html;
    }

    location ~* \.(?:ico|css|js|gif|jpe?g|png|woff2?|eot|ttf|svg|mp4|webm)$ {
        expires 6M;
        access_log off;
        add_header Cache-Control "public";
        try_files $uri /index.html;
    }
}
EOF

echo "✅ Configuration Nginx mise à jour"

# Vérifier la syntaxe Nginx
echo "🔍 Vérification de la syntaxe Nginx..."
sudo nginx -t

if [ $? -eq 0 ]; then
    echo "✅ Syntaxe Nginx valide"
    
    # Recharger Nginx
    echo "🔄 Rechargement de Nginx..."
    sudo systemctl reload nginx
    
    if [ $? -eq 0 ]; then
        echo "✅ Nginx rechargé avec succès"
        echo ""
        echo "🎉 Configuration terminée !"
        echo ""
        echo "📁 Les fichiers media sont maintenant accessibles via:"
        echo "   https://api-diligence.numerix.digital/media/courriers/..."
        echo "   https://api-diligence.numerix.digital/media/diligences/..."
        echo ""
        echo "🧪 Testez avec:"
        echo "   curl -I https://api-diligence.numerix.digital/media/courriers/SEMINAIRE_GIZ_.pdf"
    else
        echo "❌ Erreur lors du rechargement de Nginx"
        exit 1
    fi
else
    echo "❌ Erreur de syntaxe Nginx"
    echo "🔙 Restauration de la configuration précédente..."
    sudo cp /etc/nginx/sites-available/default.backup.* /etc/nginx/sites-available/default
    exit 1
fi
