"""Web content extraction service using httpx + BeautifulSoup + Trafilatura."""

from __future__ import annotations

import json
import re
import time
from typing import Optional
from urllib.parse import urljoin, urlparse

import httpx
import trafilatura
from bs4 import BeautifulSoup, Comment

from app.config import get_settings
from app.models import (
    ExtractedContent,
    OpenGraphTags,
    SchemaMarkup,
    SEOData,
    TwitterCard,
)

settings = get_settings()

# Common user agents to rotate
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:133.0) Gecko/20100101 Firefox/133.0",
]

DEFAULT_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}


async def fetch_html(url: str) -> tuple[str, str]:
    """
    Fetch HTML content from a URL.

    Validates the URL for security (SSRF protection) before fetching.

    Returns:
        Tuple of (html_content, final_url after redirects)

    Raises:
        URLValidationError: If the URL fails security checks.
        httpx.HTTPStatusError: If the HTTP response has an error status.
        httpx.TimeoutException: If the request times out.
    """
    import random

    from app.services.url_validator import validate_url

    # Validate URL before making any network request
    validate_url(url)

    headers = {
        **DEFAULT_HEADERS,
        "User-Agent": random.choice(USER_AGENTS),
    }

    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=httpx.Timeout(settings.scrape_timeout),
        verify=True,
        max_redirects=5,
    ) as client:
        response = await client.get(str(url), headers=headers)
        response.raise_for_status()

        # Verify content-type is HTML-ish
        content_type = response.headers.get("content-type", "")
        if (
            content_type
            and "html" not in content_type.lower()
            and "text" not in content_type.lower()
        ):
            raise ValueError(
                f"URL returned non-HTML content type: {content_type}. "
                "Only HTML pages are supported."
            )

        # Enforce max response size (10MB)
        content_length = len(response.text)
        if content_length > 10_000_000:
            raise ValueError("Response too large (>10MB). URL may not be an HTML page.")

        return response.text, str(response.url)


def extract_content(
    html: str,
    url: str,
    include_images: bool = False,
    include_links: bool = False,
    output_format: str = "text",
) -> ExtractedContent:
    """
    Extract clean, structured content from HTML.

    Uses Trafilatura for main content extraction and BeautifulSoup for metadata.

    Args:
        output_format: "text" for plain text, "markdown" for Markdown output.
    """
    start_time = time.time()

    soup = BeautifulSoup(html, "lxml")

    # --- Extract metadata ---
    title = ""
    title_tag = soup.find("title")
    if title_tag:
        title = title_tag.get_text(strip=True)

    # Try to find author
    author = _extract_author(soup)

    # Try to find published date
    published_date = _extract_date(soup)

    # Detect language
    language = None
    html_tag = soup.find("html")
    if html_tag and html_tag.get("lang"):
        language = html_tag["lang"]

    # --- Extract main content with Trafilatura ---
    extracted = trafilatura.extract(
        html,
        url=url,
        include_comments=False,
        include_tables=True,
        no_fallback=False,
        favor_precision=False,
        favor_recall=True,
    )

    text = extracted or ""

    # Fallback: use BeautifulSoup if Trafilatura returns nothing
    if not text:
        text = _fallback_extract(soup)

    # Markdown output (Trafilatura natively supports this)
    markdown_text: str | None = None
    if output_format == "markdown":
        md = trafilatura.extract(
            html,
            url=url,
            include_comments=False,
            include_tables=True,
            include_links=True,
            include_images=True,
            no_fallback=False,
            favor_recall=True,
            output_format="markdown",
        )
        markdown_text = md or None

    # Truncate if too long
    if len(text) > settings.max_content_length:
        text = text[: settings.max_content_length] + "..."
    if markdown_text and len(markdown_text) > settings.max_content_length:
        markdown_text = markdown_text[: settings.max_content_length] + "..."

    word_count = len(text.split()) if text else 0

    # Excerpt (first 300 chars)
    excerpt = text[:300].strip() + "..." if len(text) > 300 else text.strip()

    # Readability metrics (zero-cost computation)
    readability = None
    if text and word_count >= 20:
        from app.models import ReadabilityMetrics
        from app.services.text_analytics import compute_readability
        from dataclasses import asdict

        scores = compute_readability(text)
        readability = ReadabilityMetrics(**asdict(scores))

    # Optional: images
    images: list[str] = []
    if include_images:
        for img in soup.find_all("img", src=True):
            img_url = urljoin(url, img["src"])
            if img_url not in images:
                images.append(img_url)

    # Optional: links
    links: list[str] = []
    if include_links:
        for a in soup.find_all("a", href=True):
            href = urljoin(url, a["href"])
            parsed = urlparse(href)
            if parsed.scheme in ("http", "https") and href not in links:
                links.append(href)

    elapsed_ms = int((time.time() - start_time) * 1000)

    return ExtractedContent(
        url=url,
        title=title,
        author=author,
        published_date=published_date,
        text=text,
        markdown=markdown_text,
        word_count=word_count,
        excerpt=excerpt,
        readability=readability,
        images=images[:50],  # Limit to 50 images
        links=links[:100],  # Limit to 100 links
        language=language,
        extraction_time_ms=elapsed_ms,
    )


