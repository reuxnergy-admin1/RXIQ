"""Tests for the scraper service — content and SEO extraction."""

from __future__ import annotations

from app.services.scraper import extract_content, extract_seo_metadata

SAMPLE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Article - Sample Site</title>
    <meta name="description" content="This is a test article for unit testing.">
    <meta name="author" content="John Doe">
    <meta property="og:title" content="Test Article OG Title">
    <meta property="og:description" content="OG description for test article">
    <meta property="og:image" content="https://example.com/image.jpg">
    <meta property="og:type" content="article">
    <meta property="article:published_time" content="2026-01-15T10:00:00Z">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="Test Article Twitter Title">
    <meta name="robots" content="index, follow">
    <link rel="canonical" href="https://example.com/test-article">
    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": "Test Article",
        "author": {
            "@type": "Person",
            "name": "John Doe"
        }
    }
    </script>
</head>
<body>
    <header><nav>Navigation</nav></header>
    <article>
        <h1>Test Article Heading</h1>
        <h2>Introduction</h2>
        <p>This is the first paragraph of the test article. It contains some important information about the topic at hand. The article discusses various aspects of testing web content extraction.</p>
        <h2>Main Content</h2>
        <p>The main content section provides detailed analysis. We explore multiple dimensions of the subject matter, including technical implementation details and best practices for content extraction.</p>
        <p>Additional paragraph with more content to ensure we have enough text for extraction testing. This paragraph adds depth to the article and provides more material for the summarization engine.</p>
        <img src="/images/test.jpg" alt="Test image">
        <img src="/images/no-alt.jpg">
        <a href="/internal-link">Internal Link</a>
        <a href="https://external.com/page">External Link</a>
    </article>
    <footer>Footer content</footer>
</body>
</html>
"""


class TestContentExtraction:
    """Tests for content extraction."""

    def test_extracts_title(self):
        result = extract_content(SAMPLE_HTML, "https://example.com/test-article")
        assert result.title == "Test Article - Sample Site"

    def test_extracts_author(self):
        result = extract_content(SAMPLE_HTML, "https://example.com/test-article")
        assert result.author == "John Doe"

    def test_extracts_published_date(self):
        result = extract_content(SAMPLE_HTML, "https://example.com/test-article")
        assert result.published_date == "2026-01-15T10:00:00Z"

    def test_extracts_text(self):
        result = extract_content(SAMPLE_HTML, "https://example.com/test-article")
        assert len(result.text) > 0
        assert result.word_count > 0

    def test_detects_language(self):
        result = extract_content(SAMPLE_HTML, "https://example.com/test-article")
        assert result.language == "en"

    def test_generates_excerpt(self):
        result = extract_content(SAMPLE_HTML, "https://example.com/test-article")
        assert len(result.excerpt) > 0
        assert len(result.excerpt) <= 303  # 300 + "..."

    def test_includes_images_when_requested(self):
        result = extract_content(
            SAMPLE_HTML, "https://example.com/test-article", include_images=True
        )
        assert len(result.images) > 0

    def test_excludes_images_by_default(self):
        result = extract_content(SAMPLE_HTML, "https://example.com/test-article")
        assert len(result.images) == 0

    def test_includes_links_when_requested(self):
        result = extract_content(
            SAMPLE_HTML, "https://example.com/test-article", include_links=True
        )
        assert len(result.links) > 0

    def test_tracks_extraction_time(self):
        result = extract_content(SAMPLE_HTML, "https://example.com/test-article")
        assert result.extraction_time_ms >= 0


class TestSEOExtraction:
    """Tests for SEO metadata extraction."""

    def test_extracts_title(self):
        result = extract_seo_metadata(SAMPLE_HTML, "https://example.com/test-article")
        assert result.title == "Test Article - Sample Site"

    def test_extracts_meta_description(self):
        result = extract_seo_metadata(SAMPLE_HTML, "https://example.com/test-article")
        assert result.meta_description == "This is a test article for unit testing."

    def test_extracts_canonical_url(self):
        result = extract_seo_metadata(SAMPLE_HTML, "https://example.com/test-article")
        assert result.canonical_url == "https://example.com/test-article"

    def test_extracts_h1_tags(self):
        result = extract_seo_metadata(SAMPLE_HTML, "https://example.com/test-article")
        assert "Test Article Heading" in result.h1_tags

    def test_extracts_h2_tags(self):
        result = extract_seo_metadata(SAMPLE_HTML, "https://example.com/test-article")
        assert "Introduction" in result.h2_tags
        assert "Main Content" in result.h2_tags

    def test_extracts_open_graph(self):
        result = extract_seo_metadata(SAMPLE_HTML, "https://example.com/test-article")
        assert result.open_graph.og_title == "Test Article OG Title"
        assert result.open_graph.og_type == "article"
        assert result.open_graph.og_image == "https://example.com/image.jpg"

    def test_extracts_twitter_card(self):
        result = extract_seo_metadata(SAMPLE_HTML, "https://example.com/test-article")
        assert result.twitter_card.card == "summary_large_image"
        assert result.twitter_card.title == "Test Article Twitter Title"

    def test_extracts_schema_markup(self):
        result = extract_seo_metadata(SAMPLE_HTML, "https://example.com/test-article")
        assert "Article" in result.schema_markup.types
        assert len(result.schema_markup.data) > 0

    def test_extracts_robots(self):
        result = extract_seo_metadata(SAMPLE_HTML, "https://example.com/test-article")
        assert result.robots == "index, follow"

    def test_extracts_charset(self):
        result = extract_seo_metadata(SAMPLE_HTML, "https://example.com/test-article")
        assert result.charset == "UTF-8"

    def test_counts_links(self):
        result = extract_seo_metadata(SAMPLE_HTML, "https://example.com/test-article")
        assert result.internal_links >= 1
        assert result.external_links >= 1

    def test_counts_images(self):
        result = extract_seo_metadata(SAMPLE_HTML, "https://example.com/test-article")
        assert result.total_images == 2
        assert result.images_without_alt == 1

    def test_detects_language(self):
        result = extract_seo_metadata(SAMPLE_HTML, "https://example.com/test-article")
        assert result.language == "en"

    def test_tracks_extraction_time(self):
        result = extract_seo_metadata(SAMPLE_HTML, "https://example.com/test-article")
        assert result.extraction_time_ms >= 0
