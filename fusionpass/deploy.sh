#!/usr/bin/env bash
# Build the Fusion Pass web app and publish it to https://watch.fusionpass.shop on the bridge.
# First run also creates the nginx vhost and the Let's Encrypt cert (DNS record already exists,
# orange-cloud). Later runs just rebuild and re-upload.   Usage: fusionpass/deploy.sh
set -euo pipefail
echo "Retired 2026-09-27: watch.fusionpass.shop now serves the Nuvio-based app (oiefjqhio/fusionpass-webapp). Refusing to overwrite it." >&2
exit 1
cd "$(dirname "$0")/.."
KEY=/root/.ssh/srvl_fleet
HOST=root@149.56.140.29
B=(ssh -o BatchMode=yes -i "$KEY" "$HOST")

python3 fusionpass/rebrand.py
COREPACK_ENABLE_DOWNLOAD_PROMPT=0 pnpm install --frozen-lockfile --silent
COREPACK_ENABLE_DOWNLOAD_PROMPT=0 pnpm run build 2>&1 | grep -E "compiled|ERROR"

"${B[@]}" 'mkdir -p /var/www/fusionpass-web'
rsync -a --delete --exclude /app/ -e "ssh -i $KEY" build/ "$HOST:/var/www/fusionpass-web/"

"${B[@]}" bash -s <<'REMOTE'
set -euo pipefail
chown -R www-data:www-data /var/www/fusionpass-web
V=/etc/nginx/sites-available/watch.fusionpass.shop
if [ ! -e /etc/letsencrypt/live/watch.fusionpass.shop/fullchain.pem ]; then
  cat > "$V" <<'EOF'
server {
    listen 80;
    server_name watch.fusionpass.shop;
    location ^~ /.well-known/acme-challenge/ { root /var/www/letsencrypt; }
    location / { return 301 https://watch.fusionpass.shop$request_uri; }
}
EOF
  ln -sf "$V" /etc/nginx/sites-enabled/
  nginx -t && systemctl reload nginx
  certbot certonly --webroot -w /var/www/letsencrypt -d watch.fusionpass.shop --non-interactive --agree-tos --keep-until-expiring
fi
cat > "$V" <<'EOF'
# Fusion Pass web app: branded stremio-web fork (github.com/oiefjqhio/fusionpass-web), static
# build in /var/www/fusionpass-web (fusionpass/deploy.sh). Orange-cloud, Cloudflare-only via ufw.
server {
    listen 80;
    server_name watch.fusionpass.shop;
    location ^~ /.well-known/acme-challenge/ { root /var/www/letsencrypt; }
    location / { return 301 https://watch.fusionpass.shop$request_uri; }
}

server {
    listen 443 ssl http2;
    server_name watch.fusionpass.shop;

    ssl_certificate     /etc/letsencrypt/live/watch.fusionpass.shop/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/watch.fusionpass.shop/privkey.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;

    root /var/www/fusionpass-web;
    index index.html;
    gzip on;
    gzip_types text/css application/javascript application/json image/svg+xml application/manifest+json;

    # Content-hashed build output: cache for a year. The shell and service worker: never.
    location ~ "^/[0-9a-f]{40}/" { expires 1y; add_header Cache-Control "public, immutable"; try_files $uri =404; }
    location = /index.html { add_header Cache-Control "no-cache"; }
    location = /service-worker.js { add_header Cache-Control "no-cache"; }
    location = /manifest.json { add_header Cache-Control "no-cache"; }
    location / { try_files $uri $uri/ /index.html; }
}
EOF
ln -sf "$V" /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
REMOTE

code=$(curl -s -o /dev/null -w '%{http_code}' https://watch.fusionpass.shop/)
echo "https://watch.fusionpass.shop -> $code"