def extract_seo_metadata(html: str, url: str) -> SEOData:
    """Extract comprehensive SEO metadata from HTML."""
    start_time = time.time()
    soup = BeautifulSoup(html, "lxml")
    parsed_url = urlparse(url)

    # Title
    title = None
    title_tag = soup.find("title")
    if title_tag:
        title = title_tag.get_text(strip=True)

    # Meta description
    meta_desc = None
    meta_tag = soup.find("meta", attrs={"name": re.compile(r"description", re.I)})
    if meta_tag:
        meta_desc = meta_tag.get("content", "")

    # Canonical URL
    canonical = None
    link_tag = soup.find("link", attrs={"rel": "canonical"})
    if link_tag:
        canonical = link_tag.get("href", "")

    # Heading tags
    h1_tags = [h.get_text(strip=True) for h in soup.find_all("h1")]
    h2_tags = [h.get_text(strip=True) for h in soup.find_all("h2")]

    # Open Graph tags
    og = _extract_open_graph(soup)

    # Twitter Card
    tc = _extract_twitter_card(soup)

    # Schema.org / JSON-LD
    schema = _extract_schema_markup(soup)

    # Robots meta
    robots = None
    robots_tag = soup.find("meta", attrs={"name": re.compile(r"robots", re.I)})
    if robots_tag:
        robots = robots_tag.get("content", "")

    # Viewport
    viewport = None
    vp_tag = soup.find("meta", attrs={"name": "viewport"})
    if vp_tag:
        viewport = vp_tag.get("content", "")

    # Charset
    charset = None
    charset_tag = soup.find("meta", attrs={"charset": True})
    if charset_tag:
        charset = charset_tag.get("charset", "")

    # Language
    language = None
    html_tag = soup.find("html")
    if html_tag and html_tag.get("lang"):
        language = html_tag["lang"]

    # Word count (visible text)
    body = soup.find("body")
    visible_text = body.get_text(" ", strip=True) if body else ""
    word_count = len(visible_text.split())

    # Link analysis
    all_links = soup.find_all("a", href=True)
    internal_links = 0
    external_links = 0
    for a in all_links:
        href = a["href"]
        link_parsed = urlparse(urljoin(url, href))
        if link_parsed.netloc == parsed_url.netloc or not link_parsed.netloc:
            internal_links += 1
        else:
            external_links += 1

    # Image analysis
    all_images = soup.find_all("img")
    total_images = len(all_images)
    images_without_alt = sum(1 for img in all_images if not img.get("alt"))

    elapsed_ms = int((time.time() - start_time) * 1000)

    return SEOData(
        url=url,
        title=title,
        meta_description=meta_desc,
        canonical_url=canonical,
        h1_tags=h1_tags[:10],
        h2_tags=h2_tags[:20],
        open_graph=og,
        twitter_card=tc,
        schema_markup=schema,
        robots=robots,
        viewport=viewport,
        charset=charset,
        language=language,
        word_count=word_count,
        internal_links=internal_links,
        external_links=external_links,
        images_without_alt=images_without_alt,
        total_images=total_images,
        extraction_time_ms=elapsed_ms,
    )


# ──────────────────────────────────────────────
# Private helpers
# ──────────────────────────────────────────────


