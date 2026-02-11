"""Tests for app.services.text_analytics module."""

from __future__ import annotations

import pytest

from app.services.text_analytics import (
    _count_sentences,
    _count_syllables,
    _get_words,
    compute_content_quality_score,
    compute_readability,
    compute_similarity,
)

# ──────────────────────────────────────────────
# Helper functions
# ──────────────────────────────────────────────


class TestCountSyllables:
    def test_one_syllable(self):
        assert _count_syllables("the") == 1
        assert _count_syllables("cat") == 1

    def test_two_syllables(self):
        assert _count_syllables("hello") == 2

    def test_three_syllables(self):
        assert _count_syllables("beautiful") == 3

    def test_empty(self):
        assert _count_syllables("") == 0

    def test_short_word(self):
        assert _count_syllables("it") == 1
        assert _count_syllables("a") == 1


class TestCountSentences:
    def test_single(self):
        assert _count_sentences("Hello world.") == 1

    def test_multiple(self):
        assert _count_sentences("Hello. World! How?") == 3

    def test_empty(self):
        assert _count_sentences("") == 0


class TestGetWords:
    def test_basic(self):
        words = _get_words("Hello world, how are you?")
        assert "Hello" in words
        assert "world" in words
        assert len(words) == 5

    def test_empty(self):
        assert _get_words("") == []


# ──────────────────────────────────────────────
# Readability scoring
# ──────────────────────────────────────────────


SAMPLE_TEXT = (
    "Artificial intelligence has transformed the technology landscape dramatically. "
    "Machine learning algorithms now power everything from search engines to self-driving cars. "
    "Natural language processing enables computers to understand and generate human text. "
    "Deep learning neural networks can recognize images and speech with remarkable accuracy. "
    "The rapid growth of AI has raised important ethical questions about privacy and bias. "
    "Researchers continue to push boundaries in developing more capable and aligned systems. "
    "The economic impact of AI is estimated to be trillions of dollars in the coming decade. "
    "Education and healthcare sectors are seeing particularly transformative applications. "
    "Governments worldwide are establishing regulatory frameworks for AI development. "
    "The future promises even more sophisticated and beneficial AI technologies."
)


class TestComputeReadability:
    def test_returns_dataclass(self):
        result = compute_readability(SAMPLE_TEXT)
        assert hasattr(result, "flesch_reading_ease")
        assert hasattr(result, "reading_level")
        assert hasattr(result, "reading_time_minutes")

    def test_scores_range(self):
        result = compute_readability(SAMPLE_TEXT)
        assert 0 <= result.flesch_reading_ease <= 100
        assert result.flesch_kincaid_grade >= 0
        assert result.coleman_liau_index >= 0
        assert result.automated_readability_index >= 0

    def test_reading_level_label(self):
        result = compute_readability(SAMPLE_TEXT)
        assert result.reading_level != ""
        assert "grade" in result.reading_level.lower() or "college" in result.reading_level.lower() or "easy" in result.reading_level.lower() or "difficult" in result.reading_level.lower()

    def test_statistics(self):
        result = compute_readability(SAMPLE_TEXT)
        assert result.word_count > 0
        assert result.sentence_count > 0
        assert result.avg_sentence_length > 0
        assert result.unique_words > 0
        assert 0 < result.vocabulary_density <= 1

    def test_reading_time(self):
        result = compute_readability(SAMPLE_TEXT)
        assert result.reading_time_seconds > 0
        assert result.reading_time_minutes > 0

    def test_short_text_safe(self):
        result = compute_readability("Hi.")
        assert result.flesch_reading_ease == 0
        assert result.reading_level == "Too short to analyze"

    def test_complex_words(self):
        result = compute_readability(SAMPLE_TEXT)
        assert result.complex_word_count >= 0
        assert result.complex_word_pct >= 0


# ──────────────────────────────────────────────
# Content quality scoring
# ──────────────────────────────────────────────


