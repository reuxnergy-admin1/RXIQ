# Deploying RXIQ API to Vultr

Complete guide to deploy RXIQ API on a Vultr VPS and connect it to RapidAPI.

---

## Table of Contents

1. [Create a Vultr VPS](#1-create-a-vultr-vps)
2. [One-Command Setup](#2-one-command-setup)
3. [Manual Setup (Alternative)](#3-manual-setup-alternative)
4. [Add SSL Certificate](#4-add-ssl-certificate)
5. [Connect to RapidAPI](#5-connect-to-rapidapi)
6. [Management Commands](#6-management-commands)
7. [Monitoring & Logs](#7-monitoring--logs)
8. [Auto-Restart & Updates](#8-auto-restart--updates)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. Create a Vultr VPS

1. Log in to [my.vultr.com](https://my.vultr.com)
2. Click **Deploy New Server**
3. Settings:

| Setting         | Value                          |
|-----------------|--------------------------------|
| Type            | Cloud Compute — Shared CPU     |
| Location        | Amsterdam (or closest to users)|
| Image           | Ubuntu 22.04 LTS              |
| Plan            | **$6/mo** (1 vCPU, 1 GB RAM) — enough for moderate traffic |
| Auto Backups    | Enable ($1.20/mo extra)        |
| SSH Keys        | Add your SSH key (recommended) |
| Hostname        | `rxiq-rapidapi`                |

> **Scaling guide:**
> - **$6/mo (1 GB)** — up to ~50 req/min, good for launch
> - **$12/mo (2 GB)** — up to ~150 req/min, good for growth
> - **$24/mo (4 GB)** — up to ~500 req/min, handles heavy traffic

4. Click **Deploy Now** and wait ~60 seconds
5. Copy your server's **IP address** from the dashboard

---

## 2. One-Command Setup

SSH into your server and run the automated setup script:

```bash
ssh root@YOUR-VULTR-IP
```

```bash
curl -sSL https://raw.githubusercontent.com/reuxnergy-admin1/RXIQ/main/vultr-setup.sh | bash
```

This script automatically:
- Updates the system & installs security tools
- Installs Docker & Docker Compose
- Configures UFW firewall (SSH, HTTP, HTTPS only)
- Clones the RXIQ repo to `/opt/rxiq-rapidapi`
- Creates a `.env` template
- Sets up Nginx as a reverse proxy (port 80 → 8080)
- Builds and starts the Docker containers

**After the script completes, edit your API keys:**

```bash
nano /opt/rxiq-rapidapi/.env
```

Set your real values:

```env
OPENAI_API_KEY=sk-your-real-key-here
RAPIDAPI_PROXY_SECRET=your-secret-from-rapidapi-dashboard
```

Then restart:

```bash
cd /opt/rxiq-rapidapi
docker compose up -d
```

**Verify it's running:**

```bash
curl http://localhost/health
# → {"status":"healthy","version":"2.0.0"}

curl http://YOUR-VULTR-IP/health
# → {"status":"healthy","version":"2.0.0"}
```

---

## 3. Manual Setup (Alternative)

If you prefer step-by-step control:

### 3.1 SSH & Update

```bash
ssh root@YOUR-VULTR-IP
apt update && apt upgrade -y
apt install -y curl git ufw fail2ban nginx
```

### 3.2 Install Docker

```bash
curl -fsSL https://get.docker.com | sh
systemctl enable docker && systemctl start docker
apt install -y docker-compose-plugin
```

### 3.3 Firewall

```bash
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
echo "y" | ufw enable
```

### 3.4 Clone & Configure

```bash
git clone https://github.com/reuxnergy-admin1/RXIQ.git /opt/rxiq-rapidapi
cd /opt/rxiq-rapidapi

cat > .env <<EOF
OPENAI_API_KEY=sk-your-real-key
RAPIDAPI_PROXY_SECRET=your-secret
REDIS_URL=redis://redis:6379/0
APP_ENV=production
APP_DEBUG=false
LOG_LEVEL=info
EOF
```

### 3.5 Nginx Reverse Proxy

```bash
cat > /etc/nginx/sites-available/rxiq-rapidapi <<'NGINX'
server {
    listen 80;
    server_name _;

    client_max_body_size 10M;
    proxy_connect_timeout 60s;
    proxy_read_timeout 120s;
    proxy_send_timeout 60s;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /health {
        proxy_pass http://127.0.0.1:8080/health;
        access_log off;
    }
}
NGINX

ln -sf /etc/nginx/sites-available/rxiq-rapidapi /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx
systemctl enable nginx
```

### 3.6 Build & Start

```bash
cd /opt/rxiq-rapidapi
docker compose up -d --build
```

---

## 4. Add SSL Certificate

Free SSL with Let's Encrypt (requires a domain pointing to your Vultr IP):

```bash
# Install certbot
apt install -y certbot python3-certbot-nginx

# Get certificate (replace with your domain)
certbot --nginx -d api.rxiq.com

# Auto-renewal is set up automatically, verify:
certbot renew --dry-run
```

**Without a domain** — use Vultr IP directly with `http://`. RapidAPI proxies all
requests, so end-users never see your raw URL. SSL between RapidAPI and your
server is optional but recommended.

**With Cloudflare (alternative):**
1. Add your domain to Cloudflare
2. Point DNS A record to Vultr IP (proxy enabled)
3. Cloudflare handles SSL automatically
4. Set RapidAPI Base URL to `https://api.rxiq.com`

---

## 5. Connect to RapidAPI

Once your server is live:

### 5.1 Get Your Proxy Secret

1. Go to [RapidAPI Provider Dashboard](https://provider.rapidapi.com)
2. Select **RXIQ** → **Configuration** → **Security**
3. Copy the **Proxy Secret** value

### 5.2 Set It on Your Server

```bash
cd /opt/rxiq-rapidapi
nano .env
# Set: RAPIDAPI_PROXY_SECRET=the-value-you-copied
docker compose up -d
```

### 5.3 Set Base URL

In RapidAPI Dashboard → **Configuration**:

| Field    | Value                                        |
|----------|----------------------------------------------|
| Base URL | `http://YOUR-VULTR-IP` (or `https://api.rxiq.com`) |

### 5.4 Add Endpoints

In RapidAPI Dashboard → **Endpoints**, add these 6 POST endpoints:

| Endpoint              | Description                              |
|-----------------------|------------------------------------------|
| `POST /api/v1/extract`   | Extract & clean content from any URL  |
| `POST /api/v1/summarize` | AI-powered content summarization      |
| `POST /api/v1/sentiment` | Sentiment analysis with emotion detection |
| `POST /api/v1/seo`       | SEO audit with actionable recommendations |
| `POST /api/v1/analyze`   | Full content analysis (readability, keywords, quality) |
| `POST /api/v1/compare`   | Compare two URLs side-by-side          |

See [RAPIDAPI_DEPLOY.md](RAPIDAPI_DEPLOY.md) for detailed endpoint configuration.

---

## 6. Management Commands

Run these from `/opt/rxiq-rapidapi`:

```bash
# Status
docker compose ps

# Restart
docker compose restart

# Stop
docker compose down

# Start
docker compose up -d

# Rebuild after code changes
git pull
docker compose up -d --build

# View resource usage
docker stats

# Enter the API container
docker compose exec api bash
```

---

## 7. Monitoring & Logs

### View Logs

```bash
# All logs (follow mode)
docker compose logs -f

# API logs only
docker compose logs -f api

# Last 100 lines
docker compose logs --tail 100 api

# Redis logs
docker compose logs -f redis
```

### Health Check

```bash
# Quick health check
curl -s http://localhost/health | python3 -m json.tool

# Full endpoint test
curl -s -X POST http://localhost/api/v1/extract \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}' | python3 -m json.tool
```

### Uptime Monitoring (Optional)

Set up free uptime monitoring:

1. **UptimeRobot** (free): [uptimerobot.com](https://uptimerobot.com)
   - Monitor type: HTTP(s)
   - URL: `http://YOUR-VULTR-IP/health`
   - Interval: 5 minutes

2. **Better Stack** (free tier): [betterstack.com](https://betterstack.com)

---

## 8. Auto-Restart & Updates

### Auto-Restart on Reboot

Docker containers are already configured with `restart: unless-stopped` in `docker-compose.yml`. They will auto-restart if the VPS reboots.

Verify:

```bash
docker compose ps
# STATUS should show "Up" with "(healthy)" for both containers
```

### Auto-Deploy on Git Push (Optional)

Create a simple webhook-based auto-deploy:

```bash
cat > /opt/rxiq-rapidapi/deploy.sh <<'EOF'
#!/bin/bash
cd /opt/rxiq-rapidapi
git pull origin main
docker compose up -d --build
echo "Deployed at $(date)" >> /var/log/rxiq-deploy.log
EOF

chmod +x /opt/rxiq-rapidapi/deploy.sh
```

Add a cron job to auto-pull every 5 minutes (simple approach):

```bash
crontab -e
# Add this line:
# */5 * * * * /opt/rxiq-rapidapi/deploy.sh >> /var/log/rxiq-deploy.log 2>&1
```

---

## 9. Troubleshooting

### Container won't start

```bash
# Check logs for errors
docker compose logs api

# Common fix: rebuild
docker compose down
docker compose up -d --build
```

### Port 8080 already in use

```bash
# Find what's using the port
lsof -i :8080

# Kill the process
kill -9 <PID>

# Restart
docker compose up -d
```

### OpenAI API errors

```bash
# Verify your key is set
docker compose exec api env | grep OPENAI

# Test the key directly
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer sk-your-key"
```

### Nginx 502 Bad Gateway

```bash
# Check if API container is running
docker compose ps

# Restart everything
docker compose restart
systemctl restart nginx
```

### Out of memory

```bash
# Check memory
free -h

# If low, reduce workers in Dockerfile (change --workers 4 to --workers 2)
# Or upgrade your Vultr plan
```

### Redis connection issues

```bash
# Check Redis is healthy
docker compose exec redis redis-cli ping
# Should return: PONG

# Restart Redis
docker compose restart redis
```

---

## Architecture Diagram

```
                    ┌─────────────┐
    Users ──────►   │  RapidAPI   │
                    │  (Proxy)    │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   Nginx     │  :80 / :443
                    │  (Reverse   │
                    │   Proxy)    │
                    └──────┬──────┘
                           │
                           ▼
              ┌────────────────────────┐
              │  Docker Compose        │
              │                        │
              │  ┌──────────────────┐  │
              │  │  RXIQ API        │  │  :8080
              │  │  (Gunicorn +     │  │
              │  │   Uvicorn)       │  │
              │  └────────┬─────────┘  │
              │           │            │
              │  ┌────────▼─────────┐  │
              │  │  Redis 7         │  │  :6379
              │  │  (Cache)         │  │
              │  └──────────────────┘  │
              └────────────────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  OpenAI API │
                    │  (GPT-4o    │
                    │   mini)     │
                    └─────────────┘
```

---

## Cost Summary

| Component          | Cost/Month |
|--------------------|-----------|
| Vultr VPS (1 GB)   | $6.00     |
| Auto Backups       | $1.20     |
| Domain (optional)  | ~$1.00    |
| OpenAI API         | Usage-based (~$0.15/1K req) |
| SSL (Let's Encrypt)| Free      |
| **Total (fixed)**  | **~$7.20/mo** |

Your RapidAPI revenue from subscriptions covers this cost quickly — even 1 Starter
plan subscriber ($9.99/mo) makes the infrastructure profitable.
