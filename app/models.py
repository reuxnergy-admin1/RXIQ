"""Pydantic models for API requests and responses."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, HttpUrl


# ──────────────────────────────────────────────
# Enums
# ──────────────────────────────────────────────

class SummaryFormat(str, Enum):
    """Supported summarization output formats."""
    tldr = "tldr"
    bullets = "bullets"
    key_takeaways = "key_takeaways"
    paragraph = "paragraph"


class SentimentLabel(str, Enum):
    """Sentiment classification labels."""
    positive = "positive"
    negative = "negative"
    neutral = "neutral"
    mixed = "mixed"


# ──────────────────────────────────────────────
# Requests
# ──────────────────────────────────────────────

class ExtractRequest(BaseModel):
    """Request body for content extraction."""
    url: HttpUrl = Field(..., description="The URL to extract content from")
    include_images: bool = Field(False, description="Include image URLs in the response")
    include_links: bool = Field(False, description="Include outbound links in the response")
    output_format: str = Field("text", description="Output format: 'text' (plain text) or 'markdown'")

    model_config = {"json_schema_extra": {"examples": [{"url": "https://example.com/article", "output_format": "markdown"}]}}


class SummarizeRequest(BaseModel):
    """Request body for AI summarization."""
    url: Optional[HttpUrl] = Field(None, description="URL to scrape and summarize")
    text: Optional[str] = Field(None, description="Raw text to summarize (alternative to URL)", max_length=50000)
    format: SummaryFormat = Field(SummaryFormat.tldr, description="Output format for the summary")
    max_length: int = Field(200, description="Approximate max length of summary in words", ge=20, le=1000)
    language: str = Field("en", description="Output language (ISO 639-1 code)")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"url": "https://example.com/article", "format": "bullets", "max_length": 150}
            ]
        }
    }


class SentimentRequest(BaseModel):
    """Request body for sentiment analysis."""
    url: Optional[HttpUrl] = Field(None, description="URL to scrape and analyze")
    text: Optional[str] = Field(None, description="Raw text to analyze (alternative to URL)", max_length=50000)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"text": "This product is absolutely amazing! Best purchase I've ever made."}
            ]
        }
    }


class SEORequest(BaseModel):
    """Request body for SEO metadata extraction."""
    url: HttpUrl = Field(..., description="The URL to extract SEO metadata from")

    model_config = {"json_schema_extra": {"examples": [{"url": "https://example.com"}]}}


class AnalyzeRequest(BaseModel):
    """Request body for full content analysis (extract + summarize + sentiment + SEO)."""
    url: HttpUrl = Field(..., description="The URL to fully analyze")
    summary_format: SummaryFormat = Field(SummaryFormat.tldr, description="Summary output format")
    summary_max_length: int = Field(200, description="Approximate max summary length in words", ge=20, le=1000)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"url": "https://example.com/article", "summary_format": "bullets"}
            ]
        }
    }


# ──────────────────────────────────────────────
# Responses
# ──────────────────────────────────────────────


class ReadabilityMetrics(BaseModel):
    """Readability scores and text statistics (zero API cost)."""
    flesch_reading_ease: float = Field(0, description="Flesch Reading Ease score (0-100, higher = easier)")
    flesch_kincaid_grade: float = Field(0, description="Flesch-Kincaid US grade level")
    coleman_liau_index: float = Field(0, description="Coleman-Liau US grade level")
    automated_readability_index: float = Field(0, description="Automated Readability Index")
    avg_grade_level: float = Field(0, description="Average of all grade-level metrics")
    reading_level: str = Field("", description="Human-readable difficulty label")
    sentence_count: int = 0
    word_count: int = 0
    syllable_count: int = 0
    char_count: int = 0
    avg_sentence_length: float = 0
    avg_word_length: float = 0
    avg_syllables_per_word: float = 0
    unique_words: int = 0
    vocabulary_density: float = Field(0, description="Unique words / total words (0-1)")
    complex_word_count: int = 0
    complex_word_pct: float = Field(0, description="Percentage of words with 3+ syllables")
    reading_time_seconds: int = Field(0, description="Estimated reading time in seconds")
    reading_time_minutes: float = Field(0, description="Estimated reading time in minutes")


class ExtractedContent(BaseModel):
    """Extracted content from a web page."""
    url: str
    title: str = ""
    author: Optional[str] = None
    published_date: Optional[str] = None
    text: str = ""
    markdown: Optional[str] = Field(None, description="Content as clean Markdown (when output_format='markdown')")
    word_count: int = 0
    excerpt: str = ""
    readability: Optional[ReadabilityMetrics] = Field(None, description="Readability scores and text statistics")
    images: list[str] = Field(default_factory=list)
    links: list[str] = Field(default_factory=list)
    language: Optional[str] = None
    extraction_time_ms: int = 0


class ExtractResponse(BaseModel):
    """Response from the content extraction endpoint."""
    success: bool = True
    data: ExtractedContent
    cached: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SummaryData(BaseModel):
    """AI-generated summary data."""
    original_url: Optional[str] = None
    format: SummaryFormat
    summary: str
    word_count: int = 0
    original_word_count: int = 0
    language: str = "en"
    model_used: str = ""
    processing_time_ms: int = 0


class SummarizeResponse(BaseModel):
    """Response from the summarization endpoint."""
    success: bool = True
    data: SummaryData
    cached: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SentimentData(BaseModel):
    """Sentiment analysis results."""
    original_url: Optional[str] = None
    sentiment: SentimentLabel
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0.0 to 1.0)")
    scores: dict[str, float] = Field(
        default_factory=dict,
        description="Individual scores for each sentiment category"
    )
    key_phrases: list[str] = Field(
        default_factory=list,
        description="Key phrases that influenced the sentiment"
    )
    model_used: str = ""
    processing_time_ms: int = 0


class SentimentResponse(BaseModel):
    """Response from the sentiment analysis endpoint."""
    success: bool = True
    data: SentimentData
    cached: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class OpenGraphTags(BaseModel):
    """Open Graph metadata."""
    og_title: Optional[str] = None
    og_description: Optional[str] = None
    og_image: Optional[str] = None
    og_url: Optional[str] = None
    og_type: Optional[str] = None
    og_site_name: Optional[str] = None


class TwitterCard(BaseModel):
    """Twitter Card metadata."""
    card: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    image: Optional[str] = None
    site: Optional[str] = None


class SchemaMarkup(BaseModel):
    """JSON-LD / Schema.org structured data."""
    types: list[str] = Field(default_factory=list)
    data: list[dict[str, Any]] = Field(default_factory=list)


class SEOData(BaseModel):
    """SEO metadata extraction results."""
    url: str
    title: Optional[str] = None
    meta_description: Optional[str] = None
    canonical_url: Optional[str] = None
    h1_tags: list[str] = Field(default_factory=list)
    h2_tags: list[str] = Field(default_factory=list)
    open_graph: OpenGraphTags = Field(default_factory=OpenGraphTags)
    twitter_card: TwitterCard = Field(default_factory=TwitterCard)
    schema_markup: SchemaMarkup = Field(default_factory=SchemaMarkup)
    robots: Optional[str] = None
    viewport: Optional[str] = None
    charset: Optional[str] = None
    language: Optional[str] = None
    word_count: int = 0
    internal_links: int = 0
    external_links: int = 0
    images_without_alt: int = 0
    total_images: int = 0
    extraction_time_ms: int = 0


class SEOResponse(BaseModel):
    """Response from the SEO metadata extraction endpoint."""
    success: bool = True
    data: SEOData
    cached: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class KeywordData(BaseModel):
    """Keyword and topic extraction results."""
    original_url: Optional[str] = None
    keywords: list[str] = Field(default_factory=list, description="Important keywords/phrases")
    topics: list[str] = Field(default_factory=list, description="Broad topic categories")
    entities: list[dict[str, str]] = Field(default_factory=list, description="Named entities with types")
    category: str = Field("other", description="Content category classification")
    tags: list[str] = Field(default_factory=list, description="Auto-generated content tags")
    model_used: str = ""
    processing_time_ms: int = 0


class ContentQualityScore(BaseModel):
    """Composite content quality score (0-100)."""
    total_score: int = Field(0, description="Overall quality score (0-100)")
    grade: str = Field("F", description="Letter grade (A+ to F)")
    breakdown: dict[str, int] = Field(default_factory=dict, description="Score breakdown by category")
    max_scores: dict[str, int] = Field(default_factory=dict, description="Maximum possible score per category")
    recommendations: list[str] = Field(default_factory=list, description="Actionable improvement suggestions")


class AnalyzeData(BaseModel):
    """Full analysis combining all endpoints."""
    content: ExtractedContent
    summary: SummaryData
    sentiment: SentimentData
    seo: SEOData
    keywords: Optional[KeywordData] = None
    quality: Optional[ContentQualityScore] = None
    total_processing_time_ms: int = 0


class AnalyzeResponse(BaseModel):
    """Response from the full analysis endpoint."""
    success: bool = True
    data: AnalyzeData
    cached: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ──────────────────────────────────────────────
# Compare Endpoint
# ──────────────────────────────────────────────


class CompareRequest(BaseModel):
    """Request body for content comparison."""
    url1: HttpUrl = Field(..., description="First URL to compare")
    url2: HttpUrl = Field(..., description="Second URL to compare")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"url1": "https://example.com/article-1", "url2": "https://example.com/article-2"}
            ]
        }
    }


class CompareData(BaseModel):
    """Content comparison results."""
    url1: str
    url2: str
    similarity_score: float = Field(0, ge=0, le=1, description="Cosine similarity (0-1)")
    shared_keywords: list[str] = Field(default_factory=list)
    unique_to_url1: list[str] = Field(default_factory=list)
    unique_to_url2: list[str] = Field(default_factory=list)
    word_count_diff: int = 0
    readability_diff: dict[str, Any] = Field(default_factory=dict)
    processing_time_ms: int = 0


class CompareResponse(BaseModel):
    """Response from the content comparison endpoint."""
    success: bool = True
    data: CompareData
    cached: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorDetail(BaseModel):
    """Error detail model."""
    code: str
    message: str
    details: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standard error response."""
    success: bool = False
    error: ErrorDetail
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    version: str
    uptime_seconds: float
    redis_connected: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class UsageResponse(BaseModel):
    """API usage statistics for the current billing period."""
    plan: str = "free"
    calls_used: int = 0
    calls_limit: int = 100
    calls_remaining: int = 100
    period_start: datetime
    period_end: datetime
