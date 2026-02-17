"""
Jobper Services — Contract search, detail, matching, favorites
"""

from __future__ import annotations

import logging
from datetime import datetime

from sqlalchemy import func, text

from config import Config
from core.cache import cached
from core.database import Contract, Favorite, UnitOfWork

logger = logging.getLogger(__name__)


# =============================================================================
# SEARCH
# =============================================================================


def search_contracts(query: str, user_id: int, page: int = 1, per_page: int = 20) -> dict:
    """
    Search contracts: tries Elasticsearch first, falls back to PostgreSQL FTS.
    Returns: {results: [...], total, page, pages}
    """
    try:
        from search.engine import is_healthy
        from search.engine import search as es_search

        if is_healthy():
            return es_search(query, user_id, page, per_page)
    except Exception as e:
        logger.warning(f"ES search failed, falling back to DB: {e}")

    return _db_search(query, user_id, page, per_page)


def _db_search(query: str, user_id: int, page: int, per_page: int) -> dict:
    """
    Database search with PostgreSQL full-text search (Spanish) when available.
    Falls back to ILIKE for SQLite (dev).
    """
    use_fts = Config.is_postgresql() and query

    with UnitOfWork() as uow:
        q = uow.session.query(Contract)

        if query:
            if use_fts:
                # PostgreSQL FTS with Spanish stemmer — uses GIN index if created
                ts_query = func.plainto_tsquery("spanish", query)
                ts_vector = func.to_tsvector(
                    "spanish",
                    func.coalesce(Contract.title, "") + " " + func.coalesce(Contract.description, ""),
                )
                q = q.filter(ts_vector.op("@@")(ts_query))
                # Order by relevance rank
                rank = func.ts_rank(ts_vector, ts_query)
                q = q.order_by(rank.desc(), Contract.created_at.desc())
            else:
                # SQLite / simple fallback
                pattern = f"%{query}%"
                q = q.filter(Contract.title.ilike(pattern) | Contract.description.ilike(pattern))
                q = q.order_by(Contract.created_at.desc())
        else:
            q = q.order_by(Contract.created_at.desc())

        total = q.count()
        contracts = q.offset((page - 1) * per_page).limit(per_page).all()

        fav_ids = _get_favorite_ids(uow, user_id)
        results = [_contract_to_dict(c, c.id in fav_ids) for c in contracts]

    return {
        "contracts": results,
        "total": total,
        "page": page,
        "pages": (total + per_page - 1) // per_page,
    }


# =============================================================================
# FEED (matched contracts for user)
# =============================================================================


def get_matched_feed(user_id: int, page: int = 1, per_page: int = 20) -> dict:
    """Get contracts ordered by relevance for user."""
    with UnitOfWork() as uow:
        user = uow.users.get(user_id)
        if not user:
            return {"results": [], "total": 0, "page": 1, "pages": 0}

        q = uow.session.query(Contract).order_by(Contract.created_at.desc())

        # Filter by user keywords if available
        if user.keywords:
            from sqlalchemy import or_

            filters = []
            for kw in user.keywords:
                filters.append(Contract.title.ilike(f"%{kw}%"))
                filters.append(Contract.description.ilike(f"%{kw}%"))
            if filters:
                q = q.filter(or_(*filters))

        total = q.count()
        contracts = q.offset((page - 1) * per_page).limit(per_page).all()
        fav_ids = _get_favorite_ids(uow, user_id)

        results = [_contract_to_dict(c, c.id in fav_ids) for c in contracts]

    return {
        "contracts": results,
        "total": total,
        "page": page,
        "pages": (total + per_page - 1) // per_page,
    }


# =============================================================================
# DETAIL
# =============================================================================


@cached(ttl=600, key_pattern="contract:{contract_id}:{user_id}")
def get_contract_detail(contract_id: int, user_id: int) -> dict | None:
    """Get full contract detail with match info."""
    with UnitOfWork() as uow:
        contract = uow.contracts.get(contract_id)
        if not contract:
            return None

        fav_ids = _get_favorite_ids(uow, user_id)
        result = _contract_to_dict(contract, contract.id in fav_ids)
        result["raw_data"] = contract.raw_data or {}

    return result


def get_contract_analysis(contract_id: int, user_id: int) -> dict | None:
    """Run AI analysis on contract (Business+ plan)."""
    try:
        from intelligence.analyzer import analyze_contract

        return analyze_contract(contract_id, user_id)
    except Exception as e:
        logger.error(f"Analysis failed for contract {contract_id}: {e}")
        return {"error": "Análisis no disponible en este momento"}


# =============================================================================
# FAVORITES
# =============================================================================


def get_favorite_count(user_id: int) -> int:
    """Get total number of favorites for a user."""
    with UnitOfWork() as uow:
        return uow.session.query(Favorite).filter(Favorite.user_id == user_id).count()


def is_favorited(user_id: int, contract_id: int) -> bool:
    """Check if a contract is already favorited by the user."""
    with UnitOfWork() as uow:
        return (
            uow.session.query(Favorite)
            .filter(
                Favorite.user_id == user_id,
                Favorite.contract_id == contract_id,
            )
            .first()
            is not None
        )


