"""RapidAPI pricing tiers configuration.

This module defines the pricing plans and their limits, matching what you configure
on the RapidAPI marketplace. Use this for server-side enforcement if needed beyond
what RapidAPI already handles.
"""

PRICING_TIERS = {
    "free": {
        "name": "Basic (Free)",
        "price_monthly": 0,
        "calls_per_month": 100,
        "rate_per_minute": 5,
        "endpoints": ["extract"],  # Free tier: extract only
        "features": [
            "Content extraction from any URL",
            "Basic metadata (title, author, date)",
            "Rate limited to 5 requests/minute",
        ],
        "overage_price": None,  # Hard limit
    },
    "starter": {
        "name": "Starter",
        "price_monthly": 9.99,
        "calls_per_month": 2500,
        "rate_per_minute": 10,
        "endpoints": ["extract", "summarize", "sentiment", "seo", "analyze"],
        "features": [
            "All 5 endpoints",
            "AI summarization (4 formats)",
            "Sentiment analysis",
            "SEO metadata extraction",
            "Full analysis endpoint",
            "Standard processing speed",
            "10 requests/minute",
        ],
        "overage_price": 0.005,
    },
    "pro": {
        "name": "Pro",
        "price_monthly": 29.99,
        "calls_per_month": 15000,
        "rate_per_minute": 30,
        "endpoints": ["extract", "summarize", "sentiment", "seo", "analyze"],
        "features": [
            "Everything in Starter",
            "Priority processing speed",
            "30 requests/minute",
            "Webhook support (coming soon)",
            "Email support",
        ],
        "overage_price": 0.003,
    },
    "business": {
        "name": "Business",
        "price_monthly": 99.99,
        "calls_per_month": 75000,
        "rate_per_minute": 60,
        "endpoints": ["extract", "summarize", "sentiment", "seo", "analyze"],
        "features": [
            "Everything in Pro",
            "Fastest processing speed",
            "60 requests/minute",
            "Bulk/batch processing",
            "Dedicated support",
            "Custom integrations",
        ],
        "overage_price": 0.002,
    },
    "enterprise": {
        "name": "Enterprise",
        "price_monthly": "custom",
        "calls_per_month": "unlimited",
        "rate_per_minute": "unlimited",
        "endpoints": ["extract", "summarize", "sentiment", "seo", "analyze"],
        "features": [
            "Everything in Business",
            "Unlimited API calls",
            "SLA guarantee",
            "Custom endpoints",
            "White-label option",
            "Dedicated account manager",
        ],
        "overage_price": None,
    },
}


def get_tier_info(tier: str) -> dict:
    """Get information about a pricing tier."""
    return PRICING_TIERS.get(tier, PRICING_TIERS["free"])


def get_all_tiers() -> dict:
    """Get all pricing tiers."""
    return PRICING_TIERS
