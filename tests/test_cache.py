"""Tests for the caching service (in-memory fallback)."""

from __future__ import annotations

import pytest

from app.services.cache import _cache_key, get_cached, is_redis_connected, set_cached


class TestCacheService:
    """Tests for the in-memory cache (no Redis required)."""

    @pytest.mark.asyncio
    async def test_cache_miss_returns_none(self):
        result = await get_cached("test", "nonexistent-key-12345")
        assert result is None

    @pytest.mark.asyncio
    async def test_cache_set_and_get(self):
        test_data = {"title": "Test", "word_count": 42}
        await set_cached("test", "cache-roundtrip-key", test_data)
        result = await get_cached("test", "cache-roundtrip-key")
        assert result is not None
        assert result["title"] == "Test"
        assert result["word_count"] == 42

    @pytest.mark.asyncio
    async def test_cache_different_prefixes_are_isolated(self):
        await set_cached("prefix_a", "same-key", {"value": "a"})
        await set_cached("prefix_b", "same-key", {"value": "b"})
        result_a = await get_cached("prefix_a", "same-key")
        result_b = await get_cached("prefix_b", "same-key")
        assert result_a["value"] == "a"
        assert result_b["value"] == "b"

    def test_cache_key_deterministic(self):
        key1 = _cache_key("extract", "https://example.com")
        key2 = _cache_key("extract", "https://example.com")
        assert key1 == key2

    def test_cache_key_varies_by_prefix(self):
        key1 = _cache_key("extract", "https://example.com")
        key2 = _cache_key("seo", "https://example.com")
        assert key1 != key2

    def test_cache_key_varies_by_data(self):
        key1 = _cache_key("extract", "https://example.com")
        key2 = _cache_key("extract", "https://example.com/page2")
        assert key1 != key2

    def test_redis_not_connected_by_default(self):
        # Without REDIS_URL set, Redis should not be connected
        assert is_redis_connected() is False
