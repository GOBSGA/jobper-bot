"""
Jobper Core — Celery async tasks with synchronous fallback
If Celery/Redis unavailable, tasks execute inline (blocking but functional).
"""

from __future__ import annotations

import functools
import logging

from config import Config

logger = logging.getLogger(__name__)

# =============================================================================
# CELERY INIT (optional)
# =============================================================================

_celery_app = None


def get_celery():
    global _celery_app
    if _celery_app is not None:
        return _celery_app

    if not Config.CELERY_BROKER_URL:
        logger.info("Celery: No broker URL, tasks will run synchronously")
        return None

    try:
        from celery import Celery

        _celery_app = Celery(
            "jobper",
            broker=Config.CELERY_BROKER_URL,
            backend=Config.CELERY_RESULT_BACKEND or None,
        )
        _celery_app.conf.update(
            task_serializer="json",
            accept_content=["json"],
            result_serializer="json",
            timezone="America/Bogota",
            task_soft_time_limit=300,
            task_time_limit=600,
        )
        # Test connection
        _celery_app.connection_for_read().ensure_connection(max_retries=1)
        logger.info("Celery: Connected to broker")
        return _celery_app
    except Exception as e:
        logger.warning(f"Celery: Unavailable, tasks will run synchronously: {e}")
        _celery_app = None
        return None


# =============================================================================
# ASYNC TASK DECORATOR
# =============================================================================


def async_task(fn):
    """
    Decorator: registers as Celery task if available, else runs inline.

    Usage:
        @async_task
        def send_email(to, subject, body):
            ...

        # Call:
        send_email.delay(to, subject, body)   # async if Celery available
        send_email(to, subject, body)          # always sync
    """
    celery = get_celery()

    if celery:
        # Register as Celery task
        celery_task = celery.task(name=f"jobper.{fn.__qualname__}")(fn)

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            return fn(*args, **kwargs)

        wrapper.delay = celery_task.delay
        wrapper.apply_async = celery_task.apply_async
        return wrapper
    else:
        # No Celery — sync execution

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            return fn(*args, **kwargs)

        def _sync_delay(*args, **kwargs):
            logger.debug(f"Celery unavailable, running {fn.__qualname__} synchronously")
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                logger.error(f"Task {fn.__qualname__} failed: {e}")
                return None

        wrapper.delay = _sync_delay
        wrapper.apply_async = lambda args=None, kwargs=None, **_: _sync_delay(*(args or []), **(kwargs or {}))
        return wrapper


# =============================================================================
# TASK DEFINITIONS
# =============================================================================


@async_task
def task_send_email(to: str, template: str, data: dict):
    """Send email via Resend."""
    from services.notifications import send_email

    return send_email(to, template, data)


@async_task
def task_send_push(user_id: int, title: str, body: str, url: str = ""):
    """Send web push notification."""
    from services.notifications import send_push

    return send_push(user_id, title, body, url)


@async_task
def task_index_contract(contract_id: int):
    """Index contract in Elasticsearch."""
    from search.engine import index_contract_by_id

    return index_contract_by_id(contract_id)


@async_task
def task_scrape_source(source_key: str):
    """Run scraper for a data source."""
    logger.info(f"Scraping source: {source_key}")
    try:
        from aggregator.scheduler import get_aggregation_scheduler

        scheduler = get_aggregation_scheduler()
        scheduler.fetch_source(source_key)
    except Exception as e:
        logger.error(f"Scrape failed for {source_key}: {e}")


@async_task
def task_analyze_contract(contract_id: int, user_id: int):
    """Run AI analysis on a contract for a user."""
    logger.info(f"Analyzing contract {contract_id} for user {user_id}")
    try:
        from intelligence.analyzer import analyze_contract

        return analyze_contract(contract_id, user_id)
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return None


@async_task
def task_send_daily_digest():
    """Send daily digest emails to eligible users."""
    logger.info("Starting daily digest job")
    try:
        from services.notifications import send_daily_digest

        result = send_daily_digest()
        logger.info(f"Daily digest completed: {result}")
        return result
    except Exception as e:
        logger.error(f"Daily digest failed: {e}")
        return None


@async_task
def task_run_ingestion():
    """Run contract ingestion from all SECOP sources."""
    logger.info("Starting ingestion job")
    try:
        from services.ingestion import ingest_all

        result = ingest_all()
        logger.info(f"Ingestion completed: {result}")
        return result
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        return None