def toggle_favorite(user_id: int, contract_id: int) -> dict:
    """Add or remove contract from favorites. Returns {favorited: bool}."""
    with UnitOfWork() as uow:
        existing = (
            uow.session.query(Favorite)
            .filter(
                Favorite.user_id == user_id,
                Favorite.contract_id == contract_id,
            )
            .first()
        )

        if existing:
            uow.favorites.delete(existing)
            uow.commit()
            return {"favorited": False}
        else:
            fav = Favorite(user_id=user_id, contract_id=contract_id)
            uow.favorites.create(fav)
            uow.commit()
            return {"favorited": True}


def get_favorites(user_id: int, page: int = 1, per_page: int = 20) -> dict:
    """Get user's favorited contracts."""
    with UnitOfWork() as uow:
        q = (
            uow.session.query(Contract)
            .join(Favorite, Favorite.contract_id == Contract.id)
            .filter(Favorite.user_id == user_id)
        )

        total = q.count()
        contracts = q.order_by(Favorite.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()

        results = [_contract_to_dict(c, True) for c in contracts]

    return {
        "contracts": results,
        "total": total,
        "page": page,
        "pages": (total + per_page - 1) // per_page,
    }


# =============================================================================
# HELPERS
# =============================================================================


def _get_favorite_ids(uow, user_id: int) -> set:
    favs = uow.session.query(Favorite.contract_id).filter(Favorite.user_id == user_id).all()
    return {f[0] for f in favs}


def _contract_to_dict(c: Contract, is_favorited: bool = False) -> dict:
    return {
        "id": c.id,
        "external_id": c.external_id,
        "title": c.title,
        "description": (c.description or "")[:500],
        "entity": c.entity,
        "amount": c.amount,
        "currency": c.currency,
        "country": c.country,
        "source": c.source,
        "source_type": c.source_type,
        "url": c.url,
        "publication_date": c.publication_date.isoformat() if c.publication_date else None,
        "deadline": c.deadline.isoformat() if c.deadline else None,
        "is_expired": bool(c.deadline and c.deadline < datetime.utcnow()),
        "is_favorited": is_favorited,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }


# =============================================================================
# PUBLIC / DEMO
# =============================================================================


@cached(ttl=300, key_pattern="demo_contracts")
def get_demo_contracts(limit: int = 6) -> list:
    """
    Get sample contracts for landing page demo.
    Mix of: recent, high-value, variety of sectors.
    Cached for 5 minutes.
    """
    with UnitOfWork() as uow:
        # Get recent contracts with good data (has amount, not expired)
        now = datetime.utcnow()
        contracts = (
            uow.session.query(Contract)
            .filter(
                (Contract.deadline.is_(None)) | (Contract.deadline >= now),
                Contract.amount.isnot(None),
                Contract.amount > 0,
            )
            .order_by(Contract.publication_date.desc())
            .limit(limit * 3)  # Get more to filter
            .all()
        )

        if not contracts:
            # Fallback: just get any recent contracts
            contracts = uow.session.query(Contract).order_by(Contract.created_at.desc()).limit(limit).all()

        # Try to get variety by entity (O(N) instead of O(N²))
        seen_entities = set()
        seen_contract_ids = set()
        result = []

        # First pass: unique entities
        for c in contracts:
            if len(result) >= limit:
                break
            entity_key = (c.entity or "")[:20]
            if entity_key not in seen_entities:
                seen_entities.add(entity_key)
                seen_contract_ids.add(c.id)
                result.append(_contract_to_dict(c, is_favorited=False))

        # Second pass: fill remaining (using ID set for O(1) lookup)
        for c in contracts:
            if len(result) >= limit:
                break
            if c.id not in seen_contract_ids:
                seen_contract_ids.add(c.id)
                result.append(_contract_to_dict(c, is_favorited=False))

        return result


def cleanup_expired_contracts(days_grace: int = 30) -> dict:
    """
    Delete contracts that expired more than `days_grace` days ago.
    Keeps recently-expired contracts so users can still see them briefly.
    Returns: {deleted: int}
    """
    from datetime import timedelta

    cutoff = datetime.utcnow() - timedelta(days=days_grace)
    deleted = 0

    try:
        with UnitOfWork() as uow:
            expired = (
                uow.session.query(Contract)
                .filter(Contract.deadline < cutoff)
                .all()
            )
            for contract in expired:
                uow.session.delete(contract)
                deleted += 1
            uow.commit()
        logger.info(f"Cleanup: deleted {deleted} contracts expired before {cutoff.date()}")
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")

    return {"deleted": deleted}


def get_public_stats() -> dict:
    """Get public stats for landing page."""
    with UnitOfWork() as uow:
        total = uow.contracts.count()
        from sqlalchemy import func

        recent_count = (
            uow.session.query(func.count(Contract.id))
            .filter(Contract.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0))
            .scalar()
            or 0
        )

        # Get source breakdown
        sources = uow.session.query(Contract.source, func.count(Contract.id)).group_by(Contract.source).all()

        return {
            "total_contracts": total,
            "today_new": recent_count,
            "sources": {s[0]: s[1] for s in sources if s[0]},
        }
