#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────
# RXIQ API — Vultr VPS Setup Script
# ──────────────────────────────────────────────────────────────
# Run this on a fresh Vultr Ubuntu 22.04/24.04 VPS:
#   curl -sSL https://raw.githubusercontent.com/reuxnergy-admin1/RXIQ/main/vultr-setup.sh | bash
#
# Or clone first and run:
#   chmod +x vultr-setup.sh && ./vultr-setup.sh
# ──────────────────────────────────────────────────────────────

set -euo pipefail

APP_NAME="rxiq-rapidapi"
APP_DIR="/opt/$APP_NAME"
DOMAIN=""  # Set your domain here if you have one, e.g. "api.rxiq.com"

echo "═══════════════════════════════════════════════════"
echo "  RXIQ API — Vultr VPS Setup"
echo "═══════════════════════════════════════════════════"

# ──────────────────────────────
# 1. System updates
# ──────────────────────────────
echo "[1/7] Updating system packages..."
apt-get update -y && apt-get upgrade -y
apt-get install -y curl git ufw fail2ban

# ──────────────────────────────
# 2. Install Docker
# ──────────────────────────────
echo "[2/7] Installing Docker..."
if ! command -v docker &>/dev/null; then
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
    echo "Docker installed: $(docker --version)"
else
    echo "Docker already installed: $(docker --version)"
fi

# Install Docker Compose plugin
if ! docker compose version &>/dev/null; then
    apt-get install -y docker-compose-plugin
    echo "Docker Compose installed: $(docker compose version)"
else
    echo "Docker Compose already installed: $(docker compose version)"
fi

# ──────────────────────────────
# 3. Firewall setup
# ──────────────────────────────
echo "[3/7] Configuring firewall..."
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
# Allow 8080 only if not using Nginx reverse proxy
# ufw allow 8080/tcp
echo "y" | ufw enable
ufw status

# ──────────────────────────────
# 4. Clone repo
# ──────────────────────────────
echo "[4/7] Cloning RXIQ API..."
if [ -d "$APP_DIR" ]; then
    echo "Directory exists, pulling latest..."
    cd "$APP_DIR" && git pull
else
    git clone https://github.com/reuxnergy-admin1/RXIQ.git "$APP_DIR"
    cd "$APP_DIR"
fi

# ──────────────────────────────
# 5. Create .env file
# ──────────────────────────────
echo "[5/7] Setting up environment..."
if [ ! -f "$APP_DIR/.env" ]; then
    cat > "$APP_DIR/.env" <<'ENVFILE'
# RXIQ API — Production Environment
OPENAI_API_KEY=sk-your-openai-api-key-here
RAPIDAPI_PROXY_SECRET=your-rapidapi-proxy-secret-here
REDIS_URL=redis://redis:6379/0
APP_ENV=production
APP_DEBUG=false
LOG_LEVEL=info
ENVFILE
    echo ""
    echo "╔══════════════════════════════════════════════════╗"
    echo "║  IMPORTANT: Edit .env with your real keys!      ║"
    echo "║  nano /opt/$APP_NAME/.env                       ║"
    echo "╚══════════════════════════════════════════════════╝"
    echo ""
else
    echo ".env already exists, skipping..."
fi

# ──────────────────────────────
# 6. Install Nginx reverse proxy
# ──────────────────────────────
echo "[6/7] Setting up Nginx reverse proxy..."
apt-get install -y nginx

cat > /etc/nginx/sites-available/$APP_NAME <<'NGINX'
server {
    listen 80;
    server_name _;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Max request body size (for content extraction)
    client_max_body_size 10M;

    # Proxy timeouts (AI endpoints can take a while)
    proxy_connect_timeout 60s;
    proxy_read_timeout 120s;
    proxy_send_timeout 60s;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Health check endpoint (no logging)
    location /health {
        proxy_pass http://127.0.0.1:8080/health;
        access_log off;
    }
}
NGINX

# Enable site
ln -sf /etc/nginx/sites-available/$APP_NAME /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx
systemctl enable nginx

# ──────────────────────────────
# 7. Start the app
# ──────────────────────────────
echo "[7/7] Starting RXIQ API..."
cd "$APP_DIR"
docker compose up -d --build

echo ""
echo "═══════════════════════════════════════════════════"
echo "  ✓ RXIQ API is running!"
echo "═══════════════════════════════════════════════════"
echo ""
echo "  App:       http://$(curl -s ifconfig.me)"
echo "  Health:    http://$(curl -s ifconfig.me)/health"
echo "  Docs:      http://$(curl -s ifconfig.me)/docs"
echo ""
echo "  ┌─────────────────────────────────────────────┐"
echo "  │ NEXT STEPS:                                 │"
echo "  │                                             │"
echo "  │ 1. Edit your API keys:                      │"
echo "  │    nano /opt/$APP_NAME/.env                  │"
echo "  │                                             │"
echo "  │ 2. Restart after editing .env:               │"
echo "  │    cd /opt/$APP_NAME                         │"
echo "  │    docker compose up -d                      │"
echo "  │                                             │"
echo "  │ 3. (Optional) Add SSL with Let's Encrypt:    │"
echo "  │    apt install certbot python3-certbot-nginx │"
echo "  │    certbot --nginx -d your-domain.com        │"
echo "  │                                             │"
echo "  │ 4. Set RapidAPI Base URL to:                 │"
echo "  │    http://YOUR-VULTR-IP                      │"
echo "  │    (or https://your-domain.com with SSL)     │"
echo "  └─────────────────────────────────────────────┘"
echo ""
