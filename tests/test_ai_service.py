"""Tests for the AI service module with mocked OpenAI client."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models import SentimentLabel, SummaryFormat


@pytest.fixture(autouse=True)
def reset_ai_client():
    """Reset the lazy-initialized OpenAI client between tests."""
    import app.services.ai_service as ai_svc

    ai_svc._client = None
    yield
    ai_svc._client = None


def _mock_openai_response(content: str):
    """Create a mock OpenAI chat completion response."""
    message = MagicMock()
    message.content = content
    choice = MagicMock()
    choice.message = message
    response = MagicMock()
    response.choices = [choice]
    return response


class TestSummarizeText:
    """Tests for summarize_text with mocked OpenAI."""

    @pytest.mark.asyncio
    @patch("app.services.ai_service._get_client")
    async def test_summarize_tldr(self, mock_get_client):
        client_mock = MagicMock()
        client_mock.chat.completions.create = AsyncMock(
            return_value=_mock_openai_response("This is a TL;DR summary.")
        )
        mock_get_client.return_value = client_mock

        from app.services.ai_service import summarize_text

        result = await summarize_text(
            text="Some long text " * 50,
            format=SummaryFormat.tldr,
            max_length=100,
        )

        assert result.summary == "This is a TL;DR summary."
        assert result.format == SummaryFormat.tldr
        assert result.model_used == "gpt-4o-mini"
        assert result.processing_time_ms >= 0
        assert result.word_count > 0

    @pytest.mark.asyncio
    @patch("app.services.ai_service._get_client")
    async def test_summarize_bullets(self, mock_get_client):
        client_mock = MagicMock()
        client_mock.chat.completions.create = AsyncMock(
            return_value=_mock_openai_response("- Point 1\n- Point 2\n- Point 3")
        )
        mock_get_client.return_value = client_mock

        from app.services.ai_service import summarize_text

        result = await summarize_text(
            text="Detailed content " * 50,
            format=SummaryFormat.bullets,
            max_length=200,
        )

        assert "Point 1" in result.summary
        assert result.format == SummaryFormat.bullets

    @pytest.mark.asyncio
    @patch("app.services.ai_service._get_client")
    async def test_summarize_with_language(self, mock_get_client):
        client_mock = MagicMock()
        client_mock.chat.completions.create = AsyncMock(
            return_value=_mock_openai_response("Un résumé en français.")
        )
        mock_get_client.return_value = client_mock

        from app.services.ai_service import summarize_text

        result = await summarize_text(
            text="English text here",
            format=SummaryFormat.paragraph,
            language="fr",
        )

        assert result.language == "fr"
        # Verify the system prompt included language instruction
        call_args = client_mock.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]
        system_msg = messages[0]["content"]
        assert "fr" in system_msg

    @pytest.mark.asyncio
    @patch("app.services.ai_service._get_client")
    async def test_summarize_with_source_url(self, mock_get_client):
        client_mock = MagicMock()
        client_mock.chat.completions.create = AsyncMock(
            return_value=_mock_openai_response("Summary content.")
        )
        mock_get_client.return_value = client_mock

        from app.services.ai_service import summarize_text

        result = await summarize_text(
            text="Article text",
            source_url="https://example.com/article",
        )

        assert result.original_url == "https://example.com/article"

    @pytest.mark.asyncio
    @patch("app.services.ai_service._get_client")
    async def test_summarize_counts_words(self, mock_get_client):
        client_mock = MagicMock()
        client_mock.chat.completions.create = AsyncMock(
            return_value=_mock_openai_response("One two three four five")
        )
        mock_get_client.return_value = client_mock

        from app.services.ai_service import summarize_text

        result = await summarize_text(text="Long input text " * 100)

        assert result.word_count == 5
        assert result.original_word_count > 0


class TestAnalyzeSentiment:
    """Tests for analyze_sentiment with mocked OpenAI."""

    @pytest.mark.asyncio
    @patch("app.services.ai_service._get_client")
    async def test_sentiment_positive(self, mock_get_client):
        sentiment_json = json.dumps(
            {
                "sentiment": "positive",
                "confidence": 0.95,
                "scores": {"positive": 0.95, "negative": 0.02, "neutral": 0.03},
                "key_phrases": ["absolutely amazing", "best ever"],
            }
        )
        client_mock = MagicMock()
        client_mock.chat.completions.create = AsyncMock(
            return_value=_mock_openai_response(sentiment_json)
        )
        mock_get_client.return_value = client_mock

        from app.services.ai_service import analyze_sentiment

        result = await analyze_sentiment(text="This is absolutely amazing! Best ever!")

        assert result.sentiment == SentimentLabel.positive
        assert result.confidence == 0.95
        assert result.scores["positive"] == 0.95
        assert len(result.key_phrases) == 2

    @pytest.mark.asyncio
    @patch("app.services.ai_service._get_client")
    async def test_sentiment_negative(self, mock_get_client):
        sentiment_json = json.dumps(
            {
                "sentiment": "negative",
                "confidence": 0.88,
                "scores": {"positive": 0.05, "negative": 0.88, "neutral": 0.07},
                "key_phrases": ["terrible", "worst"],
            }
        )
        client_mock = MagicMock()
        client_mock.chat.completions.create = AsyncMock(
            return_value=_mock_openai_response(sentiment_json)
        )
        mock_get_client.return_value = client_mock

        from app.services.ai_service import analyze_sentiment

        result = await analyze_sentiment(text="Terrible product. Worst ever.")

        assert result.sentiment == SentimentLabel.negative
        assert result.confidence == 0.88

    @pytest.mark.asyncio
    @patch("app.services.ai_service._get_client")
    async def test_sentiment_invalid_json_fallback(self, mock_get_client):
        """When OpenAI returns invalid JSON, should use fallback values."""
        client_mock = MagicMock()
        client_mock.chat.completions.create = AsyncMock(
            return_value=_mock_openai_response("NOT VALID JSON {{{")
        )
        mock_get_client.return_value = client_mock

        from app.services.ai_service import analyze_sentiment

        result = await analyze_sentiment(text="Ambiguous text")

        assert result.sentiment == SentimentLabel.neutral
        assert result.confidence == 0.5

    @pytest.mark.asyncio
    @patch("app.services.ai_service._get_client")
    async def test_sentiment_unknown_label_fallback(self, mock_get_client):
        """When sentiment label is unrecognized, should default to neutral."""
        sentiment_json = json.dumps(
            {
                "sentiment": "confused",  # Not a valid label
                "confidence": 0.7,
                "scores": {"positive": 0.3, "negative": 0.3, "neutral": 0.4},
                "key_phrases": [],
            }
        )
        client_mock = MagicMock()
        client_mock.chat.completions.create = AsyncMock(
            return_value=_mock_openai_response(sentiment_json)
        )
        mock_get_client.return_value = client_mock

        from app.services.ai_service import analyze_sentiment

        result = await analyze_sentiment(text="Confusing text")

        assert result.sentiment == SentimentLabel.neutral

    @pytest.mark.asyncio
    @patch("app.services.ai_service._get_client")
    async def test_sentiment_with_source_url(self, mock_get_client):
        sentiment_json = json.dumps(
            {
                "sentiment": "neutral",
                "confidence": 0.6,
                "scores": {"positive": 0.3, "negative": 0.1, "neutral": 0.6},
                "key_phrases": ["factual information"],
            }
        )
        client_mock = MagicMock()
        client_mock.chat.completions.create = AsyncMock(
            return_value=_mock_openai_response(sentiment_json)
        )
        mock_get_client.return_value = client_mock

        from app.services.ai_service import analyze_sentiment

        result = await analyze_sentiment(
            text="Factual information here",
            source_url="https://example.com/news",
        )

        assert result.original_url == "https://example.com/news"
        assert result.model_used == "gpt-4o-mini"
        assert result.processing_time_ms >= 0

    @pytest.mark.asyncio
    @patch("app.services.ai_service._get_client")
    async def test_sentiment_confidence_clamped(self, mock_get_client):
        """Confidence values outside 0-1 range should be clamped."""
        sentiment_json = json.dumps(
            {
                "sentiment": "positive",
                "confidence": 1.5,  # Out of range
                "scores": {"positive": 0.9, "negative": 0.05, "neutral": 0.05},
                "key_phrases": [],
            }
        )
        client_mock = MagicMock()
        client_mock.chat.completions.create = AsyncMock(
            return_value=_mock_openai_response(sentiment_json)
        )
        mock_get_client.return_value = client_mock

        from app.services.ai_service import analyze_sentiment

        result = await analyze_sentiment(text="Over-confident text")

        assert result.confidence <= 1.0


class TestPricing:
    """Tests for the pricing module."""

    def test_get_tier_info_known_tier(self):
        from app.pricing import get_tier_info

        info = get_tier_info("pro")
        assert info["name"] == "Pro"
        assert info["price_monthly"] == 29.99
        assert info["calls_per_month"] == 15000

    def test_get_tier_info_unknown_falls_back_to_free(self):
        from app.pricing import get_tier_info

        info = get_tier_info("nonexistent")
        assert info["name"] == "Basic (Free)"
        assert info["price_monthly"] == 0

    def test_get_all_tiers(self):
        from app.pricing import get_all_tiers

        tiers = get_all_tiers()
        assert len(tiers) == 5
        assert "free" in tiers
        assert "starter" in tiers
        assert "pro" in tiers
        assert "business" in tiers
        assert "enterprise" in tiers

    def test_free_tier_limited_endpoints(self):
        from app.pricing import get_tier_info

        free = get_tier_info("free")
        assert free["endpoints"] == ["extract"]

    def test_paid_tiers_have_all_endpoints(self):
        from app.pricing import get_tier_info

        for tier in ["starter", "pro", "business", "enterprise"]:
            info = get_tier_info(tier)
            assert "extract" in info["endpoints"]
            assert "summarize" in info["endpoints"]
            assert "sentiment" in info["endpoints"]
            assert "seo" in info["endpoints"]
            assert "analyze" in info["endpoints"]
