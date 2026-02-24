"""
Jobper Services — Contract Matching Engine v2.0
Hybrid matching: Keywords + Semantic (embeddings) for Silicon Valley-level recommendations.

Score algorithm:
  - Semantic match (35%): embedding similarity between user profile and contract
  - Keyword match (25%): how many user keywords appear in contract
  - Sector match (15%): user sector matches contract category
  - Budget match (15%): contract amount within user's budget range
  - Recency bonus (10%): newer contracts score higher
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional

import numpy as np

from core.cache import cache
from core.database import Contract, UnitOfWork, User

logger = logging.getLogger(__name__)

# =============================================================================
# SEMANTIC MATCHING (Lazy-loaded singleton)
# =============================================================================

_semantic_matcher = None
_semantic_load_attempts = 0
_MAX_LOAD_ATTEMPTS = 3


def get_semantic_matcher():
    """Lazy-load the semantic matcher. Retries up to 3 times before giving up."""
    global _semantic_matcher, _semantic_load_attempts

    if _semantic_matcher is not None:
        return _semantic_matcher

    if _semantic_load_attempts >= _MAX_LOAD_ATTEMPTS:
        return None

    _semantic_load_attempts += 1
    try:
        from nlp.semantic_search import SemanticMatcher

        _semantic_matcher = SemanticMatcher()
        _semantic_load_attempts = 0  # reset on success
        logger.info("Semantic matcher loaded successfully")
    except Exception as e:
        logger.warning(
            f"Could not load semantic matcher (attempt {_semantic_load_attempts}/{_MAX_LOAD_ATTEMPTS}): {e}. "
            "Falling back to keyword-only matching."
        )
        return None

    return _semantic_matcher


def compute_user_embedding(user: User) -> Optional[np.ndarray]:
    """Compute embedding for user profile."""
    matcher = get_semantic_matcher()
    if not matcher:
        return None

    try:
        # Build user dict for semantic matcher
        user_dict = {
            "industry": user.sector,
            "include_keywords": user.keywords or [],
        }
        return matcher.compute_user_profile_embedding(user_dict, save_to_db=False)
    except Exception as e:
        logger.warning(f"Error computing user embedding: {e}")
        return None


def compute_contract_embedding(contract: Contract) -> Optional[np.ndarray]:
    """Compute embedding for a contract."""
    matcher = get_semantic_matcher()
    if not matcher:
        return None

    try:
        contract_dict = {
            "title": contract.title or "",
            "description": contract.description or "",
            "entity": contract.entity or "",
        }
        return matcher.compute_contract_embedding(contract_dict, save_to_db=False)
    except Exception as e:
        logger.debug(f"Error computing contract embedding: {e}")
        return None


def semantic_similarity(user_embedding: np.ndarray, contract_embedding: np.ndarray) -> float:
    """Calculate cosine similarity between user and contract embeddings."""
    if user_embedding is None or contract_embedding is None:
        return 0.0
    try:
        # Dot product of normalized vectors = cosine similarity
        return float(np.dot(user_embedding, contract_embedding))
    except Exception:
        return 0.0


def calculate_match_score(
    user: User,
    contract: Contract,
    user_embedding: Optional[np.ndarray] = None,
    contract_embedding: Optional[np.ndarray] = None,
) -> int:
    """
    Calculate 0-100 match score between a user profile and a contract.

    Score breakdown (Silicon Valley v2.0):
    - Semantic match: 35 points max (NEW - embedding similarity)
    - Keyword match: 25 points max
    - Sector match: 15 points max
    - Budget match: 15 points max
    - Recency bonus: 10 points max
    """
    if not user.keywords and not user.sector:
        return 50  # No profile = neutral score

    score = 0.0
    now = datetime.utcnow()

    # --- Penalty for expired contracts ---
    if contract.deadline and contract.deadline < now:
        return 0  # Don't show expired contracts

    # --- SEMANTIC MATCH (35 points max) - NEW ---
    if user_embedding is not None:
        # Compute contract embedding if not provided
        if contract_embedding is None:
            contract_embedding = compute_contract_embedding(contract)

        if contract_embedding is not None:
            similarity = semantic_similarity(user_embedding, contract_embedding)
            # Similarity is typically 0-1 for related content
            # Scale to 35 points, with bonus for high similarity
            if similarity >= 0.7:
                score += 35  # Excellent match
            elif similarity >= 0.5:
                score += similarity * 50  # 25-35 points
            elif similarity >= 0.3:
                score += similarity * 40  # 12-20 points
            else:
                score += similarity * 20  # 0-6 points

    # --- Keyword match (25 points max) ---
    user_keywords = user.keywords or []
    if user_keywords:
        contract_text = f"{contract.title or ''} {contract.description or ''}".lower()
        matches = sum(1 for kw in user_keywords if kw.lower() in contract_text)
        keyword_ratio = matches / len(user_keywords) if user_keywords else 0
        score += keyword_ratio * 25

    # --- Sector match (15 points max) ---
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
            sector_ratio = min(sector_matches / 3, 1.0)
            score += sector_ratio * 15
        else:
            contract_text = f"{contract.title or ''} {contract.description or ''}".lower()
            if user.sector.lower() in contract_text:
                score += 15

    # --- Budget match (15 points max) ---
    if contract.amount and contract.amount > 0:
        budget_min = user.budget_min or 0
        budget_max = user.budget_max or float("inf")

        if budget_min <= contract.amount <= budget_max:
            score += 15
        elif contract.amount < budget_min:
            ratio = contract.amount / budget_min if budget_min > 0 else 0
            if ratio > 0.5:
                score += 7
        elif budget_max != float("inf") and contract.amount > budget_max:
            ratio = budget_max / contract.amount if contract.amount > 0 else 0
            if ratio > 0.5:
                score += 5

    # --- Location match (bonus, not counted in main 100) ---
    if user.city:
        user_city = user.city.lower()
        entity_text = f"{contract.entity or ''}".lower()
        if user_city in entity_text:
            score += 5  # Small bonus for location match

    # --- Recency bonus (10 points max) ---
    if contract.publication_date:
        days_old = (now - contract.publication_date).days
        if days_old <= 1:
            score += 10
        elif days_old <= 3:
            score += 8
        elif days_old <= 7:
            score += 5
        elif days_old <= 14:
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
    """
    Optimized matching with O(n log k) complexity using heapq.
    Early termination when we have enough high-quality matches.
    """
    import heapq

    with UnitOfWork() as uow:
        user = uow.users.get(user_id)
        if not user:
            return []

        now = datetime.utcnow()
        since = now - timedelta(days=days_back)

        # Pre-compute user embedding ONCE for semantic matching
        user_embedding = compute_user_embedding(user)
        if user_embedding is not None:
            logger.debug(f"User {user_id} embedding computed for semantic matching")

        # Build query with pre-filters for efficiency
        query = uow.session.query(Contract).filter(
            Contract.publication_date >= since,
            (Contract.deadline.is_(None)) | (Contract.deadline >= now),
        )

        # Pre-filter by budget if user has it set
        if user.budget_min and user.budget_min > 0:
            query = query.filter((Contract.amount.is_(None)) | (Contract.amount >= user.budget_min * 0.5))
        if user.budget_max and user.budget_max > 0:
            query = query.filter((Contract.amount.is_(None)) | (Contract.amount <= user.budget_max * 2))

        # Use streaming/batching for memory efficiency
        contracts = query.order_by(Contract.publication_date.desc()).limit(500).all()

        # Use min-heap to keep top K results: O(n log k) instead of O(n log n)
        # Heap stores (score, contract_dict) - negate score for max-heap behavior
        top_k_heap = []
        high_score_count = 0  # Track contracts with score >= 80

        for c in contracts:
            score = calculate_match_score(user, c, user_embedding=user_embedding)

            if score < min_score:
                continue

            if score >= 80:
                high_score_count += 1

            contract_dict = {
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
            }

            if len(top_k_heap) < limit:
                heapq.heappush(top_k_heap, (score, c.id, contract_dict))
            elif score > top_k_heap[0][0]:
                heapq.heapreplace(top_k_heap, (score, c.id, contract_dict))

            # Early termination: if we have enough high-quality matches, stop
            if high_score_count >= limit * 2 and len(top_k_heap) >= limit:
                break

        # Extract results sorted by score descending
        results = [item[2] for item in sorted(top_k_heap, key=lambda x: -x[0])]
        return results


def get_alerts(user_id: int, hours: int = 24) -> dict:
    """Get new contract alerts for a user (contracts from last N hours with high scores)."""
    with UnitOfWork() as uow:
        user = uow.users.get(user_id)
        if not user:
            return {"contracts": [], "count": 0}

        # Check free tier limits (3 alerts/week)
        from config import Config
        from core.plans import PLAN_ORDER

        user_plan = user.plan or "free"
        is_free_tier = PLAN_ORDER.get(user_plan, 0) < PLAN_ORDER.get("alertas", 1)

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
        contracts = (
            uow.session.query(Contract)
            .filter(Contract.publication_date >= since)
            .order_by(Contract.publication_date.desc())
            .all()
        )

        # Pre-compute user embedding for semantic matching
        user_embedding = compute_user_embedding(user)

        alerts = []
        for c in contracts:
            score = calculate_match_score(user, c, user_embedding=user_embedding)
            if score >= 60:
                alerts.append(
                    {
                        "id": c.id,
                        "title": c.title,
                        "entity": c.entity,
                        "amount": c.amount,
                        "source": c.source,
                        "url": c.url,
                        "deadline": c.deadline.isoformat() if c.deadline else None,
                        "publication_date": c.publication_date.isoformat() if c.publication_date else None,
                        "match_score": score,
                    }
                )

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

        total_value = (
            uow.session.query(func.sum(Contract.amount))
            .filter(
                Contract.publication_date >= last_30d,
                Contract.amount.isnot(None),
            )
            .scalar()
            or 0
        )

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
                # Build OR conditions for all keywords in ONE query (O(1) instead of O(N))
                from sqlalchemy import or_

                keyword_conditions = []
                for kw in sector_keywords:
                    pattern = f"%{kw}%"
                    keyword_conditions.append(Contract.title.ilike(pattern))
                    keyword_conditions.append(Contract.description.ilike(pattern))

                # Single query with OR for all keywords
                sector_count = (
                    uow.session.query(Contract)
                    .filter(Contract.publication_date >= last_30d, or_(*keyword_conditions))
                    .count()
                )

                # Value query with first keyword (with safety check)
                first_keyword = sector_keywords[0] if sector_keywords else ""
                sector_value_q = (
                    uow.session.query(func.sum(Contract.amount))
                    .filter(
                        Contract.publication_date >= last_30d,
                        Contract.amount.isnot(None),
                        Contract.title.ilike(f"%{first_keyword}%") if first_keyword else True,
                    )
                    .scalar()
                    or 0
                )
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
    # Skip matching on large batches to avoid blocking the server
    MAX_CONTRACTS_FOR_MATCHING = 500
    if new_count > MAX_CONTRACTS_FOR_MATCHING:
        logger.info(
            f"Skipping real-time matching: {new_count} contracts too large (max {MAX_CONTRACTS_FOR_MATCHING}). Users will see matches on next search."
        )
        return

    logger.info(f"Checking high-priority matches for {new_count} new contracts...")

    with UnitOfWork() as uow:
        # Get users with notifications enabled
        users = uow.users.get_active_with_notifications()

        # Get contracts ingested in last 2 hours (use created_at, not publication_date,
        # because imported contracts may have old publication dates)
        since = datetime.utcnow() - timedelta(hours=2)
        new_contracts = (
            uow.session.query(Contract)
            .filter(Contract.created_at >= since)
            .limit(MAX_CONTRACTS_FOR_MATCHING)
            .all()
        )

        if not new_contracts:
            return

        for user in users:
            # Pre-compute user embedding once per user for efficiency
            user_embedding = compute_user_embedding(user)
            matches_found = 0
            MAX_NOTIFICATIONS_PER_USER = 5  # Limit to avoid spam

            for contract in new_contracts:
                # Early termination: stop after finding enough matches
                if matches_found >= MAX_NOTIFICATIONS_PER_USER:
                    break

                score = calculate_match_score(user, contract, user_embedding=user_embedding)
                if score >= 85:
                    _queue_push_notification(user, contract, score)
                    matches_found += 1


def _queue_push_notification(user: User, contract: Contract, score: int):
    """Queue a push + email notification for a high-priority match."""
    logger.info(f"High-priority match: user={user.email} contract={contract.id} score={score}")

    # Try push first (requires VAPID keys — usually not configured)
    try:
        from services.notifications import send_push

        send_push(
            user.id,
            title=f"Nuevo contrato {score}% compatible",
            body=f"{contract.title[:80]} - {contract.entity or 'Sin entidad'}",
            url=f"/contracts/{contract.id}",
        )
    except Exception as e:
        logger.debug(f"Push not available for user {user.email}: {e}")

    # Always send email for high-priority matches (this actually reaches users)
    try:
        from core.tasks import task_send_email
        from config import Config

        amount = contract.amount
        if amount:
            if amount >= 1_000_000_000:
                amount_str = f"${amount/1_000_000_000:.1f}B COP"
            elif amount >= 1_000_000:
                amount_str = f"${amount/1_000_000:.0f}M COP"
            else:
                amount_str = f"${amount:,.0f} COP"
        else:
            amount_str = "No especificado"

        task_send_email.delay(
            user.email,
            "contract_alert",
            {
                "title": contract.title or "Sin título",
                "entity": contract.entity or "No especificada",
                "amount": contract.amount or 0,
                "match_score": score,
                "url": f"{Config.FRONTEND_URL}/contracts/{contract.id}",
            },
        )
    except Exception as e:
        logger.error(f"Email notification failed for user {user.email}: {e}")

    # Send Telegram if user has linked their chat_id
    try:
        if getattr(user, "telegram_chat_id", None):
            from services.notifications import send_telegram
            from config import Config

            amount = contract.amount or 0
            if amount >= 1_000_000_000:
                amt = f"${amount/1_000_000_000:.1f}B"
            elif amount >= 1_000_000:
                amt = f"${amount/1_000_000:.0f}M"
            else:
                amt = f"${amount:,.0f}" if amount else "No especificado"

            msg = (
                f"⭐ *Contrato {score}% compatible*\n\n"
                f"*{(contract.title or 'Sin título')[:100]}*\n"
                f"🏢 {contract.entity or 'No especificada'}\n"
                f"💰 {amt} COP\n"
                f"🔗 {Config.FRONTEND_URL}/contracts/{contract.id}"
            )
            send_telegram(user.telegram_chat_id, msg)
    except Exception as e:
        logger.error(f"Telegram notification failed for user {user.email}: {e}")
