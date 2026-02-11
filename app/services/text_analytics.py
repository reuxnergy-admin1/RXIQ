"""Text analytics — readability scores, reading time, vocabulary metrics.

All computation is local (no API calls), so these features are
zero marginal cost — pure profit on every request.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass


def _count_syllables(word: str) -> int:
    """Estimate syllable count using a simple heuristic."""
    word = word.lower().strip()
    if not word:
        return 0
    if len(word) <= 3:
        return 1

    # Remove trailing silent e
    word = re.sub(r"e$", "", word)

    # Count vowel groups
    vowel_groups = re.findall(r"[aeiouy]+", word)
    count = len(vowel_groups)

    return max(1, count)


def _count_sentences(text: str) -> int:
    """Count sentences using punctuation boundaries."""
    sentences = re.split(r"[.!?]+", text)
    return len([s for s in sentences if s.strip()])


def _get_words(text: str) -> list[str]:
    """Extract clean word list from text."""
    return [w for w in re.findall(r"[a-zA-Z]+", text) if len(w) > 0]


@dataclass
class ReadabilityScores:
    """Collection of readability metrics."""

    flesch_reading_ease: float  # 0-100, higher = easier
    flesch_kincaid_grade: float  # US grade level
    coleman_liau_index: float  # US grade level
    automated_readability_index: float  # US grade level
    avg_grade_level: float  # Average of all grade metrics
    reading_level: str  # Human-readable label

    # Text statistics
    sentence_count: int
    word_count: int
    syllable_count: int
    char_count: int
    avg_sentence_length: float  # words per sentence
    avg_word_length: float  # chars per word
    avg_syllables_per_word: float

    # Vocabulary
    unique_words: int
    vocabulary_density: float  # unique/total (0-1)
    complex_word_count: int  # words with 3+ syllables
    complex_word_pct: float  # percentage of complex words

    # Reading time
    reading_time_seconds: int
    reading_time_minutes: float


def _reading_level_label(score: float) -> str:
    """Convert Flesch Reading Ease score to a human-readable label."""
    if score >= 90:
        return "Very Easy (5th grade)"
    elif score >= 80:
        return "Easy (6th grade)"
    elif score >= 70:
        return "Fairly Easy (7th grade)"
    elif score >= 60:
        return "Standard (8th-9th grade)"
    elif score >= 50:
        return "Fairly Difficult (10th-12th grade)"
    elif score >= 30:
        return "Difficult (College)"
    else:
        return "Very Difficult (Graduate)"


def compute_readability(text: str) -> ReadabilityScores:
    """Compute comprehensive readability metrics for a text.

    Returns zero-value scores for very short texts (< 2 sentences).
    """
    words = _get_words(text)
    word_count = len(words)
    sentence_count = max(_count_sentences(text), 1)
    char_count = sum(len(w) for w in words)
    syllable_count = sum(_count_syllables(w) for w in words)

    # Avoid division by zero
    if word_count < 10:
        return ReadabilityScores(
            flesch_reading_ease=0,
            flesch_kincaid_grade=0,
            coleman_liau_index=0,
            automated_readability_index=0,
            avg_grade_level=0,
            reading_level="Too short to analyze",
            sentence_count=sentence_count,
            word_count=word_count,
            syllable_count=syllable_count,
            char_count=char_count,
            avg_sentence_length=0,
            avg_word_length=0,
            avg_syllables_per_word=0,
            unique_words=len(set(w.lower() for w in words)),
            vocabulary_density=0,
            complex_word_count=0,
            complex_word_pct=0,
            reading_time_seconds=0,
            reading_time_minutes=0,
        )

    asl = word_count / sentence_count  # avg sentence length
    asw = syllable_count / word_count  # avg syllables per word
    awl = char_count / word_count  # avg word length (chars)

    # Flesch Reading Ease
    fre = 206.835 - (1.015 * asl) - (84.6 * asw)
    fre = max(0, min(100, round(fre, 1)))

    # Flesch-Kincaid Grade Level
    fkgl = (0.39 * asl) + (11.8 * asw) - 15.59
    fkgl = max(0, round(fkgl, 1))

    # Coleman-Liau Index
    # L = avg letters per 100 words, S = avg sentences per 100 words
    L = (char_count / word_count) * 100
    S = (sentence_count / word_count) * 100
    cli = (0.0588 * L) - (0.296 * S) - 15.8
    cli = max(0, round(cli, 1))

    # Automated Readability Index
    ari = (4.71 * awl) + (0.5 * asl) - 21.43
    ari = max(0, round(ari, 1))

    # Average grade level
    avg_grade = round((fkgl + cli + ari) / 3, 1)

    # Vocabulary metrics
    unique_words = len(set(w.lower() for w in words))
    vocabulary_density = round(unique_words / word_count, 3) if word_count > 0 else 0

    complex_words = [w for w in words if _count_syllables(w) >= 3]
    complex_word_count = len(complex_words)
    complex_word_pct = round((complex_word_count / word_count) * 100, 1)

    # Reading time (avg 238 words/minute for adults reading online)
    reading_time_seconds = round((word_count / 238) * 60)
    reading_time_minutes = round(word_count / 238, 1)

    return ReadabilityScores(
        flesch_reading_ease=fre,
        flesch_kincaid_grade=fkgl,
        coleman_liau_index=cli,
        automated_readability_index=ari,
        avg_grade_level=avg_grade,
        reading_level=_reading_level_label(fre),
        sentence_count=sentence_count,
        word_count=word_count,
        syllable_count=syllable_count,
        char_count=char_count,
        avg_sentence_length=round(asl, 1),
        avg_word_length=round(awl, 1),
        avg_syllables_per_word=round(asw, 2),
        unique_words=unique_words,
        vocabulary_density=vocabulary_density,
        complex_word_count=complex_word_count,
        complex_word_pct=complex_word_pct,
        reading_time_seconds=reading_time_seconds,
        reading_time_minutes=reading_time_minutes,
    )


def compute_content_quality_score(
    word_count: int,
    sentence_count: int,
    flesch_reading_ease: float,
    h1_count: int,
    h2_count: int,
    total_images: int,
    images_without_alt: int,
    internal_links: int,
    external_links: int,
    has_meta_description: bool,
    has_canonical: bool,
    has_open_graph: bool,
    has_schema_markup: bool,
) -> dict:
    """Compute a composite content quality score (0-100).

    Scoring breakdown:
    - Content depth (30 pts): word count, sentence variety
    - Readability (20 pts): Flesch score in optimal range
    - Structure (20 pts): headings, proper hierarchy
    - Media (15 pts): images with alt text
    - SEO signals (15 pts): meta, canonical, OG, schema

    Returns dict with total score, breakdown, and recommendations.
    """
    scores: dict[str, float] = {}
    recommendations: list[str] = []

    # --- Content Depth (30 pts) ---
    if word_count >= 2000:
        depth = 30
    elif word_count >= 1000:
        depth = 25
    elif word_count >= 500:
        depth = 20
    elif word_count >= 300:
        depth = 15
    elif word_count >= 100:
        depth = 8
    else:
        depth = 3
        recommendations.append("Content is very thin. Aim for 500+ words for better engagement.")

    if word_count < 300:
        recommendations.append("Articles under 300 words typically rank poorly in search engines.")
    scores["content_depth"] = depth

    # --- Readability (20 pts) ---
    # Optimal Flesch score is 60-70 (standard readability)
    if 50 <= flesch_reading_ease <= 80:
        readability = 20
    elif 40 <= flesch_reading_ease <= 90:
        readability = 15
    elif 30 <= flesch_reading_ease:
        readability = 10
    else:
        readability = 5
        recommendations.append("Content is very difficult to read. Simplify sentences and vocabulary.")

    if flesch_reading_ease > 90:
        readability = 12
        recommendations.append("Content may be too simplistic for a professional audience.")
    scores["readability"] = readability

    # --- Structure (20 pts) ---
    structure = 0
    if h1_count == 1:
        structure += 8
    elif h1_count > 1:
        structure += 4
        recommendations.append("Multiple H1 tags detected. Use exactly one H1 per page.")
    else:
        recommendations.append("Missing H1 tag. Every page should have a single H1 heading.")

    if h2_count >= 2:
        structure += 8
    elif h2_count == 1:
        structure += 5
    else:
        recommendations.append("Add H2 subheadings to break up content and improve scannability.")

    if sentence_count >= 5:
        structure += 4
    else:
        structure += 2
    scores["structure"] = structure

    # --- Media (15 pts) ---
    media = 0
    if total_images > 0:
        media += 8
        images_with_alt = total_images - images_without_alt
        alt_ratio = images_with_alt / total_images
        media += round(7 * alt_ratio)
        if images_without_alt > 0:
            recommendations.append(
                f"{images_without_alt} image(s) missing alt text. Add descriptive alt attributes."
            )
    else:
        recommendations.append("No images found. Adding relevant images improves engagement and SEO.")
    scores["media"] = media

    # --- SEO Signals (15 pts) ---
    seo = 0
    if has_meta_description:
        seo += 5
    else:
        recommendations.append("Missing meta description. Add one for better search engine snippets.")
    if has_canonical:
        seo += 3
    if has_open_graph:
        seo += 4
    else:
        recommendations.append("Missing Open Graph tags. Add them for better social media sharing.")
    if has_schema_markup:
        seo += 3
    else:
        recommendations.append("No Schema.org markup found. Add structured data for rich search results.")
    scores["seo_signals"] = seo

    total = sum(scores.values())

    # Grade label
    if total >= 90:
        grade = "A+"
    elif total >= 80:
        grade = "A"
    elif total >= 70:
        grade = "B"
    elif total >= 60:
        grade = "C"
    elif total >= 50:
        grade = "D"
    else:
        grade = "F"

    return {
        "total_score": round(total),
        "grade": grade,
        "breakdown": {k: round(v) for k, v in scores.items()},
        "max_scores": {
            "content_depth": 30,
            "readability": 20,
            "structure": 20,
            "media": 15,
            "seo_signals": 15,
        },
        "recommendations": recommendations[:8],  # Limit to top 8
    }


# ──────────────────────────────────────────────────────────
# Content Comparison
# ──────────────────────────────────────────────────────────


def compute_similarity(text1: str, text2: str) -> dict:
    """Compute cosine similarity and keyword overlap between two texts.

    Uses TF-based cosine similarity (no external ML model needed).
    Returns similarity score 0-1 plus keyword analysis.
    """
    words1 = _get_words(text1)
    words2 = _get_words(text2)

    if not words1 or not words2:
        return {
            "similarity_score": 0.0,
            "shared_keywords": [],
            "unique_to_text1": [],
            "unique_to_text2": [],
        }

    # Build term-frequency vectors
    from collections import Counter

    freq1 = Counter(words1)
    freq2 = Counter(words2)

    # All unique terms
    all_terms = set(freq1.keys()) | set(freq2.keys())

    # Cosine similarity
    dot_product = sum(freq1.get(t, 0) * freq2.get(t, 0) for t in all_terms)
    mag1 = math.sqrt(sum(v ** 2 for v in freq1.values()))
    mag2 = math.sqrt(sum(v ** 2 for v in freq2.values()))

    similarity = dot_product / (mag1 * mag2) if mag1 and mag2 else 0.0

    # Top keywords per text (by frequency, filter stopwords)
    stopwords = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "shall", "can", "to", "of", "in", "for",
        "on", "with", "at", "by", "from", "as", "into", "through", "during",
        "before", "after", "above", "below", "between", "out", "off", "over",
        "under", "again", "further", "then", "once", "that", "this", "these",
        "those", "it", "its", "he", "she", "they", "them", "his", "her",
        "their", "my", "your", "our", "who", "which", "what", "where", "when",
        "how", "all", "each", "every", "both", "few", "more", "most", "other",
        "some", "such", "no", "not", "only", "than", "too", "very", "just",
        "but", "and", "or", "if", "so", "about", "up", "also", "well",
    }

    def top_keywords(freq: Counter, n: int = 20) -> list[str]:
        return [
            w for w, _ in freq.most_common(n * 3)
            if w not in stopwords and len(w) > 2
        ][:n]

    kw1 = set(top_keywords(freq1))
    kw2 = set(top_keywords(freq2))

    shared = sorted(kw1 & kw2)
    unique1 = sorted(kw1 - kw2)
    unique2 = sorted(kw2 - kw1)

    return {
        "similarity_score": round(similarity, 4),
        "shared_keywords": shared[:20],
        "unique_to_text1": unique1[:20],
        "unique_to_text2": unique2[:20],
    }
