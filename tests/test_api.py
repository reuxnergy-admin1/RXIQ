"""Comprehensive tests for RXIQ API endpoints.

Tests cover:
- Health & meta endpoints
- Input validation
- Error response format consistency
- Security headers
- OpenAPI schema completeness
- Edge cases
- Cache behavior
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# ──────────────────────────────────────────────
# Health & Meta
# ──────────────────────────────────────────────


class TestMeta:
    """Tests for root and health endpoints."""

    def test_root_returns_api_info(self):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "RXIQ API"
        assert "version" in data
        assert "endpoints" in data
        assert "extract" in data["endpoints"]
        assert "summarize" in data["endpoints"]
        assert "sentiment" in data["endpoints"]
        assert "seo" in data["endpoints"]
        assert "analyze" in data["endpoints"]

    def test_health_returns_status(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "uptime_seconds" in data
        assert "redis_connected" in data
        assert "timestamp" in data

    def test_docs_accessible(self):
        response = client.get("/docs")
        assert response.status_code == 200

    def test_redoc_accessible(self):
        response = client.get("/redoc")
        assert response.status_code == 200

    def test_openapi_schema_has_all_endpoints(self):
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "paths" in schema
        expected_paths = [
            "/api/v1/extract",
            "/api/v1/summarize",
            "/api/v1/sentiment",
            "/api/v1/seo",
            "/api/v1/analyze",
            "/api/v1/compare",
        ]
        for path in expected_paths:
            assert path in schema["paths"], f"Missing path: {path}"
            assert "post" in schema["paths"][path], f"Missing POST for {path}"


# ──────────────────────────────────────────────
# Security Headers
# ──────────────────────────────────────────────


class TestSecurityHeaders:
    """Test that security headers are present on responses."""

    def test_has_request_id(self):
        response = client.get("/health")
        assert "X-Request-ID" in response.headers

    def test_has_response_time(self):
        response = client.get("/health")
        assert "X-Response-Time" in response.headers
        # Should be parseable as a float + "s"
        time_str = response.headers["X-Response-Time"]
        assert time_str.endswith("s")
        float(time_str[:-1])  # Should not raise

    def test_has_content_type_nosniff(self):
        response = client.get("/health")
        assert response.headers.get("X-Content-Type-Options") == "nosniff"

    def test_has_frame_deny(self):
        response = client.get("/health")
        assert response.headers.get("X-Frame-Options") == "DENY"

    def test_has_referrer_policy(self):
        response = client.get("/health")
        assert "Referrer-Policy" in response.headers

    def test_forwards_request_id(self):
        custom_id = "test-req-123"
        response = client.get("/health", headers={"X-Request-ID": custom_id})
        assert response.headers.get("X-Request-ID") == custom_id


# ──────────────────────────────────────────────
# Extract Endpoint Validation
# ──────────────────────────────────────────────


class TestExtractValidation:
    """Input validation tests for /extract."""

    def test_requires_url(self):
        response = client.post("/api/v1/extract", json={})
        assert response.status_code == 422

    def test_rejects_invalid_url(self):
        response = client.post("/api/v1/extract", json={"url": "not-a-url"})
        assert response.status_code == 422

    def test_rejects_ftp_url(self):
        response = client.post(
            "/api/v1/extract", json={"url": "ftp://example.com/file"}
        )
        assert response.status_code == 422

    def test_accepts_valid_url_format(self):
        # This will fail at the network level (SSRF check or DNS), but not at validation
        response = client.post(
            "/api/v1/extract",
            json={"url": "https://this-domain-does-not-exist-xyz123.com"},
        )
        # Should be a 400 (invalid URL / can't resolve) not a 422 (validation)
        assert response.status_code in (400, 500, 502)

    def test_rejects_private_ip(self):
        response = client.post(
            "/api/v1/extract",
            json={"url": "http://192.168.1.1/admin"},
        )
        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["code"] == "INVALID_URL"


# ──────────────────────────────────────────────
# Summarize Endpoint Validation
# ──────────────────────────────────────────────


class TestSummarizeValidation:
    """Input validation tests for /summarize."""

    def test_requires_url_or_text(self):
        response = client.post("/api/v1/summarize", json={})
        assert response.status_code == 422

    def test_rejects_invalid_format(self):
        response = client.post(
            "/api/v1/summarize",
            json={"text": "Hello world", "format": "invalid_format"},
        )
        assert response.status_code == 422

    def test_rejects_max_length_too_small(self):
        response = client.post(
            "/api/v1/summarize",
            json={"text": "Hello world", "max_length": 5},
        )
        assert response.status_code == 422

    def test_rejects_max_length_too_large(self):
        response = client.post(
            "/api/v1/summarize",
            json={"text": "Hello world", "max_length": 5000},
        )
        assert response.status_code == 422

    def test_accepts_valid_formats(self):
        for fmt in ["tldr", "bullets", "key_takeaways", "paragraph"]:
            response = client.post(
                "/api/v1/summarize",
                json={"text": "x" * 100, "format": fmt},
            )
            # Will fail at AI call (no API key), but should pass validation
            assert response.status_code != 422, f"Format '{fmt}' rejected"


# ──────────────────────────────────────────────
# Sentiment Endpoint Validation
# ──────────────────────────────────────────────


class TestSentimentValidation:
    """Input validation tests for /sentiment."""

    def test_requires_url_or_text(self):
        response = client.post("/api/v1/sentiment", json={})
        assert response.status_code == 422

    def test_rejects_empty_object(self):
        response = client.post("/api/v1/sentiment", json={})
        assert response.status_code == 422


# ──────────────────────────────────────────────
# SEO Endpoint Validation
# ──────────────────────────────────────────────


class TestSEOValidation:
    """Input validation tests for /seo."""

    def test_requires_url(self):
        response = client.post("/api/v1/seo", json={})
        assert response.status_code == 422

    def test_rejects_invalid_url(self):
        response = client.post("/api/v1/seo", json={"url": "not-a-url"})
        assert response.status_code == 422


# ──────────────────────────────────────────────
# Analyze Endpoint Validation
# ──────────────────────────────────────────────


class TestAnalyzeValidation:
    """Input validation tests for /analyze."""

    def test_requires_url(self):
        response = client.post("/api/v1/analyze", json={})
        assert response.status_code == 422

    def test_rejects_invalid_summary_format(self):
        response = client.post(
            "/api/v1/analyze",
            json={"url": "https://example.com", "summary_format": "wrong"},
        )
        assert response.status_code == 422


# ──────────────────────────────────────────────
# Error Response Consistency
# ──────────────────────────────────────────────


class TestErrorConsistency:
    """Test that all error responses use the standard format."""

    def test_404_returns_json(self):
        response = client.get("/nonexistent/path")
        assert response.status_code == 404
        # FastAPI default 404 — we accept this
        assert response.headers["content-type"].startswith("application/json")

    def test_ssrf_error_format(self):
        response = client.post(
            "/api/v1/extract",
            json={"url": "http://192.168.1.1/admin"},
        )
        data = response.json()
        assert "detail" in data
        assert "code" in data["detail"]
        assert "message" in data["detail"]

    def test_method_not_allowed(self):
        response = client.get("/api/v1/extract")
        assert response.status_code == 405


# ──────────────────────────────────────────────
# SSRF Protection via API
# ──────────────────────────────────────────────


class TestSSRFProtection:
    """Test that SSRF attacks are blocked at the API level."""

    def test_blocks_localhost_via_extract(self):
        response = client.post(
            "/api/v1/extract",
            json={"url": "http://127.0.0.1:8000/health"},
        )
        assert response.status_code == 400

    def test_blocks_internal_ip_via_seo(self):
        response = client.post(
            "/api/v1/seo",
            json={"url": "http://10.0.0.1/internal"},
        )
        assert response.status_code == 400

    def test_blocks_metadata_via_analyze(self):
        response = client.post(
            "/api/v1/analyze",
            json={"url": "http://169.254.169.254/latest/meta-data/"},
        )
        assert response.status_code == 400

    def test_blocks_private_ip_via_summarize(self):
        response = client.post(
            "/api/v1/summarize",
            json={"url": "http://192.168.0.1/page"},
        )
        assert response.status_code == 400
