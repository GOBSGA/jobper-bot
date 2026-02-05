"""
Jobper Services — Contract Matching Engine
Pure Python matching (no external AI APIs) = $0 cost per user.

Score algorithm:
  - Keyword match (50%): how many user keywords appear in contract title+description
  - Sector match (25%): user sector matches contract category/entity keywords
  - Recency bonus (25%): newer contracts score higher
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta

from core.cache import cache
from core.database import UnitOfWork, User, Contract

logger = logging.getLogger(__name__)


def calculate_match_score(user: User, contract: Contract) -> int:
    """
    Calculate 0-100 match score between a user profile and a contract.

    Score breakdown:
    - Keyword match: 40 points max
    - Sector match: 20 points max
    - Budget match: 15 points max (bonus if contract amount is within user's budget)
    - Recency bonus: 15 points max
    - Location bonus: 10 points max (if user's city matches contract entity/location)
    """
    if not user.keywords and not user.sector:
        return 50  # No profile = neutral score

    score = 0.0
    now = datetime.utcnow()

    # --- Penalty for expired contracts ---
    if contract.deadline and contract.deadline < now:
        return 0  # Don't show expired contracts

    # --- Keyword match (40 points max) ---
    user_keywords = user.keywords or []
    if user_keywords:
        contract_text = f"{contract.title or ''} {contract.description or ''}".lower()
        matches = sum(1 for kw in user_keywords if kw.lower() in contract_text)
        keyword_ratio = matches / len(user_keywords) if user_keywords else 0
        score += keyword_ratio * 40

    # --- Sector match (20 points max) ---
    if user.sector:
        from config import Config
        sector_keywords = []
        sector_key = user.sector.lower()
        for key, industry in Config.INDUSTRIES.items():
            if key == sector_key or sector_key in industry["name"].lower():
                sector_keywords = industry["keywords"]
                break

        if sector_keywords:
            contract_text = f"{contract.title or ''} {contract.description or ''} {contract.entity or ''}".lower()
            sector_matches = sum(1 for kw in sector_keywords if kw in contract_text)
            sector_ratio = min(sector_matches / 3, 1.0)  # 3+ keyword matches = full score
            score += sector_ratio * 20
        else:
            # Direct sector text match
            contract_text = f"{contract.title or ''} {contract.description or ''}".lower()
            if user.sector.lower() in contract_text:
                score += 20

    # --- Budget match (15 points max) ---
    if contract.amount and contract.amount > 0:
        budget_min = user.budget_min or 0
        budget_max = user.budget_max or float('inf')

        if budget_min <= contract.amount <= budget_max:
            score += 15  # Full points if within range
        elif contract.amount < budget_min:
            # Partial points if slightly under budget (might still be interesting)
            ratio = contract.amount / budget_min if budget_min > 0 else 0
            if ratio > 0.5:  # At least 50% of minimum budget
                score += 7
        elif budget_max != float('inf') and contract.amount > budget_max:
            # Partial points if slightly over budget (might still be interesting)
            ratio = budget_max / contract.amount if contract.amount > 0 else 0
            if ratio > 0.5:  # No more than 2x the maximum budget
                score += 5

    # --- Location match (10 points max) ---
    if user.city:
        user_city = user.city.lower()
        # Check entity name (often includes location like "Alcaldía de Medellín")
        entity_text = f"{contract.entity or ''}".lower()
        if user_city in entity_text:
            score += 10
        # Also check description for location mentions
        elif user_city in f"{contract.description or ''}".lower():
            score += 5

    # --- Recency bonus (15 points max) ---
    if contract.publication_date:
        days_old = (now - contract.publication_date).days
        if days_old <= 1:
            score += 15
        elif days_old <= 3:
            score += 12
        elif days_old <= 7:
            score += 8
        elif days_old <= 14:
            score += 4
        elif days_old <= 30:
            score += 2

    return min(100, max(0, round(score)))


def get_matched_contracts(user_id: int, min_score: int = 0, limit: int = 50, days_back: int = 30) -> list[dict]:
    """Get contracts matched and scored for a specific user."""
    cache_key = f"matched:{user_id}:{min_score}:{limit}"
    cached_result = cache.get_json(cache_key)
    if cached_result is not None:
        return cached_result

    result = _compute_matched_contracts(user_id, min_score, limit, days_back)
    cache.set_json(cache_key, result, ttl=600)  # 10 min cache
    return result


def _compute_matched_contracts(user_id: int, min_score: int, limit: int, days_back: int) -> list[dict]:
    with UnitOfWork() as uow:
        user = uow.users.get(user_id)
        if not user:
            return []

        now = datetime.utcnow()
        since = now - timedelta(days=days_back)

        # Build query with pre-filters for efficiency
        query = uow.session.query(Contract).filter(
            Contract.publication_date >= since,
            # Exclude expired contracts
            (Contract.deadline.is_(None)) | (Contract.deadline >= now),
        )

        # Pre-filter by budget if user has it set (query optimization)
        if user.budget_min and user.budget_min > 0:
            # Allow contracts with no amount (don't filter them out) or amount >= 50% of min
            query = query.filter(
                (Contract.amount.is_(None)) | (Contract.amount >= user.budget_min * 0.5)
            )
        if user.budget_max and user.budget_max > 0:
            # Allow contracts with no amount or amount <= 2x of max
            query = query.filter(
                (Contract.amount.is_(None)) | (Contract.amount <= user.budget_max * 2)
            )

        contracts = query.order_by(Contract.publication_date.desc()).limit(1000).all()

        scored = []
        for c in contracts:
            score = calculate_match_score(user, c)
            if score >= min_score:
                scored.append({
                    "id": c.id,
                    "title": c.title,
                    "description": (c.description or "")[:200],
                    "entity": c.entity,
                    "amount": c.amount,
                    "currency": c.currency,
                    "source": c.source,
                    "url": c.url,
                    "deadline": c.deadline.isoformat() if c.deadline else None,
                    "publication_date": c.publication_date.isoformat() if c.publication_date else None,
                    "match_score": score,
                })

        scored.sort(key=lambda x: x["match_score"], reverse=True)
        return scored[:limit]


def get_alerts(user_id: int, hours: int = 24) -> dict:
    """Get new contract alerts for a user (contracts from last N hours with high scores)."""
    with UnitOfWork() as uow:
        user = uow.users.get(user_id)
        if not user:
            return {"contracts": [], "count": 0}

        # Check free tier limits (3 alerts/week)
        from config import Config
        from core.middleware import PLAN_ORDER
        user_plan = user.plan or "free"
        is_free_tier = PLAN_ORDER.get(user_plan, 0) < PLAN_ORDER.get("alertas", 2)

        if is_free_tier:
            weekly_limit = Config.PLANS.get("free", {}).get("limits", {}).get("alerts_per_week", 3)
            now = datetime.utcnow()

            # Reset weekly counter if new week started (Monday)
            week_start = now - timedelta(days=now.weekday())  # Monday of current week
            week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)

            if not user.alerts_week_start or user.alerts_week_start < week_start:
                user.alerts_week_start = week_start
                user.alerts_sent_this_week = 0
                uow.commit()

            # Check if user hit the weekly limit
            alerts_remaining = max(0, weekly_limit - (user.alerts_sent_this_week or 0))
            if alerts_remaining == 0:
                return {
                    "contracts": [],
                    "count": 0,
                    "limit_reached": True,
                    "weekly_limit": weekly_limit,
                    "alerts_used": user.alerts_sent_this_week,
                    "upgrade_required": "alertas",
                }

        since = datetime.utcnow() - timedelta(hours=hours)
        contracts = uow.session.query(Contract).filter(
            Contract.publication_date >= since
        ).order_by(Contract.publication_date.desc()).all()

        alerts = []
        for c in contracts:
            score = calculate_match_score(user, c)
            if score >= 60:
                alerts.append({
                    "id": c.id,
                    "title": c.title,
                    "entity": c.entity,
                    "amount": c.amount,
                    "source": c.source,
                    "url": c.url,
                    "deadline": c.deadline.isoformat() if c.deadline else None,
                    "publication_date": c.publication_date.isoformat() if c.publication_date else None,
                    "match_score": score,
                })

        alerts.sort(key=lambda x: x["match_score"], reverse=True)

        # Apply free tier limit
        if is_free_tier:
            alerts = alerts[:alerts_remaining]
            # Update counter
            if alerts:
                user.alerts_sent_this_week = (user.alerts_sent_this_week or 0) + len(alerts)
                uow.commit()

        response = {
            "contracts": alerts,
            "count": len(alerts),
            "since": since.isoformat(),
        }

        # Add limit info for free tier
        if is_free_tier:
            response["weekly_limit"] = Config.PLANS.get("free", {}).get("limits", {}).get("alerts_per_week", 3)
            response["alerts_used"] = user.alerts_sent_this_week or 0

        return response


def get_market_stats(user_id: int) -> dict:
    """Get market statistics relevant to the user's sector."""
    cache_key = f"market_stats:{user_id}"
    cached_result = cache.get_json(cache_key)
    if cached_result is not None:
        return cached_result

    result = _compute_market_stats(user_id)
    cache.set_json(cache_key, result, ttl=900)  # 15 min cache
    return result


def _compute_market_stats(user_id: int) -> dict:
    with UnitOfWork() as uow:
        user = uow.users.get(user_id)

        now = datetime.utcnow()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        last_30d = now - timedelta(days=30)

        total = uow.session.query(Contract).count()
        new_24h = uow.session.query(Contract).filter(Contract.publication_date >= last_24h).count()
        new_7d = uow.session.query(Contract).filter(Contract.publication_date >= last_7d).count()
        new_30d = uow.session.query(Contract).filter(Contract.publication_date >= last_30d).count()

        # Total value of recent contracts
        from sqlalchemy import func
        total_value = uow.session.query(func.sum(Contract.amount)).filter(
            Contract.publication_date >= last_30d,
            Contract.amount.isnot(None),
        ).scalar() or 0

        # Sector-specific stats if user has sector
        sector_count = 0
        sector_value = 0
        if user and user.sector:
            from config import Config
            sector_keywords = []
            for key, industry in Config.INDUSTRIES.items():
                if key == user.sector.lower() or user.sector.lower() in industry["name"].lower():
                    sector_keywords = industry["keywords"][:5]
                    break

            if sector_keywords:
                for kw in sector_keywords:
                    pattern = f"%{kw}%"
                    q = uow.session.query(Contract).filter(
                        Contract.publication_date >= last_30d,
                        (Contract.title.ilike(pattern) | Contract.description.ilike(pattern))
                    )
                    sector_count += q.count()

                sector_value_q = uow.session.query(func.sum(Contract.amount)).filter(
                    Contract.publication_date >= last_30d,
                    Contract.amount.isnot(None),
                    Contract.title.ilike(f"%{sector_keywords[0]}%")
                ).scalar() or 0
                sector_value = sector_value_q

        return {
            "total_contracts": total,
            "new_last_24h": new_24h,
            "new_last_7d": new_7d,
            "new_last_30d": new_30d,
            "total_value_30d": total_value,
            "sector_contracts_30d": sector_count,
            "sector_value_30d": sector_value,
        }


def notify_high_priority_matches(new_count: int):
    """After ingestion, find high-priority matches and queue notifications."""
    logger.info(f"Checking high-priority matches for {new_count} new contracts...")

    with UnitOfWork() as uow:
        # Get users with notifications enabled
        users = uow.users.get_active_with_notifications()

        # Get contracts from last hour (just ingested)
        since = datetime.utcnow() - timedelta(hours=1)
        new_contracts = uow.session.query(Contract).filter(
            Contract.publication_date >= since
        ).all()

        if not new_contracts:
            return

        for user in users:
            for contract in new_contracts:
                score = calculate_match_score(user, contract)
                if score >= 85:
                    _queue_push_notification(user, contract, score)


def _queue_push_notification(user: User, contract: Contract, score: int):
    """Queue a push notification for a high-priority match."""
    logger.info(f"High-priority match: user={user.email} contract={contract.id} score={score}")
    # Push notification will be sent via the existing push infrastructure
    try:
        from services.notifications import send_push
        send_push(
            user.id,
            title=f"Nuevo contrato {score}% compatible",
            body=f"{contract.title[:80]} - {contract.entity or 'Sin entidad'}",
            url=f"/contracts/{contract.id}",
        )
    except Exception as e:
        logger.error(f"Push notification failed for user {user.email}: {e}")
