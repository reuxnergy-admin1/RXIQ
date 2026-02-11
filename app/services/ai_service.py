"""AI service for summarization and sentiment analysis using OpenAI."""

from __future__ import annotations

import json
import time
from typing import Optional

from openai import AsyncOpenAI

from app.config import get_settings
from app.models import SentimentData, SentimentLabel, SummaryData, SummaryFormat

settings = get_settings()

# Lazy-init client
_client: Optional[AsyncOpenAI] = None

MODEL = "gpt-4o-mini"


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _client


# ──────────────────────────────────────────────
# Summarization
# ──────────────────────────────────────────────

SUMMARY_PROMPTS = {
    SummaryFormat.tldr: (
        "Provide a concise TL;DR summary of the following text. "
        "Keep it to {max_length} words or fewer. Be direct and factual."
    ),
    SummaryFormat.bullets: (
        "Summarize the following text as a bullet-point list of the key points. "
        "Use 3-7 bullet points. Each bullet should be one clear sentence. "
        "Keep the total under {max_length} words."
    ),
    SummaryFormat.key_takeaways: (
        "Extract the key takeaways from the following text. "
        "Present them as numbered insights (3-7 items). "
        "Each takeaway should be actionable or informative. "
        "Keep the total under {max_length} words."
    ),
    SummaryFormat.paragraph: (
        "Write a clear, well-structured paragraph summarizing the following text. "
        "Keep it under {max_length} words. Maintain the original tone and key facts."
    ),
}


async def summarize_text(
    text: str,
    format: SummaryFormat = SummaryFormat.tldr,
    max_length: int = 200,
    language: str = "en",
    source_url: Optional[str] = None,
) -> SummaryData:
    """Generate an AI summary of the provided text."""
    start_time = time.time()
    client = _get_client()

    system_prompt = SUMMARY_PROMPTS[format].format(max_length=max_length)
    if language != "en":
        system_prompt += f"\n\nIMPORTANT: Write the summary in the language with ISO code '{language}'."

    # Truncate input to avoid token limits
    truncated_text = text[: settings.max_content_length]

    response = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": truncated_text},
        ],
        temperature=0.3,
        max_tokens=1000,
    )

    summary = response.choices[0].message.content or ""
    elapsed_ms = int((time.time() - start_time) * 1000)

    return SummaryData(
        original_url=source_url,
        format=format,
        summary=summary.strip(),
        word_count=len(summary.split()),
        original_word_count=len(text.split()),
        language=language,
        model_used=MODEL,
        processing_time_ms=elapsed_ms,
    )


# ──────────────────────────────────────────────
# Sentiment Analysis
# ──────────────────────────────────────────────

SENTIMENT_SYSTEM_PROMPT = """You are a sentiment analysis engine. Analyze the sentiment of the provided text and respond ONLY with a valid JSON object in this exact format:

{
  "sentiment": "positive" | "negative" | "neutral" | "mixed",
  "confidence": 0.0 to 1.0,
  "scores": {
    "positive": 0.0 to 1.0,
    "negative": 0.0 to 1.0,
    "neutral": 0.0 to 1.0
  },
  "key_phrases": ["phrase1", "phrase2", "phrase3"]
}

Rules:
- "sentiment" must be one of: positive, negative, neutral, mixed
- "confidence" is your confidence in the primary sentiment label
- "scores" must sum to approximately 1.0
- "key_phrases" should list 3-5 short phrases from the text that most influenced your analysis
- Return ONLY the JSON, no markdown, no explanation"""


async def analyze_sentiment(
    text: str,
    source_url: Optional[str] = None,
) -> SentimentData:
    """Analyze the sentiment of the provided text."""
    start_time = time.time()
    client = _get_client()

    # Truncate for sentiment (less text needed than summarization)
    truncated_text = text[:10000]

    response = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SENTIMENT_SYSTEM_PROMPT},
            {"role": "user", "content": truncated_text},
        ],
        temperature=0.1,
        max_tokens=500,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content or "{}"

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        result = {
            "sentiment": "neutral",
            "confidence": 0.5,
            "scores": {"positive": 0.33, "negative": 0.33, "neutral": 0.34},
            "key_phrases": [],
        }

    elapsed_ms = int((time.time() - start_time) * 1000)

    # Validate sentiment label
    sentiment_str = result.get("sentiment", "neutral").lower()
    try:
        sentiment_label = SentimentLabel(sentiment_str)
    except ValueError:
        sentiment_label = SentimentLabel.neutral

    return SentimentData(
        original_url=source_url,
        sentiment=sentiment_label,
        confidence=min(max(float(result.get("confidence", 0.5)), 0.0), 1.0),
        scores=result.get("scores", {}),
        key_phrases=result.get("key_phrases", [])[:5],
        model_used=MODEL,
        processing_time_ms=elapsed_ms,
    )


# ──────────────────────────────────────────────
# Keyword & Topic Extraction
# ──────────────────────────────────────────────

KEYWORDS_SYSTEM_PROMPT = """You are a keyword and topic extraction engine. Analyze the provided text and respond ONLY with a valid JSON object in this exact format:

{
  "keywords": ["keyword1", "keyword2", "keyword3"],
  "topics": ["topic1", "topic2"],
  "entities": [
    {"name": "Entity Name", "type": "PERSON|ORG|PLACE|PRODUCT|EVENT|OTHER"}
  ],
  "category": "technology|business|health|science|politics|entertainment|sports|education|lifestyle|other",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
}

Rules:
- "keywords" should list 5-10 semantically important keywords/phrases from the text
- "topics" should list 2-4 broad topics the text covers
- "entities" should list named entities (people, companies, places, products) found in the text (max 10)
- "category" must be exactly one of the listed categories
- "tags" should be 3-7 short, lowercase tags suitable for content categorization
- Return ONLY the JSON, no markdown, no explanation"""


async def extract_keywords(
    text: str,
    source_url: Optional[str] = None,
) -> dict:
    """Extract keywords, topics, entities, and category from text."""
    start_time = time.time()
    client = _get_client()

    truncated_text = text[:8000]

    response = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": KEYWORDS_SYSTEM_PROMPT},
            {"role": "user", "content": truncated_text},
        ],
        temperature=0.1,
        max_tokens=600,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content or "{}"

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        result = {
            "keywords": [],
            "topics": [],
            "entities": [],
            "category": "other",
            "tags": [],
        }

    elapsed_ms = int((time.time() - start_time) * 1000)

    return {
        "original_url": source_url,
        "keywords": result.get("keywords", [])[:10],
        "topics": result.get("topics", [])[:5],
        "entities": result.get("entities", [])[:10],
        "category": result.get("category", "other"),
        "tags": result.get("tags", [])[:7],
        "model_used": MODEL,
        "processing_time_ms": elapsed_ms,
    }
