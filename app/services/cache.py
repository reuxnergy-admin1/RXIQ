"""In-memory + optional Redis caching service."""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Optional

from cachetools import TTLCache

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# In-memory fallback cache (1000 items, configurable TTL)
_memory_cache = TTLCache(maxsize=1000, ttl=settings.cache_ttl)

# Redis client (lazy init)
_redis_client = None
_redis_available = False


async def init_redis() -> bool:
    """Initialize Redis connection. Returns True if successful."""
    global _redis_client, _redis_available

    if not settings.redis_url:
        logger.info("No REDIS_URL configured. Using in-memory cache only.")
        return False

    try:
        import redis.asyncio as aioredis

        _redis_client = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=5,
        )
        await _redis_client.ping()
        _redis_available = True
        logger.info("Redis connected successfully.")
        return True
    except Exception as e:
        logger.warning(
            f"Redis connection failed: {e}. Falling back to in-memory cache."
        )
        _redis_available = False
        return False


async def close_redis():
    """Gracefully close Redis connection."""
    global _redis_client, _redis_available
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
        _redis_available = False


def _cache_key(prefix: str, data: str) -> str:
    """Generate a cache key from prefix and data."""
    h = hashlib.sha256(data.encode()).hexdigest()[:16]
    return f"ciq:{prefix}:{h}"


async def get_cached(prefix: str, key_data: str) -> Optional[dict[str, Any]]:
    """Get a cached value by prefix and key data."""
    key = _cache_key(prefix, key_data)

    # Try Redis first
    if _redis_available and _redis_client:
        try:
            value = await _redis_client.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            logger.warning(f"Redis GET failed: {e}")

    # Fallback to memory cache
    value = _memory_cache.get(key)
    if value:
        return value

    return None


async def set_cached(
    prefix: str, key_data: str, value: dict[str, Any], ttl: Optional[int] = None
) -> None:
    """Set a cached value."""
    key = _cache_key(prefix, key_data)
    ttl = ttl or settings.cache_ttl

    # Store in memory cache always
    _memory_cache[key] = value

    # Also store in Redis if available
    if _redis_available and _redis_client:
        try:
            await _redis_client.setex(key, ttl, json.dumps(value, default=str))
        except Exception as e:
            logger.warning(f"Redis SET failed: {e}")


def is_redis_connected() -> bool:
    """Check if Redis is connected."""
    return _redis_available
