"""
Jobper Services — Admin panel (KPIs, users, payments, scrapers, logs)
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from core.cache import cache
from core.database import AuditLog, Contract, DataSource, Payment, PrivateContract, Subscription, UnitOfWork, User

logger = logging.getLogger(__name__)


def get_kpis() -> dict:
    """Dashboard KPIs: MRR, users, churn, contracts."""
    with UnitOfWork() as uow:
        total_users = uow.users.count()
        now = datetime.utcnow()
        thirty_ago = now - timedelta(days=30)

        # Active subscriptions
        active_subs = (
            uow.session.query(Subscription)
            .filter(
                Subscription.status == "active",
                Subscription.ends_at > now,
            )
            .all()
        )

        mrr = sum(s.amount for s in active_subs)
        active_paid = len(active_subs)

        # Trial users
        trial_users = (
            uow.session.query(User)
            .filter(
                User.plan == "trial",
                User.trial_ends_at > now,
            )
            .count()
        )

        # Contracts today
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        contracts_today = uow.session.query(Contract).filter(Contract.created_at >= today_start).count()

        total_contracts = uow.contracts.count()

        # Churn (cancelled in last 30 days)
        churned = (
            uow.session.query(Subscription)
            .filter(
                Subscription.status == "cancelled",
                Subscription.ends_at >= thirty_ago,
            )
            .count()
        )

    return {
        "mrr": mrr,
        "total_users": total_users,
        "active_paid": active_paid,
        "trial_users": trial_users,
        "churn_30d": churned,
        "total_contracts": total_contracts,
        "contracts_today": contracts_today,
    }


def list_users(page: int = 1, per_page: int = 50, search: str = "") -> dict:
    """List users with plan info."""
    with UnitOfWork() as uow:
        if search:
            users = uow.users.search(search, limit=per_page)
            total = len(users)
        else:
            q = uow.session.query(User).order_by(User.created_at.desc())
            total = q.count()
            users = q.offset((page - 1) * per_page).limit(per_page).all()

        results = [
            {
                "id": u.id,
                "email": u.email,
                "company_name": u.company_name,
                "plan": u.plan,
                "created_at": u.created_at.isoformat() if u.created_at else None,
                "is_admin": u.is_admin,
            }
            for u in users
        ]

    return {"results": results, "total": total, "page": page}


def list_payments(page: int = 1, per_page: int = 50) -> dict:
    """List payments with status."""
    with UnitOfWork() as uow:
        q = uow.session.query(Payment).order_by(Payment.created_at.desc())
        total = q.count()
        payments = q.offset((page - 1) * per_page).limit(per_page).all()

        results = [
            {
                "id": p.id,
                "user_id": p.user_id,
                "amount": p.amount,
                "currency": p.currency,
                "type": p.type,
                "status": p.status,
                "wompi_ref": p.wompi_ref,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in payments
        ]

    return {"results": results, "total": total, "page": page}


def moderate_contract(contract_id: int, action: str) -> dict:
    """Approve, reject, or delete a marketplace contract."""
    with UnitOfWork() as uow:
        pc = uow.private_contracts.get(contract_id)
        if not pc:
            return {"error": "Contrato no encontrado"}

        if action == "approve":
            pc.status = "active"
        elif action == "reject":
            pc.status = "cancelled"
        elif action == "delete":
            uow.private_contracts.delete(pc)
            uow.commit()
            return {"ok": True, "action": "deleted"}
        else:
            return {"error": "Acción inválida"}

        uow.commit()

    return {"ok": True, "action": action}


def get_scraper_status() -> list[dict]:
    """Get status of all data sources."""
    with UnitOfWork() as uow:
        sources = uow.session.query(DataSource).all()
        return [
            {
                "key": s.source_key,
                "name": s.display_name,
                "enabled": s.is_enabled,
                "last_fetch": s.last_successful_fetch.isoformat() if s.last_successful_fetch else None,
                "error_count": s.error_count,
            }
            for s in sources
        ]


def get_system_health() -> dict:
    """Check health of all external services."""
    health = {
        "database": True,
        "redis": False,
        "elasticsearch": False,
        "celery": False,
    }

    # Redis
    health["redis"] = cache.is_healthy()

    # Elasticsearch
    try:
        from search.engine import is_healthy as es_healthy

        health["elasticsearch"] = es_healthy()
    except Exception:
        pass

    # Celery
    try:
        from core.tasks import get_celery

        celery = get_celery()
        health["celery"] = celery is not None
    except Exception:
        pass

    return health


def get_logs(page: int = 1, per_page: int = 100, action: str = "", user_id: int = None) -> dict:
    """Get audit logs with filters."""
    with UnitOfWork() as uow:
        q = uow.session.query(AuditLog).order_by(AuditLog.created_at.desc())

        if action:
            q = q.filter(AuditLog.action == action)
        if user_id:
            q = q.filter(AuditLog.user_id == user_id)

        total = q.count()
        logs = q.offset((page - 1) * per_page).limit(per_page).all()

        results = [
            {
                "id": l.id,
                "user_id": l.user_id,
                "action": l.action,
                "resource": l.resource,
                "resource_id": l.resource_id,
                "details": l.details,
                "ip": l.ip,
                "created_at": l.created_at.isoformat() if l.created_at else None,
            }
            for l in logs
        ]

    return {"results": results, "total": total, "page": page}