class TestComputeContentQualityScore:
    def test_minimal_content(self):
        result = compute_content_quality_score(
            word_count=3, sentence_count=1, flesch_reading_ease=50,
            h1_count=0, h2_count=0, total_images=0, images_without_alt=0,
            internal_links=0, external_links=0,
            has_meta_description=False, has_canonical=False,
            has_open_graph=False, has_schema_markup=False,
        )
        assert "total_score" in result
        assert "grade" in result
        assert 0 <= result["total_score"] <= 100

    def test_good_content(self):
        result = compute_content_quality_score(
            word_count=len(SAMPLE_TEXT.split()),
            sentence_count=10,
            flesch_reading_ease=65.0,
            h1_count=1,
            h2_count=3,
            total_images=5,
            images_without_alt=0,
            internal_links=10,
            external_links=5,
            has_meta_description=True,
            has_canonical=True,
            has_open_graph=True,
            has_schema_markup=True,
        )
        assert result["total_score"] > 50
        assert result["grade"] in ("A+", "A", "A-", "B+", "B", "B-", "C+", "C")

    def test_breakdown_categories(self):
        result = compute_content_quality_score(
            word_count=100, sentence_count=5, flesch_reading_ease=60,
            h1_count=1, h2_count=2, total_images=1, images_without_alt=0,
            internal_links=3, external_links=1,
            has_meta_description=True, has_canonical=False,
            has_open_graph=False, has_schema_markup=False,
        )
        assert "breakdown" in result
        assert "content_depth" in result["breakdown"]
        assert "readability" in result["breakdown"]
        assert "structure" in result["breakdown"]

    def test_recommendations_list(self):
        # Bad content should produce recommendations
        result = compute_content_quality_score(
            word_count=1, sentence_count=1, flesch_reading_ease=20,
            h1_count=0, h2_count=0, total_images=0, images_without_alt=0,
            internal_links=0, external_links=0,
            has_meta_description=False, has_canonical=False,
            has_open_graph=False, has_schema_markup=False,
        )
        assert isinstance(result["recommendations"], list)

    def test_max_scores(self):
        result = compute_content_quality_score(
            word_count=100, sentence_count=5, flesch_reading_ease=60,
            h1_count=1, h2_count=2, total_images=0, images_without_alt=0,
            internal_links=0, external_links=0,
            has_meta_description=False, has_canonical=False,
            has_open_graph=False, has_schema_markup=False,
        )
        assert result["max_scores"]["content_depth"] == 30
        assert result["max_scores"]["readability"] == 20


# ──────────────────────────────────────────────
# Content comparison / similarity
# ──────────────────────────────────────────────


class TestComputeSimilarity:
    def test_identical_texts(self):
        result = compute_similarity(SAMPLE_TEXT, SAMPLE_TEXT)
        assert result["similarity_score"] == 1.0

    def test_different_texts(self):
        text2 = (
            "Cooking is a wonderful activity that brings people together. "
            "Recipes from around the world showcase diverse culinary traditions. "
            "Fresh ingredients are essential for creating delicious and healthy meals."
        )
        result = compute_similarity(SAMPLE_TEXT, text2)
        assert 0 <= result["similarity_score"] < 0.5

    def test_shared_keywords(self):
        text2 = (
            "Artificial intelligence is changing the world of technology. "
            "Machine learning and deep learning are subsets of AI. "
            "The future of AI is promising and full of possibilities."
        )
        result = compute_similarity(SAMPLE_TEXT, text2)
        assert len(result["shared_keywords"]) > 0

    def test_unique_keywords(self):
        text2 = "Cooking, recipes, ingredients, and delicious flavors make food wonderful."
        result = compute_similarity(SAMPLE_TEXT, text2)
        assert len(result["unique_to_text1"]) > 0
        assert len(result["unique_to_text2"]) > 0

    def test_empty_text(self):
        result = compute_similarity("", SAMPLE_TEXT)
        assert result["similarity_score"] == 0.0

    def test_return_structure(self):
        result = compute_similarity("hello world", "hello earth")
        assert "similarity_score" in result
        assert "shared_keywords" in result
        assert "unique_to_text1" in result
        assert "unique_to_text2" in result
