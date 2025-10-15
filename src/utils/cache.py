"""Caching utilities for Google Workspace API responses."""

import asyncio
import time
from typing import Any, Dict, Optional, Tuple
from cachetools import TTLCache
from .logger import setup_logger

logger = setup_logger(__name__)


class AsyncCache:
    """Async-safe cache with TTL support."""

    def __init__(self, maxsize: int = 1000, ttl: int = 300):
        """Initialize cache.

        Args:
            maxsize: Maximum number of cached items
            ttl: Time-to-live in seconds
        """
        self._cache: TTLCache = TTLCache(maxsize=maxsize, ttl=ttl)
        self._lock = asyncio.Lock()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0
        }

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        async with self._lock:
            try:
                value = self._cache[key]
                self._stats["hits"] += 1
                logger.debug(f"Cache hit for key: {key}")
                return value
            except KeyError:
                self._stats["misses"] += 1
                logger.debug(f"Cache miss for key: {key}")
                return None

    async def set(self, key: str, value: Any) -> None:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
        """
        async with self._lock:
            old_size = len(self._cache)
            self._cache[key] = value
            new_size = len(self._cache)

            if new_size < old_size:
                self._stats["evictions"] += 1

            logger.debug(f"Cached value for key: {key}")

    async def delete(self, key: str) -> bool:
        """Delete value from cache.

        Args:
            key: Cache key

        Returns:
            True if key existed, False otherwise
        """
        async with self._lock:
            try:
                del self._cache[key]
                logger.debug(f"Deleted cache key: {key}")
                return True
            except KeyError:
                return False

    async def clear(self) -> None:
        """Clear all cached values."""
        async with self._lock:
            self._cache.clear()
            logger.info("Cache cleared")

    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics.

        Returns:
            Dictionary with hit/miss/eviction counts
        """
        total = self._stats["hits"] + self._stats["misses"]
        hit_rate = self._stats["hits"] / total if total > 0 else 0.0

        return {
            **self._stats,
            "size": len(self._cache),
            "hit_rate": hit_rate
        }


# Global cache instances per service
_caches: Dict[str, AsyncCache] = {}


def get_cache(service: str, **kwargs) -> AsyncCache:
    """Get or create cache for a service.

    Args:
        service: Service name
        **kwargs: AsyncCache initialization parameters

    Returns:
        AsyncCache instance
    """
    if service not in _caches:
        _caches[service] = AsyncCache(**kwargs)
    return _caches[service]


def cache_key(*args, **kwargs) -> str:
    """Generate cache key from arguments.

    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments

    Returns:
        String cache key
    """
    parts = [str(arg) for arg in args]
    parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
    return ":".join(parts)


async def cached_call(
    service: str,
    key: str,
    func,
    *args,
    ttl: Optional[int] = None,
    **kwargs
) -> Any:
    """Execute function with caching.

    Args:
        service: Service name for cache selection
        key: Cache key
        func: Function to execute
        *args: Positional arguments for func
        ttl: Custom TTL for this cache entry
        **kwargs: Keyword arguments for func

    Returns:
        Result of func execution (from cache or fresh)
    """
    cache = get_cache(service, ttl=ttl) if ttl else get_cache(service)

    # Check cache
    cached_value = await cache.get(key)
    if cached_value is not None:
        return cached_value

    # Execute function
    if asyncio.iscoroutinefunction(func):
        result = await func(*args, **kwargs)
    else:
        result = func(*args, **kwargs)

    # Cache result
    await cache.set(key, result)
    return result
