#!/bin/bash
# RXIQ API — cURL Usage Examples

BASE_URL="https://rxiq-api.p.rapidapi.com"
API_KEY="ef7129c761msh9476e78fc3f01ecp1b52dbjsn5620584fb605"
API_HOST="rxiq-api.p.rapidapi.com"

# ──────────────────────────────────────────────
# 1. Extract Content from URL
# ──────────────────────────────────────────────

echo "=== 1. EXTRACT CONTENT ==="
curl -s -X POST "$BASE_URL/api/v1/extract" \
  -H "Content-Type: application/json" \
  -H "X-RapidAPI-Key: $API_KEY" \
  -H "X-RapidAPI-Host: $API_HOST" \
  -d '{
    "url": "https://example.com",
    "include_images": false,
    "include_links": false
  }' | python -m json.tool

echo ""

# ──────────────────────────────────────────────
# 2. Summarize URL Content
# ──────────────────────────────────────────────

echo "=== 2. SUMMARIZE (bullets) ==="
curl -s -X POST "$BASE_URL/api/v1/summarize" \
  -H "Content-Type: application/json" \
  -H "X-RapidAPI-Key: $API_KEY" \
  -H "X-RapidAPI-Host: $API_HOST" \
  -d '{
    "url": "https://example.com",
    "format": "bullets",
    "max_length": 200,
    "language": "en"
  }' | python -m json.tool

echo ""

# ──────────────────────────────────────────────
# 2b. Summarize Raw Text
# ──────────────────────────────────────────────

echo "=== 2b. SUMMARIZE TEXT (tldr) ==="
curl -s -X POST "$BASE_URL/api/v1/summarize" \
  -H "Content-Type: application/json" \
  -H "X-RapidAPI-Key: $API_KEY" \
  -H "X-RapidAPI-Host: $API_HOST" \
  -d '{
    "text": "Artificial intelligence has transformed multiple industries. From healthcare diagnostics to autonomous vehicles, AI systems are becoming increasingly sophisticated.",
    "format": "tldr",
    "max_length": 50
  }' | python -m json.tool

echo ""

# ──────────────────────────────────────────────
# 3. Sentiment Analysis
# ──────────────────────────────────────────────

echo "=== 3. SENTIMENT ANALYSIS ==="
curl -s -X POST "$BASE_URL/api/v1/sentiment" \
  -H "Content-Type: application/json" \
  -H "X-RapidAPI-Key: $API_KEY" \
  -H "X-RapidAPI-Host: $API_HOST" \
  -d '{
    "text": "This product is absolutely amazing! Best purchase I have ever made. The quality exceeded my expectations."
  }' | python -m json.tool

echo ""

# ──────────────────────────────────────────────
# 4. SEO Metadata Extraction
# ──────────────────────────────────────────────

echo "=== 4. SEO METADATA ==="
curl -s -X POST "$BASE_URL/api/v1/seo" \
  -H "Content-Type: application/json" \
  -H "X-RapidAPI-Key: $API_KEY" \
  -H "X-RapidAPI-Host: $API_HOST" \
  -d '{
    "url": "https://example.com"
  }' | python -m json.tool

echo ""

# ──────────────────────────────────────────────
# 5. Full Analysis (all-in-one)
# ──────────────────────────────────────────────

echo "=== 5. FULL ANALYSIS ==="
curl -s -X POST "$BASE_URL/api/v1/analyze" \
  -H "Content-Type: application/json" \
  -H "X-RapidAPI-Key: $API_KEY" \
  -H "X-RapidAPI-Host: $API_HOST" \
  -d '{
    "url": "https://example.com",
    "summary_format": "key_takeaways",
    "summary_max_length": 200
  }' | python -m json.tool

echo ""

# ──────────────────────────────────────────────
# 6. Health Check
# ──────────────────────────────────────────────

echo "=== HEALTH CHECK ==="
curl -s "$BASE_URL/health" | python -m json.tool
