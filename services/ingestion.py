"""
Jobper Services — Contract Ingestion Pipeline
Scrapes SECOP I & II sources and persists new contracts to the database.
Supports multi-dataset ingestion with aggressive first-run loading.
"""
from __future__ import annotations

import logging
import threading
from datetime import datetime

from core.database import UnitOfWork, Contract, DataSource
from scrapers.base import ContractData

logger = logging.getLogger(__name__)

_ingestion_lock = threading.Lock()


def get_contract_count() -> int:
    """Get total number of contracts in the database."""
    try:
        with UnitOfWork() as uow:
            return uow.session.query(Contract).count()
    except Exception:
        return 0


def ingest_secop(days_back: int = 7, dataset_key: str = "procesos") -> dict:
    """Fetch contracts from a specific SECOP dataset and persist new ones."""
    from scrapers.secop import SecopScraper

    scraper = SecopScraper(dataset_key=dataset_key)
    raw = scraper.fetch_contracts(days_back=days_back)
    return _persist_contracts(raw, f"secop_{dataset_key}")


def ingest_all(days_back: int = 7) -> dict:
    """Run all SECOP scrapers and persist results."""
    results = {}

    # Check if this is a first run (low contract count = aggressive ingestion)
    count = get_contract_count()
    if count < 500:
        days_back = max(days_back, 365)
        logger.info(f"Low contract count ({count}), using aggressive days_back={days_back}")

    # Scrape all SECOP datasets
    for dataset_key in ["procesos", "adjudicados", "secop1", "ejecucion", "tvec"]:
        try:
            results[dataset_key] = ingest_secop(days_back=days_back, dataset_key=dataset_key)
        except Exception as e:
            logger.error(f"[{dataset_key}] Ingestion failed: {e}")
            results[dataset_key] = {"new": 0, "skipped": 0, "errors": 1}

    total_new = sum(r.get("new", 0) for r in results.values())
    total_skipped = sum(r.get("skipped", 0) for r in results.values())
    total_errors = sum(r.get("errors", 0) for r in results.values())

    logger.info(
        f"Ingestion complete: {total_new} new, {total_skipped} skipped, {total_errors} errors"
    )

    # Trigger post-ingestion notifications if we got new contracts
    if total_new > 0:
        try:
            _post_ingestion_notify(total_new)
        except Exception as e:
            logger.error(f"Post-ingestion notification failed: {e}")

    return {
        "sources": results,
        "total_new": total_new,
        "total_skipped": total_skipped,
        "total_errors": total_errors,
    }


def _post_ingestion_notify(new_count: int):
    """After ingestion, check for high-priority matches and notify users."""
    from services.matching import notify_high_priority_matches
    notify_high_priority_matches(new_count)


def _persist_contracts(contracts: list[ContractData], source_key: str) -> dict:
    """Persist a list of ContractData to the database, skipping duplicates."""
    if not _ingestion_lock.acquire(blocking=False):
        logger.warning("Ingestion already running, skipping")
        return {"new": 0, "skipped": 0, "errors": 0, "locked": True}

    new_count = 0
    skip_count = 0
    error_count = 0

    try:
        with UnitOfWork() as uow:
            for cd in contracts:
                try:
                    existing = uow.contracts.get_by_external_id(cd.external_id)
                    if existing:
                        skip_count += 1
                        continue

                    contract = Contract(
                        external_id=cd.external_id,
                        title=cd.title,
                        description=cd.description,
                        entity=cd.entity,
                        amount=cd.amount,
                        currency=cd.currency,
                        country=cd.country,
                        source=cd.source,
                        source_type="government" if "SECOP" in cd.source else "private",
                        url=cd.url,
                        publication_date=cd.publication_date,
                        deadline=cd.deadline,
                        raw_data=cd.raw_data,
                    )
                    uow.contracts.create(contract)
                    new_count += 1
                except Exception as e:
                    logger.error(f"Error persisting contract {cd.external_id}: {e}")
                    error_count += 1

            uow.commit()

            # Update data source last fetch timestamp
            ds = uow.session.query(DataSource).filter(
                DataSource.source_key == source_key
            ).first()
            if ds:
                ds.last_successful_fetch = datetime.utcnow()
                ds.error_count = 0
                uow.commit()

        logger.info(
            f"[{source_key}] Ingested: {new_count} new, {skip_count} skipped, {error_count} errors"
        )
    except Exception as e:
        logger.error(f"[{source_key}] Ingestion failed: {e}")
        error_count += 1
    finally:
        _ingestion_lock.release()

    return {"new": new_count, "skipped": skip_count, "errors": error_count}


def check_expiring_subscriptions():
    """Send reminder emails to users whose trial or subscription expires in 3 days."""
    from datetime import timedelta
    from core.database import User, Subscription
    from core.tasks import task_send_email

    now = datetime.utcnow()
    remind_window_start = now + timedelta(days=2)
    remind_window_end = now + timedelta(days=4)

    try:
        with UnitOfWork() as uow:
            # Trial users expiring in ~3 days
            expiring_trials = uow.session.query(User).filter(
                User.plan == "trial",
                User.trial_ends_at.between(remind_window_start, remind_window_end),
            ).all()
            for user in expiring_trials:
                days_left = max(0, (user.trial_ends_at - now).days)
                task_send_email.delay(user.email, "trial_expiring", {"days_left": days_left})
                logger.info(f"Trial reminder sent to {user.email} ({days_left}d left)")

            # Paid subscriptions expiring in ~3 days
            expiring_subs = uow.session.query(Subscription).filter(
                Subscription.status == "active",
                Subscription.ends_at.between(remind_window_start, remind_window_end),
            ).all()
            for sub in expiring_subs:
                user = uow.users.get(sub.user_id)
                if user:
                    days_left = max(0, (sub.ends_at - now).days)
                    task_send_email.delay(
                        user.email, "subscription_expiring",
                        {"days_left": days_left, "plan": sub.plan},
                    )
                    logger.info(f"Renewal reminder sent to {user.email} ({days_left}d left)")

            # Expire overdue subscriptions
            overdue = uow.session.query(Subscription).filter(
                Subscription.status == "active",
                Subscription.ends_at < now,
            ).all()
            for sub in overdue:
                sub.status = "expired"
                user = uow.users.get(sub.user_id)
                if user:
                    user.plan = "free"
                    logger.info(f"Subscription expired for user {user.email}")
            if overdue:
                uow.commit()

            # Expire overdue trials
            expired_trials = uow.session.query(User).filter(
                User.plan == "trial",
                User.trial_ends_at < now,
            ).all()
            for user in expired_trials:
                user.plan = "expired"
                logger.info(f"Trial expired for user {user.email}")
            if expired_trials:
                uow.commit()

    except Exception as e:
        logger.error(f"Expiration check failed: {e}")


def run_ingestion_async(days_back: int = 7):
    """Run ingestion in a background thread (non-blocking)."""
    thread = threading.Thread(
        target=ingest_all,
        args=(days_back,),
        daemon=True,
        name="ingestion-worker",
    )
    thread.start()
    logger.info("Background ingestion started")
