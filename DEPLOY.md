# ──────────────────────────────────────────────────────────────
# RXIQ API — Deployment Guide
# ──────────────────────────────────────────────────────────────
#
# OPTION 1: Vultr VPS (recommended — full control, $6/mo)
# ──────────────────────────────────────────────────────────────
#
#   See VULTR_DEPLOY.md for the complete guide.
#
#   Quick start:
#     ssh root@YOUR-VULTR-IP
#     curl -sSL https://raw.githubusercontent.com/reuxnergy-admin1/RXIQ/main/vultr-setup.sh | bash
#     nano /opt/rxiq-rapidapi/.env   # Set your API keys
#     cd /opt/rxiq-rapidapi && docker compose up -d
#
# ──────────────────────────────────────────────────────────────
# OPTION 2: Docker (any cloud provider)
# ──────────────────────────────────────────────────────────────
#
#   # Build and run locally:
#   docker compose up --build
#
#   # Or build image for cloud:
#   docker build -t rxiq-rapidapi .
#   docker push your-registry/rxiq-rapidapi
#
# ──────────────────────────────────────────────────────────────
# OPTION 3: Local Development
# ──────────────────────────────────────────────────────────────
#
#   pip install -r requirements.txt
#   cp .env.example .env
#   # Edit .env with your OpenAI key
#   uvicorn app.main:app --reload --port 8000
#
# ──────────────────────────────────────────────────────────────
# POST-DEPLOYMENT: Connect to RapidAPI
# ──────────────────────────────────────────────────────────────
#
#   1. Get your deployed URL (e.g., http://YOUR-VULTR-IP)
#   2. Go to RapidAPI Provider Dashboard
#   3. Set Base URL to your deployed URL
#   4. Copy your RapidAPI Proxy Secret
#   5. Set RAPIDAPI_PROXY_SECRET env var on your server
#   6. Test all endpoints via RapidAPI tester
#   7. Make API public
#
# See RAPIDAPI_DEPLOY.md for full marketplace setup instructions.
# See VULTR_DEPLOY.md for Vultr-specific deployment guide.
