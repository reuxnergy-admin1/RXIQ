"""Tests for new features: markdown output, readability, keywords, quality score, compare endpoint.

Mocked scraper and AI services — no network calls needed.
"""

from __future__ import annotations

from dataclasses import asdict
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.models import (
    ExtractedContent,
    ReadabilityMetrics,
    SentimentData,
    SentimentLabel,
    SEOData,
    SummaryData,
    SummaryFormat,
)
from app.services.text_analytics import ReadabilityScores

client = TestClient(app)

# ──────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────

SAMPLE_TEXT = (
    "Artificial intelligence has transformed the technology landscape dramatically. "
    "Machine learning algorithms now power everything from search engines to self-driving cars. "
    "Natural language processing enables computers to understand and generate human text. "
    "Deep learning neural networks can recognize images and speech with remarkable accuracy. "
    "The rapid growth of AI has raised important ethical questions about privacy and bias."
)

MOCK_READABILITY = ReadabilityMetrics(
    flesch_reading_ease=45.0,
    flesch_kincaid_grade=12.5,
    coleman_liau_index=14.0,
    automated_readability_index=13.0,
    avg_grade_level=13.2,
    reading_level="Difficult (College)",
    sentence_count=5,
    word_count=65,
    syllable_count=110,
    char_count=350,
    avg_sentence_length=13.0,
    avg_word_length=5.4,
    avg_syllables_per_word=1.7,
    unique_words=55,
    vocabulary_density=0.846,
    complex_word_count=15,
    complex_word_pct=23.1,
    reading_time_seconds=16,
    reading_time_minutes=0.3,
)

MOCK_CONTENT = ExtractedContent(
    url="https://example.com/article",
    title="Test Article",
    author="Jane Doe",
    text=SAMPLE_TEXT,
    word_count=65,
    excerpt=SAMPLE_TEXT[:300],
    readability=MOCK_READABILITY,
    language="en",
    extraction_time_ms=120,
)

MOCK_CONTENT_WITH_MARKDOWN = ExtractedContent(
    url="https://example.com/article",
    title="Test Article",
    author="Jane Doe",
    text=SAMPLE_TEXT,
    markdown="# Test Article\n\nArtificial intelligence has transformed...",
    word_count=65,
    excerpt=SAMPLE_TEXT[:300],
    readability=MOCK_READABILITY,
    language="en",
    extraction_time_ms=150,
)

MOCK_SUMMARY = SummaryData(
    original_url="https://example.com/article",
    format=SummaryFormat.tldr,
    summary="AI transforms technology.",
    word_count=4,
    original_word_count=65,
    language="en",
    model_used="gpt-4o-mini",
    processing_time_ms=400,
)

MOCK_SENTIMENT = SentimentData(
    original_url="https://example.com/article",
    sentiment=SentimentLabel.positive,
    confidence=0.85,
    scores={"positive": 0.85, "negative": 0.05, "neutral": 0.10},
    key_phrases=["transformed", "remarkable accuracy"],
    model_used="gpt-4o-mini",
    processing_time_ms=300,
)

MOCK_SEO = SEOData(
    url="https://example.com/article",
    title="Test Article",
    meta_description="A test article about AI.",
    canonical_url="https://example.com/article",
    h1_tags=["Test Article"],
    h2_tags=["Section 1", "Section 2"],
    total_images=3,
    images_without_alt=0,
    internal_links=5,
    external_links=2,
    extraction_time_ms=50,
)

MOCK_KEYWORDS = {
    "keywords": ["artificial intelligence", "machine learning", "deep learning"],
    "topics": ["Technology", "AI"],
    "entities": [{"name": "AI", "type": "PRODUCT"}],
    "category": "technology",
    "tags": ["ai", "machine-learning", "technology"],
    "model_used": "gpt-4o-mini",
    "processing_time_ms": 350,
}


# ──────────────────────────────────────────────
# /api/v1/extract — new features
# ──────────────────────────────────────────────


