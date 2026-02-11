"""API v1 routes for RXIQ API.

Production-ready with:
- Granular error codes and appropriate HTTP status codes
- SSRF protection via URL validation
- Proper timeout vs. scraping vs. AI error differentiation
- Structured logging for every request
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime

import httpx
from fastapi import APIRouter, HTTPException

from app.models import (
    AnalyzeData,
    AnalyzeRequest,
    AnalyzeResponse,
    CompareData,
    CompareRequest,
    CompareResponse,
    ContentQualityScore,
    ErrorDetail,
    ErrorResponse,
    ExtractRequest,
    ExtractResponse,
    KeywordData,
    SentimentRequest,
    SentimentResponse,
    SEORequest,
    SEOResponse,
    SummarizeRequest,
    SummarizeResponse,
)
from app.services import ai_service, cache, scraper
from app.services.url_validator import URLValidationError

logger = logging.getLogger("rxiq.routes")

router = APIRouter(prefix="/api/v1", tags=["RXIQ API v1"])


# ──────────────────────────────────────────────
# Shared error-handling helper
# ──────────────────────────────────────────────


def _handle_scrape_error(e: Exception, endpoint: str) -> HTTPException:
    """Convert scraping/AI exceptions into appropriate HTTP errors."""
    if isinstance(e, URLValidationError):
        return HTTPException(
            status_code=400,
            detail=ErrorDetail(
                code="INVALID_URL",
                message=e.reason,
            ).model_dump(),
        )
    if isinstance(e, httpx.TimeoutException):
        return HTTPException(
            status_code=504,
            detail=ErrorDetail(
                code="TIMEOUT",
                message="The target URL took too long to respond. Try again or use a different URL.",
            ).model_dump(),
        )
    if isinstance(e, httpx.HTTPStatusError):
        status = e.response.status_code
        return HTTPException(
            status_code=502,
            detail=ErrorDetail(
                code="UPSTREAM_ERROR",
                message=f"The target URL returned HTTP {status}.",
                details=f"Could not fetch the page (HTTP {status}).",
            ).model_dump(),
        )
    if isinstance(e, httpx.ConnectError):
        return HTTPException(
            status_code=502,
            detail=ErrorDetail(
                code="CONNECTION_FAILED",
                message="Could not connect to the target URL. Verify it is accessible.",
            ).model_dump(),
        )
    if isinstance(e, ValueError):
        return HTTPException(
            status_code=422,
            detail=ErrorDetail(
                code="INVALID_CONTENT",
                message=str(e),
            ).model_dump(),
        )

    # Generic fallback
    logger.error(f"[{endpoint}] Unhandled error: {e}", exc_info=True)
    return HTTPException(
        status_code=500,
        detail=ErrorDetail(
            code=f"{endpoint.upper()}_FAILED",
            message=f"An unexpected error occurred during {endpoint}.",
            details=str(e),
        ).model_dump(),
    )


# ──────────────────────────────────────────────
# Content Extraction
# ──────────────────────────────────────────────


@router.post(
    "/extract",
    response_model=ExtractResponse,
    summary="Extract content from a URL",
    description=(
        "Scrape and return clean, structured text from any URL. "
        "Extracts the main article body, metadata, and optionally images and links."
    ),
    responses={
        400: {"model": ErrorResponse, "description": "Invalid URL"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Extraction failed"},
        502: {"model": ErrorResponse, "description": "Target URL error"},
        504: {"model": ErrorResponse, "description": "Target URL timeout"},
    },
)
async def extract_content_endpoint(request: ExtractRequest):
    """Extract clean, structured content from a web page."""
    url = str(request.url)

    # Check cache
    cache_key = f"{url}:{request.include_images}:{request.include_links}:{request.output_format}"
    cached = await cache.get_cached("extract", cache_key)
    if cached:
        return ExtractResponse(
            data=cached,
            cached=True,
            timestamp=datetime.utcnow(),
        )

    try:
        html, final_url = await scraper.fetch_html(url)
        content = scraper.extract_content(
            html,
            final_url,
            include_images=request.include_images,
            include_links=request.include_links,
            output_format=request.output_format,
        )

        # Cache the result
        await cache.set_cached("extract", cache_key, content.model_dump())

        logger.info(
            f"[extract] url={url} words={content.word_count} ms={content.extraction_time_ms}"
        )
        return ExtractResponse(data=content, timestamp=datetime.utcnow())

    except HTTPException:
        raise
    except Exception as e:
        raise _handle_scrape_error(e, "extraction")


# ──────────────────────────────────────────────
# AI Summarization
# ──────────────────────────────────────────────


@router.post(
    "/summarize",
    response_model=SummarizeResponse,
    summary="Summarize content with AI",
    description=(
        "Generate an AI-powered summary of web content or raw text. "
        "Supports TL;DR, bullet points, key takeaways, and paragraph formats."
    ),
    responses={
        400: {"model": ErrorResponse, "description": "Invalid URL"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Summarization failed"},
        502: {"model": ErrorResponse, "description": "Target URL error"},
        504: {"model": ErrorResponse, "description": "Target URL timeout"},
    },
)
async def summarize_endpoint(request: SummarizeRequest):
    """Generate an AI summary of content from a URL or raw text."""
    if not request.url and not request.text:
        raise HTTPException(
            status_code=422,
            detail=ErrorDetail(
                code="MISSING_INPUT",
                message="Either 'url' or 'text' must be provided.",
            ).model_dump(),
        )

    # Build cache key
    source = str(request.url) if request.url else (request.text or "")[:200]
    cache_key = (
        f"{source}:{request.format.value}:{request.max_length}:{request.language}"
    )
    cached = await cache.get_cached("summarize", cache_key)
    if cached:
        return SummarizeResponse(
            data=cached,
            cached=True,
            timestamp=datetime.utcnow(),
        )

    try:
        text = request.text or ""
        source_url = None

        if request.url:
            source_url = str(request.url)
            html, final_url = await scraper.fetch_html(source_url)
            content = scraper.extract_content(html, final_url)
            text = content.text

        if not text.strip():
            raise HTTPException(
                status_code=422,
                detail=ErrorDetail(
                    code="NO_CONTENT",
                    message="No content could be extracted from the provided URL or text.",
                ).model_dump(),
            )

        summary = await ai_service.summarize_text(
            text=text,
            format=request.format,
            max_length=request.max_length,
            language=request.language,
            source_url=source_url,
        )

        await cache.set_cached("summarize", cache_key, summary.model_dump())

        logger.info(
            f"[summarize] format={request.format.value} "
            f"words={summary.original_word_count}->{summary.word_count} "
            f"ms={summary.processing_time_ms}"
        )
        return SummarizeResponse(data=summary, timestamp=datetime.utcnow())

    except HTTPException:
        raise
    except Exception as e:
        raise _handle_scrape_error(e, "summarization")


# ──────────────────────────────────────────────
# Sentiment Analysis
# ──────────────────────────────────────────────


@router.post(
    "/sentiment",
    response_model=SentimentResponse,
    summary="Analyze sentiment of content",
    description=(
        "Perform AI-powered sentiment analysis on web content or raw text. "
        "Returns sentiment label, confidence score, and key influencing phrases."
    ),
    responses={
        400: {"model": ErrorResponse, "description": "Invalid URL"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Analysis failed"},
        502: {"model": ErrorResponse, "description": "Target URL error"},
        504: {"model": ErrorResponse, "description": "Target URL timeout"},
    },
)
async def sentiment_endpoint(request: SentimentRequest):
    """Analyze the sentiment of content from a URL or raw text."""
    if not request.url and not request.text:
        raise HTTPException(
            status_code=422,
            detail=ErrorDetail(
                code="MISSING_INPUT",
                message="Either 'url' or 'text' must be provided.",
            ).model_dump(),
        )

    source = str(request.url) if request.url else (request.text or "")[:200]
    cache_key = f"{source}"
    cached = await cache.get_cached("sentiment", cache_key)
    if cached:
        return SentimentResponse(
            data=cached,
            cached=True,
            timestamp=datetime.utcnow(),
        )

    try:
        text = request.text or ""
        source_url = None

        if request.url:
            source_url = str(request.url)
            html, final_url = await scraper.fetch_html(source_url)
            content = scraper.extract_content(html, final_url)
            text = content.text

        if not text.strip():
            raise HTTPException(
                status_code=422,
                detail=ErrorDetail(
                    code="NO_CONTENT",
                    message="No content could be extracted from the provided URL or text.",
                ).model_dump(),
            )

        sentiment = await ai_service.analyze_sentiment(
            text=text,
            source_url=source_url,
        )

        await cache.set_cached("sentiment", cache_key, sentiment.model_dump())

        logger.info(
            f"[sentiment] result={sentiment.sentiment.value} "
            f"confidence={sentiment.confidence:.2f} "
            f"ms={sentiment.processing_time_ms}"
        )
        return SentimentResponse(data=sentiment, timestamp=datetime.utcnow())

    except HTTPException:
        raise
    except Exception as e:
        raise _handle_scrape_error(e, "sentiment")


# ──────────────────────────────────────────────
# SEO Metadata
# ──────────────────────────────────────────────


@router.post(
    "/seo",
    response_model=SEOResponse,
    summary="Extract SEO metadata from a URL",
    description=(
        "Extract comprehensive SEO metadata from any web page, including "
        "title, description, Open Graph tags, Twitter Cards, Schema.org markup, "
        "heading structure, and link analysis."
    ),
    responses={
        400: {"model": ErrorResponse, "description": "Invalid URL"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Extraction failed"},
        502: {"model": ErrorResponse, "description": "Target URL error"},
        504: {"model": ErrorResponse, "description": "Target URL timeout"},
    },
)
async def seo_endpoint(request: SEORequest):
    """Extract SEO metadata from a web page."""
    url = str(request.url)

    cached = await cache.get_cached("seo", url)
    if cached:
        return SEOResponse(
            data=cached,
            cached=True,
            timestamp=datetime.utcnow(),
        )

    try:
        html, final_url = await scraper.fetch_html(url)
        seo_data = scraper.extract_seo_metadata(html, final_url)

        await cache.set_cached("seo", url, seo_data.model_dump())

        logger.info(f"[seo] url={url} ms={seo_data.extraction_time_ms}")
        return SEOResponse(data=seo_data, timestamp=datetime.utcnow())

    except HTTPException:
        raise
    except Exception as e:
        raise _handle_scrape_error(e, "seo_extraction")


# ──────────────────────────────────────────────
# Full Analysis (combo endpoint)
# ──────────────────────────────────────────────


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    summary="Full content analysis",
    description=(
        "Perform a comprehensive analysis of any URL in a single API call. "
        "Returns extracted content, AI summary, sentiment analysis, and SEO metadata. "
        "This is the most powerful endpoint — one call gives you everything."
    ),
    responses={
        400: {"model": ErrorResponse, "description": "Invalid URL"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Analysis failed"},
        502: {"model": ErrorResponse, "description": "Target URL error"},
        504: {"model": ErrorResponse, "description": "Target URL timeout"},
    },
)
async def analyze_endpoint(request: AnalyzeRequest):
    """Full content analysis: extract + summarize + sentiment + SEO in one call."""
    url = str(request.url)
    total_start = time.time()

    cache_key = f"{url}:{request.summary_format.value}:{request.summary_max_length}"
    cached = await cache.get_cached("analyze", cache_key)
    if cached:
        return AnalyzeResponse(
            data=cached,
            cached=True,
            timestamp=datetime.utcnow(),
        )

    try:
        # Step 1: Fetch HTML once
        html, final_url = await scraper.fetch_html(url)

        # Step 2: Extract content and SEO (CPU-bound, fast)
        content = scraper.extract_content(
            html, final_url, include_images=True, include_links=False
        )
        seo_data = scraper.extract_seo_metadata(html, final_url)

        if not content.text.strip():
            raise HTTPException(
                status_code=422,
                detail=ErrorDetail(
                    code="NO_CONTENT",
                    message="No content could be extracted from the URL.",
                ).model_dump(),
            )

        # Step 3: Run AI tasks in parallel (IO-bound)
        summary_task = ai_service.summarize_text(
            text=content.text,
            format=request.summary_format,
            max_length=request.summary_max_length,
            source_url=final_url,
        )
        sentiment_task = ai_service.analyze_sentiment(
            text=content.text,
            source_url=final_url,
        )
        keywords_task = ai_service.extract_keywords(
            text=content.text,
            source_url=final_url,
        )

        summary, sentiment, kw_raw = await asyncio.gather(
            summary_task, sentiment_task, keywords_task
        )

        # Build keyword data model
        keywords = KeywordData(
            original_url=final_url,
            keywords=kw_raw.get("keywords", []),
            topics=kw_raw.get("topics", []),
            entities=kw_raw.get("entities", []),
            category=kw_raw.get("category", "other"),
            tags=kw_raw.get("tags", []),
            model_used=kw_raw.get("model_used", ""),
            processing_time_ms=kw_raw.get("processing_time_ms", 0),
        )

        # Content quality score (zero-cost computation)
        from app.services.text_analytics import (
            compute_content_quality_score,
            compute_readability as _cr,
        )

        _readability = _cr(content.text) if content.word_count >= 20 else None
        quality_raw = compute_content_quality_score(
            word_count=content.word_count,
            sentence_count=_readability.sentence_count if _readability else 1,
            flesch_reading_ease=_readability.flesch_reading_ease
            if _readability
            else 50.0,
            h1_count=len(seo_data.h1_tags),
            h2_count=len(seo_data.h2_tags),
            total_images=seo_data.total_images,
            images_without_alt=seo_data.images_without_alt,
            internal_links=seo_data.internal_links,
            external_links=seo_data.external_links,
            has_meta_description=bool(seo_data.meta_description),
            has_canonical=bool(seo_data.canonical_url),
            has_open_graph=bool(seo_data.open_graph and seo_data.open_graph.og_title),
            has_schema_markup=bool(
                seo_data.schema_markup and seo_data.schema_markup.types
            ),
        )
        quality = ContentQualityScore(**quality_raw)

        total_ms = int((time.time() - total_start) * 1000)

        analyze_data = AnalyzeData(
            content=content,
            summary=summary,
            sentiment=sentiment,
            seo=seo_data,
            keywords=keywords,
            quality=quality,
            total_processing_time_ms=total_ms,
        )

        await cache.set_cached("analyze", cache_key, analyze_data.model_dump())

        logger.info(
            f"[analyze] url={url} words={content.word_count} "
            f"sentiment={sentiment.sentiment.value} total_ms={total_ms}"
        )
        return AnalyzeResponse(data=analyze_data, timestamp=datetime.utcnow())

    except HTTPException:
        raise
    except Exception as e:
        raise _handle_scrape_error(e, "analysis")


# ──────────────────────────────────────────────
# Content Comparison
# ──────────────────────────────────────────────


@router.post(
    "/compare",
    response_model=CompareResponse,
    summary="Compare content from two URLs",
    description=(
        "Compare two web pages side-by-side. Returns cosine similarity score, "
        "shared keywords, unique keywords per URL, word count difference, and "
        "readability comparison. Useful for plagiarism detection, content gap "
        "analysis, and competitive benchmarking."
    ),
    responses={
        400: {"model": ErrorResponse, "description": "Invalid URL"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Comparison failed"},
        502: {"model": ErrorResponse, "description": "Target URL error"},
        504: {"model": ErrorResponse, "description": "Target URL timeout"},
    },
)
async def compare_endpoint(request: CompareRequest):
    """Compare content from two URLs."""
    url1 = str(request.url1)
    url2 = str(request.url2)
    total_start = time.time()

    cache_key = f"{url1}|{url2}"
    cached = await cache.get_cached("compare", cache_key)
    if cached:
        return CompareResponse(
            data=cached,
            cached=True,
            timestamp=datetime.utcnow(),
        )

    try:
        # Fetch both pages in parallel
        html1_task = scraper.fetch_html(url1)
        html2_task = scraper.fetch_html(url2)
        (html1, final1), (html2, final2) = await asyncio.gather(html1_task, html2_task)

        # Extract content from both
        content1 = scraper.extract_content(html1, final1)
        content2 = scraper.extract_content(html2, final2)

        if not content1.text.strip() or not content2.text.strip():
            raise HTTPException(
                status_code=422,
                detail=ErrorDetail(
                    code="NO_CONTENT",
                    message="Could not extract content from one or both URLs.",
                ).model_dump(),
            )

        # Compute similarity (zero-cost)
        from app.services.text_analytics import compute_readability, compute_similarity

        sim = compute_similarity(content1.text, content2.text)

        # Readability comparison
        readability_diff: dict[str, float] = {}
        r1 = compute_readability(content1.text) if content1.word_count >= 20 else None
        r2 = compute_readability(content2.text) if content2.word_count >= 20 else None
        if r1 and r2:
            readability_diff = {
                "flesch_reading_ease_diff": round(
                    r1.flesch_reading_ease - r2.flesch_reading_ease, 2
                ),
                "grade_level_diff": round(r1.avg_grade_level - r2.avg_grade_level, 2),
                "url1_reading_level": r1.reading_level,
                "url2_reading_level": r2.reading_level,
            }

        total_ms = int((time.time() - total_start) * 1000)

        compare_data = CompareData(
            url1=final1,
            url2=final2,
            similarity_score=sim["similarity_score"],
            shared_keywords=sim["shared_keywords"],
            unique_to_url1=sim["unique_to_text1"],
            unique_to_url2=sim["unique_to_text2"],
            word_count_diff=content1.word_count - content2.word_count,
            readability_diff=readability_diff,
            processing_time_ms=total_ms,
        )

        await cache.set_cached("compare", cache_key, compare_data.model_dump())

        logger.info(
            f"[compare] url1={url1} url2={url2} "
            f"similarity={sim['similarity_score']:.4f} ms={total_ms}"
        )
        return CompareResponse(data=compare_data, timestamp=datetime.utcnow())

    except HTTPException:
        raise
    except Exception as e:
        raise _handle_scrape_error(e, "comparison")
