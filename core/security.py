"""
Jobper Core — Rate Limiter, HMAC Verification, Input Sanitization
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import re
import secrets
import time
from collections import OrderedDict
from threading import Lock

import bleach

from config import Config

logger = logging.getLogger(__name__)


# =============================================================================
# RATE LIMITER (Redis-backed, in-memory fallback)
# =============================================================================


class _InMemoryStore:
    """Thread-safe sliding-window counter with LRU eviction."""

    def __init__(self, maxsize: int = 10_000):
        self._data: OrderedDict[str, list[float]] = OrderedDict()
        self._maxsize = maxsize
        self._lock = Lock()

    def is_limited(self, key: str, max_requests: int, window_seconds: int = 60) -> bool:
        now = time.time()
        cutoff = now - window_seconds

        with self._lock:
            hits = self._data.get(key, [])
            hits = [t for t in hits if t > cutoff]

            if len(hits) >= max_requests:
                self._data[key] = hits
                return True

            hits.append(now)
            self._data[key] = hits
            self._data.move_to_end(key)

            if len(self._data) > self._maxsize:
                self._data.popitem(last=False)

            return False


class RateLimiter:
    """Rate limiter: uses Redis if available, else in-memory."""

    def __init__(self):
        self._redis = None
        self._memory = _InMemoryStore()
        self._init_redis()

    def _init_redis(self):
        if not Config.REDIS_URL:
            return
        try:
            import redis

            self._redis = redis.from_url(Config.REDIS_URL, decode_responses=True)
            self._redis.ping()
            logger.info("RateLimiter: Redis connected")
        except Exception as e:
            logger.warning(f"RateLimiter: Redis unavailable, using in-memory: {e}")
            self._redis = None

    def is_limited(self, key: str, max_requests: int, window: int = 60) -> bool:
        if self._redis:
            try:
                return self._check_redis(key, max_requests, window)
            except Exception:
                self._redis = None  # fallback
        return self._memory.is_limited(key, max_requests, window)

    def _check_redis(self, key: str, max_req: int, window: int) -> bool:
        pipe = self._redis.pipeline()
        now = time.time()
        redis_key = f"rl:{key}"

        pipe.zremrangebyscore(redis_key, 0, now - window)
        pipe.zcard(redis_key)
        pipe.zadd(redis_key, {str(now): now})
        pipe.expire(redis_key, window)

        results = pipe.execute()
        current_count = results[1]
        return current_count >= max_req


# Singleton
rate_limiter = RateLimiter()



# =============================================================================
# INPUT SANITIZATION
# =============================================================================

ALLOWED_TAGS: list[str] = []  # No HTML allowed
ALLOWED_ATTRS: dict = {}

# Patterns that could be used for ES injection
_ES_DANGEROUS = re.compile(r'[{}\[\]"\\]')


def sanitize_html(text: str) -> str:
    """Strip all HTML tags."""
    if not text:
        return text
    return bleach.clean(text, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True)


def sanitize_search_query(text: str) -> str:
    """Remove characters that could be used for Elasticsearch injection."""
    if not text:
        return text
    cleaned = _ES_DANGEROUS.sub(" ", text)
    return " ".join(cleaned.split())[:500]  # max 500 chars


# =============================================================================
# TOKEN GENERATION
# =============================================================================


def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure URL-safe token."""
    return secrets.token_urlsafe(length)


def hash_token(token: str) -> str:
    """SHA-256 hash a token for storage (never store plaintext)."""
    return hashlib.sha256(token.encode()).hexdigest()