def _extract_author(soup: BeautifulSoup) -> Optional[str]:
    """Try multiple strategies to find the article author."""
    # <meta name="author">
    meta = soup.find("meta", attrs={"name": re.compile(r"author", re.I)})
    if meta:
        return meta.get("content", "").strip() or None

    # <meta property="article:author">
    meta = soup.find("meta", attrs={"property": re.compile(r"article:author", re.I)})
    if meta:
        return meta.get("content", "").strip() or None

    # Schema.org author in JSON-LD
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            data = json.loads(script.string or "")
            if isinstance(data, dict):
                author = data.get("author")
                if isinstance(author, dict):
                    return author.get("name")
                elif isinstance(author, str):
                    return author
        except (json.JSONDecodeError, TypeError):
            continue

    return None


def _extract_date(soup: BeautifulSoup) -> Optional[str]:
    """Try multiple strategies to find the published date."""
    # <meta property="article:published_time">
    meta = soup.find(
        "meta", attrs={"property": re.compile(r"article:published_time", re.I)}
    )
    if meta:
        return meta.get("content", "").strip() or None

    # <time datetime="">
    time_tag = soup.find("time", attrs={"datetime": True})
    if time_tag:
        return time_tag["datetime"]

    # <meta name="date">
    meta = soup.find("meta", attrs={"name": re.compile(r"^date$", re.I)})
    if meta:
        return meta.get("content", "").strip() or None

    return None


def _extract_open_graph(soup: BeautifulSoup) -> OpenGraphTags:
    """Extract Open Graph meta tags."""

    def get_og(prop: str) -> Optional[str]:
        tag = soup.find("meta", attrs={"property": f"og:{prop}"})
        return tag.get("content", "").strip() if tag else None

    return OpenGraphTags(
        og_title=get_og("title"),
        og_description=get_og("description"),
        og_image=get_og("image"),
        og_url=get_og("url"),
        og_type=get_og("type"),
        og_site_name=get_og("site_name"),
    )


def _extract_twitter_card(soup: BeautifulSoup) -> TwitterCard:
    """Extract Twitter Card meta tags."""

    def get_tc(name: str) -> Optional[str]:
        tag = soup.find("meta", attrs={"name": f"twitter:{name}"})
        if not tag:
            tag = soup.find("meta", attrs={"property": f"twitter:{name}"})
        return tag.get("content", "").strip() if tag else None

    return TwitterCard(
        card=get_tc("card"),
        title=get_tc("title"),
        description=get_tc("description"),
        image=get_tc("image"),
        site=get_tc("site"),
    )


def _extract_schema_markup(soup: BeautifulSoup) -> SchemaMarkup:
    """Extract JSON-LD Schema.org structured data."""
    types: list[str] = []
    data: list[dict] = []

    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            parsed = json.loads(script.string or "")
            if isinstance(parsed, dict):
                t = parsed.get("@type", "Unknown")
                types.append(t if isinstance(t, str) else str(t))
                data.append(parsed)
            elif isinstance(parsed, list):
                for item in parsed:
                    if isinstance(item, dict):
                        t = item.get("@type", "Unknown")
                        types.append(t if isinstance(t, str) else str(t))
                        data.append(item)
        except (json.JSONDecodeError, TypeError):
            continue

    return SchemaMarkup(types=types, data=data[:10])  # Limit to 10 items


def _fallback_extract(soup: BeautifulSoup) -> str:
    """Fallback content extraction when Trafilatura fails."""
    # Remove script, style, nav, header, footer elements
    for tag in soup.find_all(["script", "style", "nav", "header", "footer", "aside"]):
        tag.decompose()

    # Remove comments
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()

    # Try to find article or main content area
    content_area = (
        soup.find("article")
        or soup.find("main")
        or soup.find(attrs={"role": "main"})
        or soup.find("div", class_=re.compile(r"content|article|post|entry", re.I))
        or soup.find("body")
    )

    if content_area:
        paragraphs = content_area.find_all("p")
        text = "\n\n".join(
            p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)
        )
        if text:
            return text

    # Last resort: all body text
    body = soup.find("body")
    return body.get_text(" ", strip=True) if body else ""
