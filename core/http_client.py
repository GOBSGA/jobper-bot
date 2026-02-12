"""
HTTP client wrapper with timeouts, retries, and error handling.
"""

import logging
import time
from typing import Any, Dict, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

# Default timeouts (connect, read) in seconds
DEFAULT_TIMEOUT = (10, 30)  # 10s connect, 30s read
SHORT_TIMEOUT = (5, 15)  # For quick APIs
LONG_TIMEOUT = (15, 60)  # For slow APIs (scraping)


class TimeoutHTTPAdapter(HTTPAdapter):
    """HTTPAdapter with default timeout."""

    def __init__(self, timeout=DEFAULT_TIMEOUT, *args, **kwargs):
        self.timeout = timeout
        super().__init__(*args, **kwargs)

    def send(self, request, **kwargs):
        if kwargs.get("timeout") is None:
            kwargs["timeout"] = self.timeout
        return super().send(request, **kwargs)


def get_session(
    max_retries: int = 3, timeout: tuple = DEFAULT_TIMEOUT, backoff_factor: float = 0.3
) -> requests.Session:
    """
    Create a requests Session with retries and timeout.

    Args:
        max_retries: Number of retries for failed requests
        timeout: (connect_timeout, read_timeout) in seconds
        backoff_factor: Backoff factor for retries (0.3 = 0.3s, 0.6s, 1.2s, ...)

    Returns:
        Configured Session object
    """
    session = requests.Session()

    # Retry strategy
    retry_strategy = Retry(
        total=max_retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],  # Retry on these HTTP codes
        allowed_methods=["GET", "POST"],  # Retry these methods
    )

    # Mount adapter with retries and timeout
    adapter = TimeoutHTTPAdapter(timeout=timeout, max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session


def safe_request(
    method: str, url: str, timeout: tuple = DEFAULT_TIMEOUT, max_retries: int = 3, **kwargs
) -> Optional[requests.Response]:
    """
    Make an HTTP request with timeout, retries, and error handling.

    Args:
        method: HTTP method (GET, POST, etc.)
        url: URL to request
        timeout: (connect, read) timeout in seconds
        max_retries: Number of retries
        **kwargs: Additional arguments for requests

    Returns:
        Response object or None if request failed
    """
    session = get_session(max_retries=max_retries, timeout=timeout)

    try:
        start = time.time()
        response = session.request(method, url, **kwargs)
        elapsed = time.time() - start

        logger.debug(f"{method} {url} -> {response.status_code} ({elapsed:.2f}s)")

        # Raise for 4xx/5xx status codes
        response.raise_for_status()

        return response

    except requests.exceptions.Timeout as e:
        logger.error(f"Request timeout after {timeout}s: {method} {url} - {e}")
        return None

    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error: {method} {url} - {e}")
        return None

    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error {response.status_code}: {method} {url} - {e}")
        return None

    except Exception as e:
        logger.error(f"Unexpected error: {method} {url} - {e}")
        return None


def safe_get(url: str, **kwargs) -> Optional[requests.Response]:
    """GET request with timeout and error handling."""
    return safe_request("GET", url, **kwargs)


def safe_post(url: str, **kwargs) -> Optional[requests.Response]:
    """POST request with timeout and error handling."""
    return safe_request("POST", url, **kwargs)
