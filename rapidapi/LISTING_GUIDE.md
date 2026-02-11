# RXIQ API — RapidAPI Listing Guide

## Step-by-Step: Listing on RapidAPI Marketplace

### 1. Create Provider Account

1. Go to [RapidAPI Provider Dashboard](https://rapidapi.com/provider)
2. Sign up / log in
3. Click **"Add New API"**
4. Choose **"Add Existing API"** → **"REST"**

### 2. Configure Base URL

Set your base URL to your deployed API:

- **Railway**: `https://your-app.up.railway.app`
- **Render**: `https://your-app.onrender.com`
- **Custom Domain**: `https://api.rxiq.dev`

### 3. API Name & Description

**Name**: RXIQ API

**Short Description** (for search results — max 120 chars):
> AI-powered content intelligence: extract, summarize, analyze sentiment & SEO metadata from any URL in one API call.

**Long Description** (for the listing page):

```
🚀 RXIQ API — Your All-in-One Content Intelligence Toolkit

Stop building web scrapers and AI integrations from scratch. RXIQ gives you 6 powerful endpoints in one subscription:

✅ EXTRACT — Get clean, structured text from any webpage (articles, blogs, product pages)
✅ SUMMARIZE — AI-powered summaries in 4 formats: TL;DR, bullet points, key takeaways, or paragraphs
✅ SENTIMENT — Analyze sentiment with confidence scores and key phrase detection
✅ SEO — Extract complete SEO metadata: Open Graph, Twitter Cards, Schema.org, heading structure
✅ ANALYZE — All of the above in a single API call

WHY DEVELOPERS CHOOSE RXIQ:

📌 One subscription, 5 tools — Save money vs. subscribing to 5 separate APIs
📌 AI + Web Scraping combined — The two hottest categories in one API
📌 Lightning fast — Sub-2 second responses with intelligent caching
📌 Clean data — No HTML parsing needed; get structured JSON every time
📌 100% uptime focus — Built for production workloads

PERFECT FOR:

• Content aggregation apps
• SEO monitoring tools
• Market research platforms
• Social media dashboards
• News readers & summarizers
• Competitive analysis tools
• No-code/low-code integrations

RESPONSE FORMAT:
Every endpoint returns clean, consistent JSON:
{
  "success": true,
  "data": { ... },
  "cached": false,
  "timestamp": "2026-02-11T00:00:00Z"
}

START FREE — 100 API calls/month, no credit card required.

Questions? We respond to every support request within 24 hours.
```

### 4. Configure Endpoints

Add these 5 endpoints in the RapidAPI dashboard:

| Method | Path | Name |
|--------|------|------|
| POST | /api/v1/extract | Extract Content |
| POST | /api/v1/summarize | Summarize Content |
| POST | /api/v1/sentiment | Analyze Sentiment |
| POST | /api/v1/seo | Extract SEO Metadata |
| POST | /api/v1/analyze | Full Analysis |
| POST | /api/v1/compare | Compare Content |
| GET | /health | Health Check |

### 5. Configure Pricing Plans

In **Monetization** → **Plans**:

| Plan | Monthly Price | Rate Limit | Hard Limit | Overage |
|------|--------------|------------|------------|---------|
| Basic (Free) | $0.00 | 100 requests/month | Yes | — |
| Starter | $9.99 | 2,500 requests/month | Soft | $0.005/extra call |
| Pro | $29.99 | 15,000 requests/month | Soft | $0.003/extra call |
| Business | $99.99 | 75,000 requests/month | Soft | $0.002/extra call |

**Plan features to note in each tier:**

- **Basic**: Extract endpoint only, rate-limited to 5 req/min
- **Starter**: All 6 endpoints, 10 req/min
- **Pro**: All 6 endpoints, 30 req/min, priority processing
- **Business**: All 6 endpoints, 60 req/min, bulk processing, priority support

### 6. Add Code Examples

Copy the examples from `rapidapi/examples/` into each endpoint's documentation.

### 7. Set Up Proxy Secret

1. In your RapidAPI dashboard, find your **Proxy Secret**
2. Set it as `RAPIDAPI_PROXY_SECRET` environment variable on your server
3. Uncomment the proxy validation middleware in `app/main.py`

### 8. Test Everything

1. Use RapidAPI's built-in API tester to verify each endpoint
2. Test with all plan types
3. Verify rate limiting works correctly

### 9. Submit for Review

1. Ensure all endpoints have descriptions and example responses
2. Add a logo (256x256 PNG, blue/purple tech aesthetic works well)
3. Set category to **"Data"** and **"Artificial Intelligence/Machine Learning"**
4. Add tags: ai, content, scraping, summarization, sentiment, seo, nlp
5. Click **"Make Public"**

### 10. Post-Launch Checklist

- [ ] API responds correctly through RapidAPI proxy
- [ ] All 4 paid plans are visible
- [ ] Free plan allows testing without credit card
- [ ] Error responses are descriptive and helpful
- [ ] Response times are under 3 seconds for all endpoints
- [ ] Caching is working (repeat calls should be faster)
- [ ] Rate limiting is enforced per plan
