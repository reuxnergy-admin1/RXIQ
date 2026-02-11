"""
RXIQ API — Python Usage Examples
Install: pip install requests
"""

import requests

# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────

BASE_URL = "https://rxiq-api.p.rapidapi.com"  # RapidAPI proxy URL
HEADERS = {
    "Content-Type": "application/json",
    "X-RapidAPI-Key": "ef7129c761msh9476e78fc3f01ecp1b52dbjsn5620584fb605",
    "X-RapidAPI-Host": "rxiq-api.p.rapidapi.com",
}


# ──────────────────────────────────────────────
# 1. Extract Content from URL
# ──────────────────────────────────────────────

def extract_content(url: str, include_images: bool = False):
    """Extract clean text and metadata from any URL."""
    response = requests.post(
        f"{BASE_URL}/api/v1/extract",
        headers=HEADERS,
        json={
            "url": url,
            "include_images": include_images,
            "include_links": False,
        },
    )
    data = response.json()

    if data["success"]:
        content = data["data"]
        print(f"Title: {content['title']}")
        print(f"Word Count: {content['word_count']}")
        print(f"Excerpt: {content['excerpt']}")
        print(f"Author: {content.get('author', 'N/A')}")
        return content
    else:
        print(f"Error: {data['error']['message']}")
        return None


# ──────────────────────────────────────────────
# 2. Summarize Content
# ──────────────────────────────────────────────

def summarize_url(url: str, format: str = "bullets"):
    """Generate an AI summary from a URL."""
    response = requests.post(
        f"{BASE_URL}/api/v1/summarize",
        headers=HEADERS,
        json={
            "url": url,
            "format": format,       # tldr, bullets, key_takeaways, paragraph
            "max_length": 200,
            "language": "en",
        },
    )
    data = response.json()

    if data["success"]:
        summary = data["data"]
        print(f"Summary ({summary['format']}):")
        print(summary["summary"])
        print(f"\nOriginal: {summary['original_word_count']} words → Summary: {summary['word_count']} words")
        return summary
    else:
        print(f"Error: {data['error']['message']}")
        return None


def summarize_text(text: str, format: str = "tldr"):
    """Summarize raw text (no URL needed)."""
    response = requests.post(
        f"{BASE_URL}/api/v1/summarize",
        headers=HEADERS,
        json={
            "text": text,
            "format": format,
            "max_length": 100,
        },
    )
    return response.json()


# ──────────────────────────────────────────────
# 3. Sentiment Analysis
# ──────────────────────────────────────────────

def analyze_sentiment(text: str):
    """Analyze sentiment of text."""
    response = requests.post(
        f"{BASE_URL}/api/v1/sentiment",
        headers=HEADERS,
        json={"text": text},
    )
    data = response.json()

    if data["success"]:
        sentiment = data["data"]
        print(f"Sentiment: {sentiment['sentiment']} (confidence: {sentiment['confidence']:.2f})")
        print(f"Scores: {sentiment['scores']}")
        print(f"Key Phrases: {', '.join(sentiment['key_phrases'])}")
        return sentiment
    else:
        print(f"Error: {data['error']['message']}")
        return None


def analyze_sentiment_url(url: str):
    """Analyze sentiment of content at a URL."""
    response = requests.post(
        f"{BASE_URL}/api/v1/sentiment",
        headers=HEADERS,
        json={"url": url},
    )
    return response.json()


# ──────────────────────────────────────────────
# 4. SEO Metadata
# ──────────────────────────────────────────────

def extract_seo(url: str):
    """Extract comprehensive SEO metadata from a URL."""
    response = requests.post(
        f"{BASE_URL}/api/v1/seo",
        headers=HEADERS,
        json={"url": url},
    )
    data = response.json()

    if data["success"]:
        seo = data["data"]
        print(f"Title: {seo['title']}")
        print(f"Meta Description: {seo['meta_description']}")
        print(f"Canonical: {seo['canonical_url']}")
        print(f"H1 Tags: {seo['h1_tags']}")
        print(f"OG Image: {seo['open_graph']['og_image']}")
        print(f"Schema Types: {seo['schema_markup']['types']}")
        print(f"Internal Links: {seo['internal_links']}")
        print(f"External Links: {seo['external_links']}")
        print(f"Images without alt: {seo['images_without_alt']}/{seo['total_images']}")
        return seo
    else:
        print(f"Error: {data['error']['message']}")
        return None


# ──────────────────────────────────────────────
# 5. Full Analysis (all in one)
# ──────────────────────────────────────────────

def full_analysis(url: str, summary_format: str = "bullets"):
    """Run all analyses on a URL in one API call."""
    response = requests.post(
        f"{BASE_URL}/api/v1/analyze",
        headers=HEADERS,
        json={
            "url": url,
            "summary_format": summary_format,
            "summary_max_length": 200,
        },
    )
    data = response.json()

    if data["success"]:
        result = data["data"]
        print(f"=== CONTENT ===")
        print(f"Title: {result['content']['title']}")
        print(f"Words: {result['content']['word_count']}")
        print()
        print(f"=== SUMMARY ===")
        print(result["summary"]["summary"])
        print()
        print(f"=== SENTIMENT ===")
        print(f"{result['sentiment']['sentiment']} ({result['sentiment']['confidence']:.2f})")
        print()
        print(f"=== SEO ===")
        print(f"Meta: {result['seo']['meta_description']}")
        print(f"Schema: {result['seo']['schema_markup']['types']}")
        print()
        print(f"Total processing time: {result['total_processing_time_ms']}ms")
        return result
    else:
        print(f"Error: {data['error']['message']}")
        return None


# ──────────────────────────────────────────────
# Run Examples
# ──────────────────────────────────────────────

if __name__ == "__main__":
    test_url = "https://example.com"

    print("=" * 60)
    print("1. EXTRACT CONTENT")
    print("=" * 60)
    extract_content(test_url)

    print("\n" + "=" * 60)
    print("2. SUMMARIZE")
    print("=" * 60)
    summarize_url(test_url, format="bullets")

    print("\n" + "=" * 60)
    print("3. SENTIMENT ANALYSIS")
    print("=" * 60)
    analyze_sentiment("This product is fantastic! Best purchase ever.")

    print("\n" + "=" * 60)
    print("4. SEO METADATA")
    print("=" * 60)
    extract_seo(test_url)

    print("\n" + "=" * 60)
    print("5. FULL ANALYSIS")
    print("=" * 60)
    full_analysis(test_url)
