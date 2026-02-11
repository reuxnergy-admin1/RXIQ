# ContentIQ API

**AI-Powered Content Intelligence API** — Extract, summarize, analyze, and compare web content with a single API call.

Listed on [RapidAPI Marketplace](https://rapidapi.com/)

---

## Features

| Endpoint | Description |
|---|---|
| `/extract` | Extract clean text + Markdown, readability scores, reading time |
| `/summarize` | AI-powered summarization (TL;DR, bullets, key takeaways, paragraph) |
| `/sentiment` | Sentiment analysis with confidence scores and key phrases |
| `/seo` | SEO metadata (title, description, OG tags, Twitter Card, Schema.org) |
| `/analyze` | Full analysis: all of the above + keyword extraction + content quality score |
| `/compare` | Side-by-side URL comparison: similarity score, shared/unique keywords, readability diff |

### What Makes RXIQ Different

- **Readability Metrics** — Flesch Reading Ease, Flesch-Kincaid Grade, Coleman-Liau, ARI, vocabulary density, complex word %, reading time (included free on every `/extract` call)
- **Markdown Output** — Get clean Markdown from any URL with `"output_format": "markdown"`
- **Keyword & Entity Extraction** — Auto-extracted keywords, topics, named entities (PERSON/ORG/PLACE/PRODUCT), category classification, and tags
- **Content Quality Score** — Composite 0-100 grade (A+ to F) with breakdown across 5 categories and actionable recommendations
- **Content Comparison** — Compare two URLs: cosine similarity, shared keywords, readability comparison
- **Zero-Cost Features** — Readability, quality scoring, and comparison are computed locally (no API cost), boosting your profit margin

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your OpenAI API key
```

### 3. Run locally

```bash
uvicorn app.main:app --reload --port 8000
```

### 4. Try it out

```bash
curl -X POST http://localhost:8000/api/v1/extract \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

## API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Deployment

### Railway (Recommended for MVP)

```bash
# Install Railway CLI, then:
railway login
railway init
railway up
```

### Render

Use the included `render.yaml` for one-click deploy.

### Docker

```bash
docker build -t rxiq-api .
docker run -p 8000:8000 --env-file .env rxiq-api
```

## Pricing Tiers (RapidAPI)

| Plan | Price/mo | API Calls | Features |
|---|---|---|---|
| Free | $0 | 100 | Extract only, rate-limited |
| Starter | $9.99 | 2,500 | All endpoints |
| Pro | $29.99 | 15,000 | All endpoints + priority |
| Business | $99.99 | 75,000 | All endpoints + bulk |

## Tech Stack

- **Framework**: FastAPI (Python 3.10+)
- **AI**: OpenAI GPT-4o-mini
- **Scraping**: httpx + BeautifulSoup + Trafilatura
- **Caching**: Redis (with in-memory fallback)
- **Security**: SSRF protection, rate limiting, security headers
- **Monitoring**: Sentry + Prometheus
- **CI**: GitHub Actions (test + lint + Docker)

## Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=app --cov-report=term-missing

# Run specific test file
python -m pytest tests/test_api.py -v
```

**174 tests** covering API validation, mocked routes, AI service, scraper, URL validator, cache, text analytics, new features, and middleware.

## Project Structure

```
rxiq-api/
├── app/
│   ├── main.py              # FastAPI app + middleware
│   ├── config.py             # Settings from env vars
│   ├── models.py             # Pydantic request/response models
│   ├── pricing.py            # RapidAPI tier definitions
│   ├── routes/v1.py          # All 6 API endpoints
│   └── services/
│       ├── ai_service.py     # OpenAI summarization + sentiment + keywords
│       ├── cache.py          # Redis + in-memory caching
│       ├── scraper.py        # Web scraping + content/markdown extraction
│       ├── text_analytics.py # Readability, quality scoring, similarity (zero-cost)
│       └── url_validator.py  # SSRF protection
├── tests/                    # 174 tests
├── .github/workflows/ci.yml  # GitHub Actions CI
├── Dockerfile                # Production Docker image
├── docker-compose.yml        # API + Redis
├── rapidapi/                 # RapidAPI listing assets
├── RAPIDAPI_DEPLOY.md        # Step-by-step RapidAPI deployment guide
└── requirements.txt
```

## License

Proprietary — All rights reserved.
