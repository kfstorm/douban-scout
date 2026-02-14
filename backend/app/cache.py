"""Cache management for the movie explorer."""

import asyncio
import functools
import logging
import threading
from collections.abc import Callable
from typing import Any, ParamSpec, TypeVar, cast

from sqlalchemy.orm import Session

logger = logging.getLogger("douban.cache")

T = TypeVar("T")
P = ParamSpec("P")


class CacheManager:
    """Thread-safe in-memory cache manager."""

    def __init__(self) -> None:
        """Initialize cache and lock."""
        self._cache: dict[str, Any] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Any:
        """Get value from cache."""
        with self._lock:
            return self._cache.get(key)

    def set(self, key: str, value: Any) -> None:
        """Set value in cache."""
        with self._lock:
            self._cache[key] = value

    def clear(self) -> None:
        """Clear all cached entries."""
        with self._lock:
            logger.info("Clearing application cache")
            self._cache.clear()


cache_manager = CacheManager()


def cached(prefix: str) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Decorator to cache function results.

    Automatically ignores SQLAlchemy Session objects in the cache key.
    Supports both synchronous and asynchronous functions.
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
            key = _generate_key(prefix, args, kwargs)
            cached_val = cache_manager.get(key)
            if cached_val is not None:
                logger.debug(f"Cache hit (async): {key}")
                return cached_val

            logger.debug(f"Cache miss (async): {key}")
            result = await cast(Callable[P, Any], func)(*args, **kwargs)
            cache_manager.set(key, result)
            return result

        @functools.wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            key = _generate_key(prefix, args, kwargs)
            cached_val = cache_manager.get(key)
            if cached_val is not None:
                logger.debug(f"Cache hit: {key}")
                return cast(T, cached_val)

            logger.debug(f"Cache miss: {key}")
            result = func(*args, **kwargs)
            cache_manager.set(key, result)
            return result

        if asyncio.iscoroutinefunction(func):
            return cast(Callable[P, T], async_wrapper)
        return sync_wrapper

    return decorator


def _generate_key(prefix: str, args: Any, kwargs: Any) -> str:
    """Generate a cache key from arguments."""
    cache_parts = [prefix]

    # Process positional arguments
    for arg in args:
        # Skip Session objects and service instances
        if isinstance(arg, Session) or hasattr(arg, "get_movies") or hasattr(arg, "start_import"):
            continue
        cache_parts.append(str(arg))

    # Process keyword arguments
    for k in sorted(kwargs.keys()):
        if k == "db" or isinstance(kwargs[k], Session):
            continue
        cache_parts.append(f"{k}:{kwargs[k]}")

    return ":".join(cache_parts)
