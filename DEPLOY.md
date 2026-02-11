# ──────────────────────────────────────────────────────────────
# RXIQ API — Deployment Guide
# ──────────────────────────────────────────────────────────────
#
# OPTION 1: Railway (fastest — recommended for MVP)
# ──────────────────────────────────────────────────────────────
#
#   1. Install Railway CLI:
#        npm install -g @railway/cli
#
#   2. Login and init:
#        railway login
#        railway init
#
#   3. Add Redis:
#        railway add --plugin redis
#
#   4. Set environment variables:
#        railway variables set OPENAI_API_KEY=sk-your-key
#
#   5. Deploy:
#        railway up
#
#   6. Get your public URL:
#        railway domain
#
# ──────────────────────────────────────────────────────────────
# OPTION 2: Render (one-click with render.yaml)
# ──────────────────────────────────────────────────────────────
#
#   1. Push to GitHub
#   2. Go to https://render.com/deploy
#   3. Connect your repo (render.yaml auto-detected)
#   4. Set OPENAI_API_KEY in environment
#   5. Click "Apply"
#
# ──────────────────────────────────────────────────────────────
# OPTION 3: Docker (any cloud provider)
# ──────────────────────────────────────────────────────────────
#
#   # Build and run locally:
#   docker-compose up --build
#
#   # Or build image for cloud:
#   docker build -t rxiq-api .
#   docker push your-registry/rxiq-api
#
# ──────────────────────────────────────────────────────────────
# OPTION 4: Local Development
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
#   1. Get your deployed URL (e.g., https://your-app.up.railway.app)
#   2. Go to RapidAPI Provider Dashboard
#   3. Set Base URL to your deployed URL
#   4. Copy your RapidAPI Proxy Secret
#   5. Set RAPIDAPI_PROXY_SECRET env var on your server
#   6. Uncomment proxy validation middleware in app/main.py
#   7. Test all endpoints via RapidAPI tester
#   8. Make API public
#
# See rapidapi/LISTING_GUIDE.md for full marketplace setup instructions.
