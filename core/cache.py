"""
Jobper Core — Redis cache with in-memory LRU fallback
"""

from __future__ import annotations

import functools
import json
import logging
import time
from collections import OrderedDict
from threading import Lock
from typing import Optional

from config import Config

logger = logging.getLogger(__name__)


# =============================================================================
# IN-MEMORY LRU CACHE (fallback)
# =============================================================================


class _LRUCache:
    """Thread-safe LRU cache with TTL support."""

    def __init__(self, maxsize: int = 1000):
        self._data: OrderedDict[str, tuple[float, str]] = OrderedDict()  # key → (expires_at, value_json)
        self._maxsize = maxsize
        self._lock = Lock()

    def get(self, key: str) -> Optional[str]:
        with self._lock:
            item = self._data.get(key)
            if item is None:
                return None
            expires_at, value = item
            if expires_at < time.time():
                del self._data[key]
                return None
            self._data.move_to_end(key)
            return value

    def set(self, key: str, value: str, ttl: int = 300):
        with self._lock:
            self._data[key] = (time.time() + ttl, value)
            self._data.move_to_end(key)
            if len(self._data) > self._maxsize:
                self._data.popitem(last=False)

    def delete(self, key: str):
        with self._lock:
            self._data.pop(key, None)

    def delete_pattern(self, pattern: str):
        """Delete keys matching a simple prefix* pattern."""
        prefix = pattern.rstrip("*")
        with self._lock:
            to_delete = [k for k in self._data if k.startswith(prefix)]
            for k in to_delete:
                del self._data[k]


# =============================================================================
# CACHE CLIENT
# =============================================================================


_REDIS_RETRY_INTERVAL = 60  # seconds before attempting to reconnect after failure


class Cache:
    """Redis cache with automatic LRU in-memory fallback and auto-reconnect."""

    def __init__(self):
        self._redis = None
        self._memory = _LRUCache()
        self._last_failure: float = 0.0
        self._init_redis()

    def _init_redis(self):
        if not Config.REDIS_URL:
            return
        try:
            import redis

            self._redis = redis.from_url(Config.REDIS_URL, decode_responses=True)
            self._redis.ping()
            logger.info("Cache: Redis connected")
        except Exception as e:
            logger.warning(f"Cache: Redis unavailable, using in-memory: {e}")
            self._redis = None

    def _get_redis(self):
        """Return the Redis client, reconnecting if the retry interval has passed."""
        if self._redis is not None:
            return self._redis
        if Config.REDIS_URL and time.time() - self._last_failure >= _REDIS_RETRY_INTERVAL:
            self._init_redis()
        return self._redis

    def _on_failure(self):
        self._redis = None
        self._last_failure = time.time()

    def get(self, key: str) -> Optional[str]:
        r = self._get_redis()
        if r:
            try:
                return r.get(key)
            except Exception:
                self._on_failure()
        return self._memory.get(key)

    def set(self, key: str, value: str, ttl: int = 300):
        r = self._get_redis()
        if r:
            try:
                r.setex(key, ttl, value)
                return
            except Exception:
                self._on_failure()
        self._memory.set(key, value, ttl)

    def delete(self, key: str):
        r = self._get_redis()
        if r:
            try:
                r.delete(key)
                return
            except Exception:
                self._on_failure()
        self._memory.delete(key)

    def delete_pattern(self, pattern: str):
        r = self._get_redis()
        if r:
            try:
                keys = r.keys(pattern)
                if keys:
                    r.delete(*keys)
                return
            except Exception:
                self._on_failure()
        self._memory.delete_pattern(pattern)

    def get_json(self, key: str):
        raw = self.get(key)
        if raw:
            return json.loads(raw)
        return None

    def set_json(self, key: str, value, ttl: int = 300):
        self.set(key, json.dumps(value, default=str), ttl)

    def is_healthy(self) -> bool:
        if self._redis:
            try:
                return self._redis.ping()
            except Exception:
                return False
        return True  # in-memory always healthy


# Singleton
cache = Cache()


# =============================================================================
# DECORATOR
# =============================================================================


def cached(ttl: int = 300, key_pattern: str = ""):
    """Cache decorator. key_pattern can include {arg_name} placeholders."""

    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            if key_pattern:
                # Build cache key from pattern
                all_kwargs = {**kwargs}
                # Add positional args by parameter name
                import inspect

                sig = inspect.signature(fn)
                params = list(sig.parameters.keys())
                for i, arg in enumerate(args):
                    if i < len(params):
                        all_kwargs[params[i]] = arg
                cache_key = key_pattern.format(**all_kwargs)
            else:
                cache_key = f"{fn.__module__}.{fn.__qualname__}:{args}:{kwargs}"

            result = cache.get_json(cache_key)
            if result is not None:
                return result

            result = fn(*args, **kwargs)
            if result is not None:
                cache.set_json(cache_key, result, ttl)
            return result

        wrapper.invalidate = lambda **kw: cache.delete(key_pattern.format(**kw)) if key_pattern else None
        return wrapper

    return decorator
