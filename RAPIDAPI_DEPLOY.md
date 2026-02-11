# Deploying RXIQ API to RapidAPI Marketplace

Complete step-by-step guide to deploy your API and start earning revenue.

---

## Table of Contents

1. [Deploy Your API to a Hosting Provider](#step-1-deploy-your-api-to-a-hosting-provider)
2. [Create a RapidAPI Provider Account](#step-2-create-a-rapidapi-provider-account)
3. [Add Your API to RapidAPI](#step-3-add-your-api-to-rapidapi)
4. [Configure Endpoints](#step-4-configure-endpoints)
5. [Set Up Pricing Plans](#step-5-set-up-pricing-plans)
6. [Configure Security (Proxy Secret)](#step-6-configure-security-proxy-secret)
7. [Test Through RapidAPI](#step-7-test-through-rapidapi)
8. [Publish and Go Live](#step-8-publish-and-go-live)

---

## Step 1: Deploy Your API to a Hosting Provider

Your API needs a publicly accessible URL. Choose one:

### Option A: Railway (Recommended — Easiest)

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login & deploy
railway login
railway init
railway up

# Set environment variables
railway variables set OPENAI_API_KEY=sk-your-key-here
railway variables set RAPIDAPI_PROXY_SECRET=your-secret-here
railway variables set ENVIRONMENT=production
```

Railway gives you a URL like: `https://rxiq-api-production.up.railway.app`

### Option B: Render

1. Push your code to GitHub
2. Go to [render.com](https://render.com) → New Web Service
3. Connect your repo
4. Render auto-detects the `render.yaml` config
5. Add env vars: `OPENAI_API_KEY`, `RAPIDAPI_PROXY_SECRET`
6. Deploy

URL: `https://rxiq-api.onrender.com`

### Option C: Docker on Any VPS (DigitalOcean, AWS, etc.)

```bash
# Build and run
docker compose up -d

# Or without Redis:
docker build -t rxiq-rapidapi .
docker run -d -p 8080:8080 \
  -e OPENAI_API_KEY=sk-your-key \
  -e RAPIDAPI_PROXY_SECRET=your-secret \
  rxiq-rapidapi
```

### Verify Deployment

```bash
# Health check — should return {"status": "healthy"}
curl https://YOUR-DOMAIN/health

# Test extract — should return content
curl -X POST https://YOUR-DOMAIN/api/v1/extract \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

---

## Step 2: Create a RapidAPI Provider Account

1. Go to [rapidapi.com/provider](https://rapidapi.com/provider)
2. Click **"Sign Up"** (or log in if you already have an account)
3. Click your profile → **"My APIs"** → **"Add New API"**

---

## Step 3: Add Your API to RapidAPI

### 3.1 Basic Info

| Field | Value |
|---|---|
| **API Name** | `RXIQ API` |
| **Short Description** | `AI-Powered Content Intelligence — Extract, summarize, analyze, and compare web content. Readability scores, keyword extraction, content quality grading, and markdown output.` |
| **Category** | `Data` or `Text Analysis` |
| **Website** | Your GitHub repo or landing page URL |

### 3.2 Base URL

Set your **Base URL** to your deployed API:
```
https://YOUR-DOMAIN
```

### 3.3 API Logo

Upload a clean, square logo (at least 200x200 px). A simple icon with "IQ" text works well.

---

## Step 4: Configure Endpoints

In the RapidAPI dashboard, go to **"Endpoints"** and add each one:

### Endpoint 1: Extract Content

| Setting | Value |
|---|---|
| **Name** | Extract Content |
| **Method** | POST |
| **Path** | `/api/v1/extract` |
| **Description** | Extract clean text, metadata, readability scores, and reading time from any URL. Supports markdown output. |

**Request Body (JSON):**
```json
{
  "url": "https://example.com/article",
  "include_images": false,
  "include_links": false,
  "output_format": "text"
}
```

**Parameters:**
| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `url` | string | Yes | — | URL to extract content from |
| `include_images` | boolean | No | false | Include image URLs |
| `include_links` | boolean | No | false | Include outbound links |
| `output_format` | string | No | "text" | "text" or "markdown" |

### Endpoint 2: Summarize

| Setting | Value |
|---|---|
| **Name** | AI Summarize |
| **Method** | POST |
| **Path** | `/api/v1/summarize` |
| **Description** | Generate AI-powered summaries in 4 formats: TL;DR, bullet points, key takeaways, or paragraph. |

**Request Body:**
```json
{
  "url": "https://example.com/article",
  "format": "tldr",
  "max_length": 200,
  "language": "en"
}
```

### Endpoint 3: Sentiment Analysis

| Setting | Value |
|---|---|
| **Name** | Sentiment Analysis |
| **Method** | POST |
| **Path** | `/api/v1/sentiment` |
| **Description** | AI sentiment analysis with confidence scores and key influencing phrases. |

**Request Body:**
```json
{
  "url": "https://example.com/article"
}
```

### Endpoint 4: SEO Metadata

| Setting | Value |
|---|---|
| **Name** | SEO Metadata |
| **Method** | POST |
| **Path** | `/api/v1/seo` |
| **Description** | Extract complete SEO metadata: title, meta description, Open Graph, Twitter Card, Schema.org, heading structure, link analysis. |

**Request Body:**
```json
{
  "url": "https://example.com"
}
```

### Endpoint 5: Full Analysis

| Setting | Value |
|---|---|
| **Name** | Full Analysis |
| **Method** | POST |
| **Path** | `/api/v1/analyze` |
| **Description** | Complete content intelligence in one call: extraction, AI summary, sentiment, SEO, keyword/entity extraction, and content quality score (0-100 with letter grade). |

**Request Body:**
```json
{
  "url": "https://example.com/article",
  "summary_format": "tldr",
  "summary_max_length": 200
}
```

### Endpoint 6: Compare URLs

| Setting | Value |
|---|---|
| **Name** | Compare Content |
| **Method** | POST |
| **Path** | `/api/v1/compare` |
| **Description** | Compare two web pages: cosine similarity score, shared/unique keywords, word count difference, and readability comparison. |

**Request Body:**
```json
{
  "url1": "https://example.com/article-1",
  "url2": "https://example.com/article-2"
}
```

---

## Step 5: Set Up Pricing Plans

Go to **"Pricing"** in your API dashboard and create these plans:

### Free Tier
| Setting | Value |
|---|---|
| **Price** | $0/month |
| **Rate Limit** | 10 requests/minute |
| **Monthly Quota** | 100 requests |
| **Allowed Endpoints** | `/extract` only |

### Starter
| Setting | Value |
|---|---|
| **Price** | $9.99/month |
| **Rate Limit** | 30 requests/minute |
| **Monthly Quota** | 2,500 requests |
| **Allowed Endpoints** | All 6 endpoints |

### Pro
| Setting | Value |
|---|---|
| **Price** | $29.99/month |
| **Rate Limit** | 60 requests/minute |
| **Monthly Quota** | 15,000 requests |
| **Allowed Endpoints** | All 6 endpoints |

### Business
| Setting | Value |
|---|---|
| **Price** | $99.99/month |
| **Rate Limit** | 120 requests/minute |
| **Monthly Quota** | 75,000 requests |
| **Allowed Endpoints** | All 6 endpoints |

---

## Step 6: Configure Security (Proxy Secret)

RapidAPI acts as a proxy. You need to verify requests actually come from RapidAPI:

### 6.1 Get Your Proxy Secret

1. In the RapidAPI provider dashboard, go to **Security** settings
2. Find or generate **"X-RapidAPI-Proxy-Secret"**
3. Copy the secret value

### 6.2 Set It On Your Server

Add it as an environment variable on your hosting:

```bash
# Railway
railway variables set RAPIDAPI_PROXY_SECRET=your-proxy-secret-here

# Render
# Add in Environment tab in Render dashboard

# Docker
-e RAPIDAPI_PROXY_SECRET=your-proxy-secret-here
```

### 6.3 How It Works

RXIQ API automatically validates the `X-RapidAPI-Proxy-Secret` header on every request (see `app/main.py` middleware). Requests without a valid proxy secret get a `403 Forbidden` response.

**During development/testing:** Leave `RAPIDAPI_PROXY_SECRET` empty or unset to disable validation.

---

## Step 7: Test Through RapidAPI

### 7.1 Test in the RapidAPI Dashboard

1. Go to your API listing on RapidAPI
2. Subscribe to your own Free plan
3. Click on each endpoint in the **"Endpoints"** tab
4. Fill in the example request body
5. Click **"Test Endpoint"**
6. Verify you get a `200` response with the expected data

### 7.2 Test with Code

RapidAPI generates code snippets. Here's what they look like:

**Python:**
```python
import requests

url = "https://rxiq-api.p.rapidapi.com/api/v1/extract"

payload = {"url": "https://example.com"}
headers = {
    "Content-Type": "application/json",
    "X-RapidAPI-Key": "ef7129c761msh9476e78fc3f01ecp1b52dbjsn5620584fb605",
    "X-RapidAPI-Host": "rxiq-api.p.rapidapi.com"
}

response = requests.post(url, json=payload, headers=headers)
print(response.json())
```

**JavaScript:**
```javascript
const response = await fetch('https://rxiq-api.p.rapidapi.com/api/v1/analyze', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-RapidAPI-Key': 'ef7129c761msh9476e78fc3f01ecp1b52dbjsn5620584fb605',
    'X-RapidAPI-Host': 'rxiq-api.p.rapidapi.com'
  },
  body: JSON.stringify({ url: 'https://example.com/article' })
});

const data = await response.json();
console.log(data);
```

**cURL:**
```bash
curl -X POST "https://rxiq-api.p.rapidapi.com/api/v1/compare" \
  -H "Content-Type: application/json" \
  -H "X-RapidAPI-Key: ef7129c761msh9476e78fc3f01ecp1b52dbjsn5620584fb605" \
  -H "X-RapidAPI-Host: rxiq-api.p.rapidapi.com" \
  -d '{"url1": "https://example.com/page1", "url2": "https://example.com/page2"}'
```

### 7.3 Test Checklist

- [ ] `/extract` returns content with readability scores and reading time
- [ ] `/extract` with `"output_format": "markdown"` returns markdown field
- [ ] `/summarize` returns AI summary in each format (tldr, bullets, key_takeaways, paragraph)
- [ ] `/sentiment` returns sentiment label, confidence, and key phrases
- [ ] `/seo` returns complete SEO metadata
- [ ] `/analyze` returns all sections + keywords + quality score with grade
- [ ] `/compare` returns similarity score and keyword analysis
- [ ] Invalid URLs return `400` with error details
- [ ] Rate limiting works (headers show remaining quota)
- [ ] Caching works (second call to same URL returns `"cached": true`)

---

## Step 8: Publish and Go Live

### 8.1 Pre-Launch Checklist

- [ ] All 6 endpoints tested and returning correct responses
- [ ] Pricing plans configured
- [ ] Proxy secret configured and validated
- [ ] API description and documentation updated
- [ ] Logo uploaded
- [ ] Example request/response for each endpoint
- [ ] Error responses documented

### 8.2 API Description (Marketing Copy)

Use this in your RapidAPI listing description:

> **RXIQ API** — The most complete content intelligence API on RapidAPI.
>
> **6 powerful endpoints**, one API key:
> - **Extract** — Clean text, metadata, readability scores, reading time. Supports Markdown output.
> - **Summarize** — AI summaries in 4 formats (TL;DR, bullets, takeaways, paragraph) in any language.
> - **Sentiment** — Positive/negative/neutral/mixed with confidence scores and key phrases.
> - **SEO** — Full SEO audit: Open Graph, Twitter Card, Schema.org, heading structure, link analysis.
> - **Analyze** — ALL of the above in one call, PLUS keyword extraction, entity recognition, and a content quality score (0-100 with letter grade).
> - **Compare** — Side-by-side comparison of two URLs: similarity score, shared keywords, readability difference.
>
> **Why RXIQ?**
> - Readability metrics on every extract (Flesch, FK Grade, Coleman-Liau, ARI)
> - Markdown output for clean content reuse
> - Content quality grading with actionable recommendations
> - Keyword, topic, and named entity extraction
> - Zero-cost computed features (readability, quality, comparison) = better value
> - SSRF protection, caching, security headers — production-ready

### 8.3 Publish

1. Click **"Make API Public"** in the RapidAPI dashboard
2. Your API is now listed on the marketplace
3. Monitor usage in the **Analytics** tab

---

## Monitoring & Maintenance

### Check API Health

```bash
curl https://YOUR-DOMAIN/health
# {"status": "healthy", "cache": "memory", "version": "2.0.0"}
```

### View Metrics

```bash
curl https://YOUR-DOMAIN/metrics
# Prometheus-format metrics (if enabled)
```

### RapidAPI Analytics

- **Provider Dashboard** → **Analytics** shows:
  - Total API calls per day/week/month
  - Revenue per plan
  - Error rates
  - Latency percentiles
  - Subscriber count per tier

### Updating Your API

```bash
# Push code changes → CI runs tests → deploy
git push origin main

# Railway auto-deploys on push
# Render auto-deploys on push
# Docker: rebuild and restart
```

---

## Revenue Estimates

| Subscribers | Plan | Monthly Revenue |
|---|---|---|
| 50 free + 10 starter | Mixed | $99.90 |
| 50 free + 25 starter + 10 pro | Mixed | $549.65 |
| 50 free + 50 starter + 25 pro + 5 business | Mixed | $1,749.20 |

**Cost structure:**
- OpenAI API: ~$0.001-0.005 per AI-powered request (summarize, sentiment, keywords)
- Hosting: $5-20/month (Railway/Render)
- Readability, quality scoring, comparison: $0 (computed locally)
- **Net margin: 80-95%** on most requests