class TestExtractNewFeatures:
    """Tests for readability and markdown in /extract."""

    @patch("app.routes.v1.cache.get_cached", new_callable=AsyncMock, return_value=None)
    @patch("app.routes.v1.cache.set_cached", new_callable=AsyncMock)
    @patch("app.routes.v1.scraper.extract_content", return_value=MOCK_CONTENT)
    @patch("app.routes.v1.scraper.fetch_html", new_callable=AsyncMock, return_value=("<html></html>", "https://example.com/article"))
    def test_extract_includes_readability(self, mock_fetch, mock_extract, mock_set, mock_get):
        response = client.post("/api/v1/extract", json={"url": "https://example.com/article"})
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["readability"] is not None
        assert data["readability"]["flesch_reading_ease"] == 45.0
        assert data["readability"]["reading_level"] == "Difficult (College)"
        assert data["readability"]["reading_time_minutes"] == 0.3

    @patch("app.routes.v1.cache.get_cached", new_callable=AsyncMock, return_value=None)
    @patch("app.routes.v1.cache.set_cached", new_callable=AsyncMock)
    @patch("app.routes.v1.scraper.extract_content", return_value=MOCK_CONTENT_WITH_MARKDOWN)
    @patch("app.routes.v1.scraper.fetch_html", new_callable=AsyncMock, return_value=("<html></html>", "https://example.com/article"))
    def test_extract_markdown_output(self, mock_fetch, mock_extract, mock_set, mock_get):
        response = client.post(
            "/api/v1/extract",
            json={"url": "https://example.com/article", "output_format": "markdown"},
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["markdown"] is not None
        assert "# Test Article" in data["markdown"]

    @patch("app.routes.v1.cache.get_cached", new_callable=AsyncMock, return_value=None)
    @patch("app.routes.v1.cache.set_cached", new_callable=AsyncMock)
    @patch("app.routes.v1.scraper.extract_content", return_value=MOCK_CONTENT)
    @patch("app.routes.v1.scraper.fetch_html", new_callable=AsyncMock, return_value=("<html></html>", "https://example.com/article"))
    def test_extract_text_mode_no_markdown(self, mock_fetch, mock_extract, mock_set, mock_get):
        response = client.post(
            "/api/v1/extract",
            json={"url": "https://example.com/article", "output_format": "text"},
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["markdown"] is None

    @patch("app.routes.v1.cache.get_cached", new_callable=AsyncMock, return_value=None)
    @patch("app.routes.v1.cache.set_cached", new_callable=AsyncMock)
    @patch("app.routes.v1.scraper.extract_content", return_value=MOCK_CONTENT)
    @patch("app.routes.v1.scraper.fetch_html", new_callable=AsyncMock, return_value=("<html></html>", "https://example.com/article"))
    def test_extract_cache_key_includes_format(self, mock_fetch, mock_extract, mock_set, mock_get):
        """Cache key should differ by output_format."""
        client.post("/api/v1/extract", json={"url": "https://example.com/article", "output_format": "markdown"})
        cache_key = mock_get.call_args[0][1]
        assert "markdown" in cache_key


# ──────────────────────────────────────────────
# /api/v1/analyze — keywords + quality score
# ──────────────────────────────────────────────


class TestAnalyzeNewFeatures:
    """Tests for keywords and quality scoring in /analyze."""

    @patch("app.routes.v1.cache.get_cached", new_callable=AsyncMock, return_value=None)
    @patch("app.routes.v1.cache.set_cached", new_callable=AsyncMock)
    @patch("app.routes.v1.ai_service.extract_keywords", new_callable=AsyncMock, return_value=MOCK_KEYWORDS)
    @patch("app.routes.v1.ai_service.analyze_sentiment", new_callable=AsyncMock, return_value=MOCK_SENTIMENT)
    @patch("app.routes.v1.ai_service.summarize_text", new_callable=AsyncMock, return_value=MOCK_SUMMARY)
    @patch("app.routes.v1.scraper.extract_seo_metadata", return_value=MOCK_SEO)
    @patch("app.routes.v1.scraper.extract_content", return_value=MOCK_CONTENT)
    @patch("app.routes.v1.scraper.fetch_html", new_callable=AsyncMock, return_value=("<html></html>", "https://example.com/article"))
    def test_analyze_includes_keywords(self, mock_fetch, mock_extract, mock_seo, mock_summ, mock_sent, mock_kw, mock_set, mock_get):
        response = client.post("/api/v1/analyze", json={"url": "https://example.com/article"})
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["keywords"] is not None
        assert "artificial intelligence" in data["keywords"]["keywords"]
        assert len(data["keywords"]["topics"]) > 0
        assert data["keywords"]["category"] == "technology"

    @patch("app.routes.v1.cache.get_cached", new_callable=AsyncMock, return_value=None)
    @patch("app.routes.v1.cache.set_cached", new_callable=AsyncMock)
    @patch("app.routes.v1.ai_service.extract_keywords", new_callable=AsyncMock, return_value=MOCK_KEYWORDS)
    @patch("app.routes.v1.ai_service.analyze_sentiment", new_callable=AsyncMock, return_value=MOCK_SENTIMENT)
    @patch("app.routes.v1.ai_service.summarize_text", new_callable=AsyncMock, return_value=MOCK_SUMMARY)
    @patch("app.routes.v1.scraper.extract_seo_metadata", return_value=MOCK_SEO)
    @patch("app.routes.v1.scraper.extract_content", return_value=MOCK_CONTENT)
    @patch("app.routes.v1.scraper.fetch_html", new_callable=AsyncMock, return_value=("<html></html>", "https://example.com/article"))
    def test_analyze_includes_quality_score(self, mock_fetch, mock_extract, mock_seo, mock_summ, mock_sent, mock_kw, mock_set, mock_get):
        response = client.post("/api/v1/analyze", json={"url": "https://example.com/article"})
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["quality"] is not None
        assert "total_score" in data["quality"]
        assert "grade" in data["quality"]
        assert "breakdown" in data["quality"]
        assert "recommendations" in data["quality"]

    @patch("app.routes.v1.cache.get_cached", new_callable=AsyncMock, return_value=None)
    @patch("app.routes.v1.cache.set_cached", new_callable=AsyncMock)
    @patch("app.routes.v1.ai_service.extract_keywords", new_callable=AsyncMock, return_value=MOCK_KEYWORDS)
    @patch("app.routes.v1.ai_service.analyze_sentiment", new_callable=AsyncMock, return_value=MOCK_SENTIMENT)
    @patch("app.routes.v1.ai_service.summarize_text", new_callable=AsyncMock, return_value=MOCK_SUMMARY)
    @patch("app.routes.v1.scraper.extract_seo_metadata", return_value=MOCK_SEO)
    @patch("app.routes.v1.scraper.extract_content", return_value=MOCK_CONTENT)
    @patch("app.routes.v1.scraper.fetch_html", new_callable=AsyncMock, return_value=("<html></html>", "https://example.com/article"))
    def test_analyze_keywords_has_entities(self, mock_fetch, mock_extract, mock_seo, mock_summ, mock_sent, mock_kw, mock_set, mock_get):
        response = client.post("/api/v1/analyze", json={"url": "https://example.com/article"})
        data = response.json()["data"]
        entities = data["keywords"]["entities"]
        assert len(entities) > 0
        assert entities[0]["name"] == "AI"
        assert entities[0]["type"] == "PRODUCT"


# ──────────────────────────────────────────────
# /api/v1/compare — new endpoint
# ──────────────────────────────────────────────


MOCK_CONTENT_2 = ExtractedContent(
    url="https://example.com/article-2",
    title="Second Article",
    text=(
        "Cooking is a wonderful activity that brings people together. "
        "Recipes from around the world showcase diverse culinary traditions. "
        "Fresh ingredients are essential for creating delicious and healthy meals. "
        "The kitchen is where creativity meets nutrition and produces amazing results. "
        "Learning to cook well is a lifelong journey of flavors and techniques."
    ),
    word_count=55,
    excerpt="Cooking is a wonderful activity...",
    language="en",
    extraction_time_ms=100,
)


class TestCompareEndpoint:
    """Tests for /api/v1/compare endpoint."""

    @patch("app.routes.v1.cache.get_cached", new_callable=AsyncMock, return_value=None)
    @patch("app.routes.v1.cache.set_cached", new_callable=AsyncMock)
    @patch("app.routes.v1.scraper.extract_content")
    @patch("app.routes.v1.scraper.fetch_html", new_callable=AsyncMock)
    def test_compare_success(self, mock_fetch, mock_extract, mock_set, mock_get):
        mock_fetch.side_effect = [
            ("<html>1</html>", "https://example.com/article"),
            ("<html>2</html>", "https://example.com/article-2"),
        ]
        mock_extract.side_effect = [MOCK_CONTENT, MOCK_CONTENT_2]

        response = client.post("/api/v1/compare", json={
            "url1": "https://example.com/article",
            "url2": "https://example.com/article-2",
        })
        assert response.status_code == 200
        data = response.json()["data"]
        assert "similarity_score" in data
        assert 0 <= data["similarity_score"] <= 1
        assert isinstance(data["shared_keywords"], list)
        assert isinstance(data["unique_to_url1"], list)
        assert isinstance(data["unique_to_url2"], list)

    @patch("app.routes.v1.cache.get_cached", new_callable=AsyncMock, return_value=None)
    @patch("app.routes.v1.cache.set_cached", new_callable=AsyncMock)
    @patch("app.routes.v1.scraper.extract_content")
    @patch("app.routes.v1.scraper.fetch_html", new_callable=AsyncMock)
    def test_compare_word_count_diff(self, mock_fetch, mock_extract, mock_set, mock_get):
        mock_fetch.side_effect = [
            ("<html>1</html>", "https://example.com/article"),
            ("<html>2</html>", "https://example.com/article-2"),
        ]
        mock_extract.side_effect = [MOCK_CONTENT, MOCK_CONTENT_2]

        response = client.post("/api/v1/compare", json={
            "url1": "https://example.com/article",
            "url2": "https://example.com/article-2",
        })
        data = response.json()["data"]
        assert data["word_count_diff"] == MOCK_CONTENT.word_count - MOCK_CONTENT_2.word_count

    @patch("app.routes.v1.cache.get_cached", new_callable=AsyncMock, return_value=None)
    @patch("app.routes.v1.cache.set_cached", new_callable=AsyncMock)
    @patch("app.routes.v1.scraper.extract_content")
    @patch("app.routes.v1.scraper.fetch_html", new_callable=AsyncMock)
    def test_compare_readability_diff(self, mock_fetch, mock_extract, mock_set, mock_get):
        mock_fetch.side_effect = [
            ("<html>1</html>", "https://example.com/article"),
            ("<html>2</html>", "https://example.com/article-2"),
        ]
        mock_extract.side_effect = [MOCK_CONTENT, MOCK_CONTENT_2]

        response = client.post("/api/v1/compare", json={
            "url1": "https://example.com/article",
            "url2": "https://example.com/article-2",
        })
        data = response.json()["data"]
        # Both texts have enough words so readability_diff should be populated
        assert "readability_diff" in data

    @patch("app.routes.v1.cache.get_cached", new_callable=AsyncMock, return_value=None)
    @patch("app.routes.v1.scraper.extract_content")
    @patch("app.routes.v1.scraper.fetch_html", new_callable=AsyncMock)
    def test_compare_empty_content_422(self, mock_fetch, mock_extract, mock_get):
        empty_content = ExtractedContent(
            url="https://example.com/empty",
            text="",
            word_count=0,
            extraction_time_ms=50,
        )
        mock_fetch.side_effect = [
            ("<html>1</html>", "https://example.com/article"),
            ("<html>2</html>", "https://example.com/empty"),
        ]
        mock_extract.side_effect = [MOCK_CONTENT, empty_content]

        response = client.post("/api/v1/compare", json={
            "url1": "https://example.com/article",
            "url2": "https://example.com/empty",
        })
        assert response.status_code == 422

    @patch("app.routes.v1.cache.get_cached", new_callable=AsyncMock)
    def test_compare_cached(self, mock_get):
        cached_data = {
            "url1": "https://example.com/a",
            "url2": "https://example.com/b",
            "similarity_score": 0.75,
            "shared_keywords": ["test"],
            "unique_to_url1": [],
            "unique_to_url2": [],
            "word_count_diff": 10,
            "readability_diff": {},
            "processing_time_ms": 200,
        }
        mock_get.return_value = cached_data

        response = client.post("/api/v1/compare", json={
            "url1": "https://example.com/a",
            "url2": "https://example.com/b",
        })
        assert response.status_code == 200
        assert response.json()["cached"] is True

    def test_compare_invalid_url(self):
        response = client.post("/api/v1/compare", json={
            "url1": "not-a-url",
            "url2": "https://example.com/b",
        })
        assert response.status_code == 422

    @patch("app.routes.v1.cache.get_cached", new_callable=AsyncMock, return_value=None)
    @patch("app.routes.v1.cache.set_cached", new_callable=AsyncMock)
    @patch("app.routes.v1.scraper.extract_content")
    @patch("app.routes.v1.scraper.fetch_html", new_callable=AsyncMock)
    def test_compare_identical_urls(self, mock_fetch, mock_extract, mock_set, mock_get):
        """Comparing the same content should give similarity close to 1."""
        mock_fetch.side_effect = [
            ("<html>1</html>", "https://example.com/article"),
            ("<html>2</html>", "https://example.com/article"),
        ]
        mock_extract.side_effect = [MOCK_CONTENT, MOCK_CONTENT]

        response = client.post("/api/v1/compare", json={
            "url1": "https://example.com/article",
            "url2": "https://example.com/article",
        })
        assert response.status_code == 200
        assert response.json()["data"]["similarity_score"] == 1.0
