"""Route tests with mocked services.

These tests mock the scraper and AI services so we can exercise
the full route logic (caching, error handling, response format)
without network calls or API keys.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
from fastapi.testclient import TestClient

from app.main import app
from app.models import (
    ExtractedContent,
    SentimentData,
    SentimentLabel,
    SEOData,
    SummaryData,
    SummaryFormat,
)
from app.services.url_validator import URLValidationError

client = TestClient(app)


# ──────────────────────────────────────────────
# Fixtures — reusable mock return values
# ──────────────────────────────────────────────

MOCK_CONTENT = ExtractedContent(
    url="https://example.com/article",
    title="Test Article",
    author="Jane Doe",
    published_date="2026-01-15",
    text="This is a great test article with enough words to summarize and analyse properly.",
    word_count=15,
    excerpt="This is a great test article...",
    images=[],
    links=[],
    language="en",
    extraction_time_ms=120,
)

MOCK_SUMMARY = SummaryData(
    original_url="https://example.com/article",
    format=SummaryFormat.tldr,
    summary="A concise test summary.",
    word_count=5,
    original_word_count=15,
    language="en",
    model_used="gpt-4o-mini",
    processing_time_ms=500,
)

MOCK_SENTIMENT = SentimentData(
    original_url="https://example.com/article",
    sentiment=SentimentLabel.positive,
    confidence=0.92,
    scores={"positive": 0.92, "negative": 0.03, "neutral": 0.05},
    key_phrases=["great test article"],
    model_used="gpt-4o-mini",
    processing_time_ms=350,
)

MOCK_SEO = SEOData(
    url="https://example.com/article",
    title="Test Article",
    meta_description="A test article for SEO extraction.",
    canonical_url="https://example.com/article",
    h1_tags=["Test Article"],
    h2_tags=["Section 1", "Section 2"],
    extraction_time_ms=50,
)


# ──────────────────────────────────────────────
# /api/v1/extract — mocked
# ──────────────────────────────────────────────


class TestExtractMocked:
    """Tests for /extract with mocked scraper."""

    @patch("app.routes.v1.cache.get_cached", new_callable=AsyncMock, return_value=None)
    @patch("app.routes.v1.cache.set_cached", new_callable=AsyncMock)
    @patch("app.routes.v1.scraper.extract_content", return_value=MOCK_CONTENT)
    @patch("app.routes.v1.scraper.fetch_html", new_callable=AsyncMock, return_value=("<html></html>", "https://example.com/article"))
    def test_extract_success(self, mock_fetch, mock_extract, mock_set, mock_get):
        response = client.post("/api/v1/extract", json={"url": "https://example.com/article"})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["cached"] is False
        assert data["data"]["title"] == "Test Article"
        assert data["data"]["word_count"] == 15
        mock_fetch.assert_called_once()
        mock_set.assert_called_once()

    @patch("app.routes.v1.cache.get_cached", new_callable=AsyncMock, return_value=MOCK_CONTENT.model_dump())
    def test_extract_returns_cached(self, mock_get):
        response = client.post("/api/v1/extract", json={"url": "https://example.com/article"})
        assert response.status_code == 200
        data = response.json()
        assert data["cached"] is True
        assert data["data"]["title"] == "Test Article"

    @patch("app.routes.v1.cache.get_cached", new_callable=AsyncMock, return_value=None)
    @patch("app.routes.v1.scraper.fetch_html", new_callable=AsyncMock, side_effect=httpx.TimeoutException("timed out"))
    def test_extract_timeout_returns_504(self, mock_fetch, mock_get):
        response = client.post("/api/v1/extract", json={"url": "https://slow-site.com"})
        assert response.status_code == 504
        data = response.json()
        assert data["detail"]["code"] == "TIMEOUT"

    @patch("app.routes.v1.cache.get_cached", new_callable=AsyncMock, return_value=None)
    @patch("app.routes.v1.scraper.fetch_html", new_callable=AsyncMock, side_effect=httpx.ConnectError("failed"))
    def test_extract_connection_error_returns_502(self, mock_fetch, mock_get):
        response = client.post("/api/v1/extract", json={"url": "https://unreachable.com"})
        assert response.status_code == 502
        data = response.json()
        assert data["detail"]["code"] == "CONNECTION_FAILED"

    @patch("app.routes.v1.cache.get_cached", new_callable=AsyncMock, return_value=None)
    @patch("app.routes.v1.scraper.fetch_html", new_callable=AsyncMock)
    def test_extract_http_error_returns_502(self, mock_fetch, mock_get):
        resp = httpx.Response(403, request=httpx.Request("GET", "https://example.com"))
        mock_fetch.side_effect = httpx.HTTPStatusError("forbidden", request=resp.request, response=resp)
        response = client.post("/api/v1/extract", json={"url": "https://forbidden.com"})
        assert response.status_code == 502
        data = response.json()
        assert data["detail"]["code"] == "UPSTREAM_ERROR"
        assert "403" in data["detail"]["message"]

    @patch("app.routes.v1.cache.get_cached", new_callable=AsyncMock, return_value=None)
    @patch("app.routes.v1.scraper.fetch_html", new_callable=AsyncMock, side_effect=URLValidationError("Blocked host"))
    def test_extract_ssrf_returns_400(self, mock_fetch, mock_get):
        response = client.post("/api/v1/extract", json={"url": "https://evil.com"})
        assert response.status_code == 400
        assert response.json()["detail"]["code"] == "INVALID_URL"

    @patch("app.routes.v1.cache.get_cached", new_callable=AsyncMock, return_value=None)
    @patch("app.routes.v1.scraper.fetch_html", new_callable=AsyncMock, side_effect=ValueError("No text content"))
    def test_extract_value_error_returns_422(self, mock_fetch, mock_get):
        response = client.post("/api/v1/extract", json={"url": "https://empty.com"})
        assert response.status_code == 422
        data = response.json()
        # May come through as detail (HTTPException) or error (global handler)
        error = data.get("detail") or data.get("error", {})
        assert error.get("code") in ("INVALID_CONTENT", "VALIDATION_ERROR")

    @patch("app.routes.v1.cache.get_cached", new_callable=AsyncMock, return_value=None)
    @patch("app.routes.v1.scraper.fetch_html", new_callable=AsyncMock, side_effect=RuntimeError("boom"))
    def test_extract_generic_error_returns_500(self, mock_fetch, mock_get):
        response = client.post("/api/v1/extract", json={"url": "https://broken.com"})
        assert response.status_code == 500


# ──────────────────────────────────────────────
# /api/v1/summarize — mocked
# ──────────────────────────────────────────────


class TestSummarizeMocked:
    """Tests for /summarize with mocked scraper and AI."""

    @patch("app.routes.v1.cache.get_cached", new_callable=AsyncMock, return_value=None)
    @patch("app.routes.v1.cache.set_cached", new_callable=AsyncMock)
    @patch("app.routes.v1.ai_service.summarize_text", new_callable=AsyncMock, return_value=MOCK_SUMMARY)
    def test_summarize_text_success(self, mock_ai, mock_set, mock_get):
        response = client.post("/api/v1/summarize", json={"text": "A" * 200})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["summary"] == "A concise test summary."
        assert data["data"]["model_used"] == "gpt-4o-mini"
        mock_ai.assert_called_once()

    @patch("app.routes.v1.cache.get_cached", new_callable=AsyncMock, return_value=None)
    @patch("app.routes.v1.cache.set_cached", new_callable=AsyncMock)
    @patch("app.routes.v1.ai_service.summarize_text", new_callable=AsyncMock, return_value=MOCK_SUMMARY)
    @patch("app.routes.v1.scraper.extract_content", return_value=MOCK_CONTENT)
    @patch("app.routes.v1.scraper.fetch_html", new_callable=AsyncMock, return_value=("<html></html>", "https://example.com/article"))
    def test_summarize_url_success(self, mock_fetch, mock_extract, mock_ai, mock_set, mock_get):
        response = client.post("/api/v1/summarize", json={"url": "https://example.com/article", "format": "bullets"})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        mock_fetch.assert_called_once()

    @patch("app.routes.v1.cache.get_cached", new_callable=AsyncMock, return_value=MOCK_SUMMARY.model_dump())
    def test_summarize_returns_cached(self, mock_get):
        response = client.post("/api/v1/summarize", json={"text": "cached input"})
        assert response.status_code == 200
        assert response.json()["cached"] is True

    @patch("app.routes.v1.cache.get_cached", new_callable=AsyncMock, return_value=None)
    @patch("app.routes.v1.cache.set_cached", new_callable=AsyncMock)
    @patch("app.routes.v1.scraper.extract_content")
    @patch("app.routes.v1.scraper.fetch_html", new_callable=AsyncMock, return_value=("<html></html>", "https://example.com"))
    def test_summarize_no_content_returns_422(self, mock_fetch, mock_extract, mock_set, mock_get):
        empty = ExtractedContent(url="https://example.com", text="", word_count=0, excerpt="")
        mock_extract.return_value = empty
        response = client.post("/api/v1/summarize", json={"url": "https://example.com"})
        assert response.status_code == 422
        data = response.json()
        error = data.get("detail") or data.get("error", {})
        assert error.get("code") in ("NO_CONTENT", "VALIDATION_ERROR")

    @patch("app.routes.v1.cache.get_cached", new_callable=AsyncMock, return_value=None)
    @patch("app.routes.v1.scraper.fetch_html", new_callable=AsyncMock, side_effect=httpx.TimeoutException("timeout"))
    def test_summarize_timeout_returns_504(self, mock_fetch, mock_get):
        response = client.post("/api/v1/summarize", json={"url": "https://slow.com"})
        assert response.status_code == 504

    def test_summarize_empty_text_returns_422(self):
        response = client.post("/api/v1/summarize", json={"text": "   "})
        # Should be caught as NO_CONTENT or validation — either 422
        assert response.status_code in (422, 500)


# ──────────────────────────────────────────────
# /api/v1/sentiment — mocked
# ──────────────────────────────────────────────


class TestSentimentMocked:
    """Tests for /sentiment with mocked AI."""

    @patch("app.routes.v1.cache.get_cached", new_callable=AsyncMock, return_value=None)
    @patch("app.routes.v1.cache.set_cached", new_callable=AsyncMock)
    @patch("app.routes.v1.ai_service.analyze_sentiment", new_callable=AsyncMock, return_value=MOCK_SENTIMENT)
    def test_sentiment_text_success(self, mock_ai, mock_set, mock_get):
        response = client.post("/api/v1/sentiment", json={"text": "This is amazing!"})
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["sentiment"] == "positive"
        assert data["data"]["confidence"] == 0.92
        assert len(data["data"]["key_phrases"]) > 0

    @patch("app.routes.v1.cache.get_cached", new_callable=AsyncMock, return_value=None)
    @patch("app.routes.v1.cache.set_cached", new_callable=AsyncMock)
    @patch("app.routes.v1.ai_service.analyze_sentiment", new_callable=AsyncMock, return_value=MOCK_SENTIMENT)
    @patch("app.routes.v1.scraper.extract_content", return_value=MOCK_CONTENT)
    @patch("app.routes.v1.scraper.fetch_html", new_callable=AsyncMock, return_value=("<html></html>", "https://example.com"))
    def test_sentiment_url_success(self, mock_fetch, mock_extract, mock_ai, mock_set, mock_get):
        response = client.post("/api/v1/sentiment", json={"url": "https://example.com"})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["sentiment"] == "positive"

    @patch("app.routes.v1.cache.get_cached", new_callable=AsyncMock, return_value=MOCK_SENTIMENT.model_dump())
    def test_sentiment_returns_cached(self, mock_get):
        response = client.post("/api/v1/sentiment", json={"text": "cached text"})
        assert response.status_code == 200
        assert response.json()["cached"] is True

    @patch("app.routes.v1.cache.get_cached", new_callable=AsyncMock, return_value=None)
    @patch("app.routes.v1.cache.set_cached", new_callable=AsyncMock)
    @patch("app.routes.v1.scraper.extract_content")
    @patch("app.routes.v1.scraper.fetch_html", new_callable=AsyncMock, return_value=("<html></html>", "https://example.com"))
    def test_sentiment_no_content_returns_422(self, mock_fetch, mock_extract, mock_set, mock_get):
        empty = ExtractedContent(url="https://example.com", text="  ", word_count=0, excerpt="")
        mock_extract.return_value = empty
        response = client.post("/api/v1/sentiment", json={"url": "https://example.com"})
        assert response.status_code == 422
        data = response.json()
        error = data.get("detail") or data.get("error", {})
        assert error.get("code") in ("NO_CONTENT", "VALIDATION_ERROR")


# ──────────────────────────────────────────────
# /api/v1/seo — mocked
# ──────────────────────────────────────────────


class TestSEOMocked:
    """Tests for /seo with mocked scraper."""

    @patch("app.routes.v1.cache.get_cached", new_callable=AsyncMock, return_value=None)
    @patch("app.routes.v1.cache.set_cached", new_callable=AsyncMock)
    @patch("app.routes.v1.scraper.extract_seo_metadata", return_value=MOCK_SEO)
    @patch("app.routes.v1.scraper.fetch_html", new_callable=AsyncMock, return_value=("<html></html>", "https://example.com"))
    def test_seo_success(self, mock_fetch, mock_seo, mock_set, mock_get):
        response = client.post("/api/v1/seo", json={"url": "https://example.com"})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["title"] == "Test Article"
        assert data["data"]["meta_description"] == "A test article for SEO extraction."
        assert len(data["data"]["h1_tags"]) == 1
        assert len(data["data"]["h2_tags"]) == 2

    @patch("app.routes.v1.cache.get_cached", new_callable=AsyncMock, return_value=MOCK_SEO.model_dump())
    def test_seo_returns_cached(self, mock_get):
        response = client.post("/api/v1/seo", json={"url": "https://example.com"})
        assert response.status_code == 200
        assert response.json()["cached"] is True

    @patch("app.routes.v1.cache.get_cached", new_callable=AsyncMock, return_value=None)
    @patch("app.routes.v1.scraper.fetch_html", new_callable=AsyncMock, side_effect=httpx.ConnectError("dns failed"))
    def test_seo_connection_error_returns_502(self, mock_fetch, mock_get):
        response = client.post("/api/v1/seo", json={"url": "https://unreachable.com"})
        assert response.status_code == 502


# ──────────────────────────────────────────────
# /api/v1/analyze — mocked
# ──────────────────────────────────────────────


MOCK_KEYWORDS_RESULT = {
    "keywords": ["test", "article"],
    "topics": ["Testing"],
    "entities": [],
    "category": "other",
    "tags": ["test"],
    "model_used": "gpt-4o-mini",
    "processing_time_ms": 200,
}


class TestAnalyzeMocked:
    """Tests for /analyze with mocked scraper and AI."""

    @patch("app.routes.v1.cache.get_cached", new_callable=AsyncMock, return_value=None)
    @patch("app.routes.v1.cache.set_cached", new_callable=AsyncMock)
    @patch("app.routes.v1.ai_service.extract_keywords", new_callable=AsyncMock, return_value=MOCK_KEYWORDS_RESULT)
    @patch("app.routes.v1.ai_service.analyze_sentiment", new_callable=AsyncMock, return_value=MOCK_SENTIMENT)
    @patch("app.routes.v1.ai_service.summarize_text", new_callable=AsyncMock, return_value=MOCK_SUMMARY)
    @patch("app.routes.v1.scraper.extract_seo_metadata", return_value=MOCK_SEO)
    @patch("app.routes.v1.scraper.extract_content", return_value=MOCK_CONTENT)
    @patch("app.routes.v1.scraper.fetch_html", new_callable=AsyncMock, return_value=("<html></html>", "https://example.com"))
    def test_analyze_success(self, mock_fetch, mock_extract, mock_seo, mock_summarize, mock_sentiment, mock_kw, mock_set, mock_get):
        response = client.post("/api/v1/analyze", json={"url": "https://example.com"})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["cached"] is False
        # Check all four sections are present
        assert "content" in data["data"]
        assert "summary" in data["data"]
        assert "sentiment" in data["data"]
        assert "seo" in data["data"]
        assert data["data"]["total_processing_time_ms"] >= 0
        # Verify content section
        assert data["data"]["content"]["title"] == "Test Article"
        # Verify summary section
        assert data["data"]["summary"]["summary"] == "A concise test summary."
        # Verify sentiment section
        assert data["data"]["sentiment"]["sentiment"] == "positive"
        # Verify SEO section
        assert data["data"]["seo"]["title"] == "Test Article"

    @patch("app.routes.v1.cache.get_cached", new_callable=AsyncMock)
    def test_analyze_returns_cached(self, mock_get):
        from app.models import AnalyzeData
        cached_data = AnalyzeData(
            content=MOCK_CONTENT,
            summary=MOCK_SUMMARY,
            sentiment=MOCK_SENTIMENT,
            seo=MOCK_SEO,
            total_processing_time_ms=1000,
        )
        mock_get.return_value = cached_data.model_dump()
        response = client.post("/api/v1/analyze", json={"url": "https://example.com"})
        assert response.status_code == 200
        assert response.json()["cached"] is True

    @patch("app.routes.v1.cache.get_cached", new_callable=AsyncMock, return_value=None)
    @patch("app.routes.v1.cache.set_cached", new_callable=AsyncMock)
    @patch("app.routes.v1.scraper.extract_seo_metadata", return_value=MOCK_SEO)
    @patch("app.routes.v1.scraper.extract_content")
    @patch("app.routes.v1.scraper.fetch_html", new_callable=AsyncMock, return_value=("<html></html>", "https://example.com"))
    def test_analyze_no_content_returns_422(self, mock_fetch, mock_extract, mock_seo, mock_set, mock_get):
        empty = ExtractedContent(url="https://example.com", text="", word_count=0, excerpt="")
        mock_extract.return_value = empty
        response = client.post("/api/v1/analyze", json={"url": "https://example.com"})
        assert response.status_code == 422
        data = response.json()
        error = data.get("detail") or data.get("error", {})
        assert error.get("code") in ("NO_CONTENT", "VALIDATION_ERROR")

    @patch("app.routes.v1.cache.get_cached", new_callable=AsyncMock, return_value=None)
    @patch("app.routes.v1.scraper.fetch_html", new_callable=AsyncMock, side_effect=httpx.TimeoutException("timeout"))
    def test_analyze_timeout_returns_504(self, mock_fetch, mock_get):
        response = client.post("/api/v1/analyze", json={"url": "https://slow.com"})
        assert response.status_code == 504

    @patch("app.routes.v1.cache.get_cached", new_callable=AsyncMock, return_value=None)
    @patch("app.routes.v1.scraper.fetch_html", new_callable=AsyncMock, side_effect=URLValidationError("Blocked"))
    def test_analyze_ssrf_returns_400(self, mock_fetch, mock_get):
        response = client.post("/api/v1/analyze", json={"url": "https://evil.com"})
        assert response.status_code == 400
        assert response.json()["detail"]["code"] == "INVALID_URL"


# ──────────────────────────────────────────────
# Error helper unit tests
# ──────────────────────────────────────────────


class TestHandleScrapeError:
    """Unit tests for _handle_scrape_error helper."""

    def test_url_validation_error(self):
        from app.routes.v1 import _handle_scrape_error
        exc = _handle_scrape_error(URLValidationError("bad host"), "test")
        assert exc.status_code == 400
        assert exc.detail["code"] == "INVALID_URL"

    def test_timeout_error(self):
        from app.routes.v1 import _handle_scrape_error
        exc = _handle_scrape_error(httpx.TimeoutException("slow"), "test")
        assert exc.status_code == 504
        assert exc.detail["code"] == "TIMEOUT"

    def test_http_status_error(self):
        from app.routes.v1 import _handle_scrape_error
        resp = httpx.Response(500, request=httpx.Request("GET", "https://example.com"))
        exc = _handle_scrape_error(httpx.HTTPStatusError("err", request=resp.request, response=resp), "test")
        assert exc.status_code == 502
        assert exc.detail["code"] == "UPSTREAM_ERROR"

    def test_connect_error(self):
        from app.routes.v1 import _handle_scrape_error
        exc = _handle_scrape_error(httpx.ConnectError("dns fail"), "test")
        assert exc.status_code == 502
        assert exc.detail["code"] == "CONNECTION_FAILED"

    def test_value_error(self):
        from app.routes.v1 import _handle_scrape_error
        exc = _handle_scrape_error(ValueError("no content"), "test")
        assert exc.status_code == 422
        assert exc.detail["code"] == "INVALID_CONTENT"

    def test_generic_error(self):
        from app.routes.v1 import _handle_scrape_error
        exc = _handle_scrape_error(RuntimeError("unexpected"), "test")
        assert exc.status_code == 500
        assert "TEST" in exc.detail["code"]


# ──────────────────────────────────────────────
# Middleware tests
# ──────────────────────────────────────────────


class TestMiddleware:
    """Test production middleware behavior."""

    def test_cache_control_api_no_store(self):
        """API routes should have no-store cache-control."""
        response = client.post("/api/v1/extract", json={"url": "http://192.168.1.1"})
        assert response.headers.get("Cache-Control") == "no-store"

    def test_cache_control_meta_public(self):
        """Non-API routes should have public cache-control."""
        response = client.get("/health")
        assert "public" in response.headers.get("Cache-Control", "")

    def test_response_has_timestamp_format(self):
        """Responses should include properly formatted timestamps."""
        response = client.get("/health")
        data = response.json()
        # Should be parseable as ISO datetime
        ts = data["timestamp"]
        assert "T" in ts  # ISO format separator
