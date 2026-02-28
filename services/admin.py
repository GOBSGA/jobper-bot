"""
Jobper Services — Admin panel (KPIs, users, payments, scrapers, logs)
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from config import Config
from core.cache import cache
from sqlalchemy import func as sa_func

from core.database import AuditLog, Contract, DataSource, Payment, PrivateContract, Subscription, UnitOfWork, User

logger = logging.getLogger(__name__)


def get_kpis() -> dict:
    """Dashboard KPIs: MRR, users, churn, contracts, revenue breakdown."""
    with UnitOfWork() as uow:
        total_users = uow.users.count()
        now = datetime.utcnow()
        thirty_ago = now - timedelta(days=30)
        seven_ago = now - timedelta(days=7)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

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

        # Grace subscriptions (temporary access pending review)
        grace_subs = (
            uow.session.query(Subscription)
            .filter(
                Subscription.status == "grace",
                Subscription.ends_at > now,
            )
            .count()
        )

        # Trial users
        trial_users = (
            uow.session.query(User)
            .filter(
                User.plan == "trial",
                User.trial_ends_at > now,
            )
            .count()
        )

        # New users (today, 7d, 30d)
        new_today = uow.session.query(User).filter(User.created_at >= today_start).count()
        new_7d = uow.session.query(User).filter(User.created_at >= seven_ago).count()
        new_30d = uow.session.query(User).filter(User.created_at >= thirty_ago).count()

        # Users by plan
        all_users_plans = uow.session.query(User.plan).all()
        plan_counts: dict[str, int] = {}
        for (plan,) in all_users_plans:
            p = plan or "free"
            plan_counts[p] = plan_counts.get(p, 0) + 1

        # Contracts
        contracts_today = uow.session.query(Contract).filter(Contract.created_at >= today_start).count()
        contracts_7d = uow.session.query(Contract).filter(Contract.created_at >= seven_ago).count()
        total_contracts = uow.contracts.count()

        # Revenue last 30d (approved payments) — use DB-side SUM to avoid loading all rows
        revenue_30d = (
            uow.session.query(sa_func.sum(Payment.amount))
            .filter(Payment.status == "approved", Payment.created_at >= thirty_ago)
            .scalar() or 0
        )

        # Pending payments (need review)
        pending_payments = (
            uow.session.query(Payment)
            .filter(Payment.status.in_(["pending", "review", "grace"]))
            .count()
        )

        # Churn (cancelled in last 30 days)
        churned = (
            uow.session.query(Subscription)
            .filter(
                Subscription.status == "cancelled",
                Subscription.ends_at >= thirty_ago,
            )
            .count()
        )

        # Recent signups (last 10)
        recent_users = (
            uow.session.query(User)
            .order_by(User.created_at.desc())
            .limit(10)
            .all()
        )
        recent_signups = [
            {
                "id": u.id,
                "email": u.email,
                "company_name": u.company_name,
                "plan": u.plan,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in recent_users
        ]

        # Recent payments (last 10)
        recent_pmts = (
            uow.session.query(Payment)
            .order_by(Payment.created_at.desc())
            .limit(10)
            .all()
        )
        user_ids = {p.user_id for p in recent_pmts}
        users_map = (
            {
                u.id: u.email
                for u in uow.session.query(User).filter(User.id.in_(user_ids)).all()
            }
            if user_ids
            else {}
        )
        recent_payments = [
            {
                "id": p.id,
                "user_id": p.user_id,
                "user_email": users_map.get(p.user_id, "—"),
                "amount": p.amount,
                "status": p.status,
                "plan": (p.metadata_json or {}).get("plan"),
                "reference": p.reference,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in recent_pmts
        ]

        # Active users today (distinct users with audit logs today)
        active_today = (
            uow.session.query(AuditLog.user_id)
            .filter(AuditLog.created_at >= today_start, AuditLog.user_id.isnot(None))
            .distinct()
            .count()
        )

    return {
        "mrr": mrr,
        "arr": mrr * 12,
        "revenue_30d": revenue_30d,
        "total_users": total_users,
        "active_paid": active_paid,
        "grace_subs": grace_subs,
        "trial_users": trial_users,
        "pending_payments": pending_payments,
        "new_today": new_today,
        "new_7d": new_7d,
        "new_30d": new_30d,
        "active_today": active_today,
        "plan_counts": plan_counts,
        "churn_30d": churned,
        "total_contracts": total_contracts,
        "contracts_today": contracts_today,
        "contracts_7d": contracts_7d,
        "recent_signups": recent_signups,
        "recent_payments": recent_payments,
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
                "sector": u.sector,
                "city": u.city,
                "trust_level": u.trust_level,
                "verified_payments_count": u.verified_payments_count or 0,
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

        user_ids = {p.user_id for p in payments}
        users_map = (
            {
                u.id: u.email
                for u in uow.session.query(User).filter(User.id.in_(user_ids)).all()
            }
            if user_ids
            else {}
        )

        results = [
            {
                "id": p.id,
                "user_id": p.user_id,
                "user_email": users_map.get(p.user_id, "—"),
                "amount": p.amount,
                "currency": p.currency,
                "type": p.type,
                "status": p.status,
                "plan": (p.metadata_json or {}).get("plan"),
                "reference": p.reference,
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


def get_user_detail(user_id: int) -> dict:
    """Full profile + subscriptions + payments + activity for one user."""
    with UnitOfWork() as uow:
        user = uow.users.get(user_id)
        if not user:
            return {"error": "Usuario no encontrado"}

        # User profile
        profile = {
            "id": user.id,
            "email": user.email,
            "company_name": user.company_name,
            "plan": user.plan,
            "sector": user.sector,
            "city": user.city,
            "keywords": user.keywords or [],
            "budget_min": user.budget_min,
            "budget_max": user.budget_max,
            "trust_level": user.trust_level,
            "trust_score": user.trust_score,
            "verified_payments_count": user.verified_payments_count or 0,
            "is_admin": user.is_admin,
            "onboarding_completed": user.onboarding_completed,
            "trial_ends_at": user.trial_ends_at.isoformat() if user.trial_ends_at else None,
            "privacy_policy_version": getattr(user, "privacy_policy_version", None),
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }

        # Subscriptions
        subs = (
            uow.session.query(Subscription)
            .filter(Subscription.user_id == user_id)
            .order_by(Subscription.created_at.desc())
            .limit(20)
            .all()
        )
        subscriptions = [
            {
                "id": s.id,
                "plan": s.plan,
                "status": s.status,
                "amount": s.amount,
                "starts_at": s.starts_at.isoformat() if s.starts_at else None,
                "ends_at": s.ends_at.isoformat() if s.ends_at else None,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in subs
        ]

        # Payments
        pmts = (
            uow.session.query(Payment)
            .filter(Payment.user_id == user_id)
            .order_by(Payment.created_at.desc())
            .limit(20)
            .all()
        )
        payments = [
            {
                "id": p.id,
                "amount": p.amount,
                "status": p.status,
                "type": p.type,
                "reference": p.reference,
                "plan": (p.metadata_json or {}).get("plan"),
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in pmts
        ]

        # Recent activity (last 30 audit logs)
        logs = (
            uow.session.query(AuditLog)
            .filter(AuditLog.user_id == user_id)
            .order_by(AuditLog.created_at.desc())
            .limit(30)
            .all()
        )
        activity = [
            {
                "action": log.action,
                "resource": log.resource,
                "resource_id": log.resource_id,
                "ip": log.ip,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ]

    return {
        "profile": profile,
        "subscriptions": subscriptions,
        "payments": payments,
        "activity": activity,
    }


def admin_change_plan(user_id: int, new_plan: str) -> dict:
    """Change a user's plan and create a subscription record."""
    valid_plans = ("free", "trial", "cazador", "competidor", "dominador")
    if new_plan not in valid_plans:
        return {"error": f"Plan inválido. Opciones: {', '.join(valid_plans)}"}

    with UnitOfWork() as uow:
        user = uow.users.get(user_id)
        if not user:
            return {"error": "Usuario no encontrado"}

        old_plan = user.plan
        user.plan = new_plan

        # Create subscription for paid plans (prices from Config.PLANS)
        if new_plan in ("cazador", "competidor", "dominador"):
            now = datetime.utcnow()
            plan_prices = {
                "cazador": Config.PLANS["cazador"]["price"],
                "competidor": Config.PLANS["competidor"]["price"],
                "dominador": Config.PLANS["dominador"]["price"],
            }
            sub = Subscription(
                user_id=user_id,
                plan=new_plan,
                status="active",
                amount=plan_prices.get(new_plan, 0),
                starts_at=now,
                ends_at=now + timedelta(days=30),
            )
            uow.session.add(sub)

        if new_plan == "trial":
            user.trial_ends_at = datetime.utcnow() + timedelta(days=14)

        uow.commit()

    logger.info(f"Admin changed user {user_id} plan: {old_plan} → {new_plan}")
    return {"ok": True, "old_plan": old_plan, "new_plan": new_plan}


def admin_toggle_admin(user_id: int) -> dict:
    """Toggle admin status. Protects against removing the last admin."""
    with UnitOfWork() as uow:
        user = uow.users.get(user_id)
        if not user:
            return {"error": "Usuario no encontrado"}

        if user.is_admin:
            admin_count = uow.session.query(User).filter(User.is_admin == True).count()
            if admin_count <= 1:
                return {"error": "No puedes quitar el último administrador"}
            user.is_admin = False
        else:
            user.is_admin = True

        uow.commit()

    return {"ok": True, "is_admin": user.is_admin}


def admin_extend_trial(user_id: int, days: int = 7) -> dict:
    """Extend a user's trial by N days from today."""
    with UnitOfWork() as uow:
        user = uow.users.get(user_id)
        if not user:
            return {"error": "Usuario no encontrado"}

        now = datetime.utcnow()
        # Extend from current expiry or from now, whichever is later
        base = max(user.trial_ends_at or now, now)
        user.trial_ends_at = base + timedelta(days=days)
        if user.plan not in ("cazador", "competidor", "dominador"):
            user.plan = "trial"
        uow.commit()

    logger.info(f"Admin extended trial for user {user_id} by {days} days → {user.trial_ends_at}")
    return {"ok": True, "trial_ends_at": user.trial_ends_at.isoformat()}


def admin_send_magic_link(user_id: int) -> dict:
    """Send a magic link (login link) to user's email."""
    from services.auth import send_magic_link

    with UnitOfWork() as uow:
        user = uow.users.get(user_id)
        if not user:
            return {"error": "Usuario no encontrado"}
        email = user.email

    try:
        result = send_magic_link(email)
        if result.get("error"):
            return result
        logger.info(f"Admin sent magic link to {email} (user_id={user_id})")
        return {"ok": True, "email": email}
    except Exception as exc:
        logger.error(f"admin_send_magic_link failed for {email}: {exc}")
        return {"error": f"Error al enviar email: {exc}"}


def get_activity_feed(page: int = 1, per_page: int = 50) -> dict:
    """Global activity feed: audit logs with user emails."""
    with UnitOfWork() as uow:
        q = uow.session.query(AuditLog).order_by(AuditLog.created_at.desc())
        total = q.count()
        logs = q.offset((page - 1) * per_page).limit(per_page).all()

        # Batch-fetch user emails
        user_ids = {log.user_id for log in logs if log.user_id}
        users_map = (
            {
                u.id: u.email
                for u in uow.session.query(User.id, User.email).filter(User.id.in_(user_ids)).all()
            }
            if user_ids
            else {}
        )

        results = [
            {
                "id": log.id,
                "user_id": log.user_id,
                "user_email": users_map.get(log.user_id, "—"),
                "action": log.action,
                "resource": log.resource,
                "resource_id": log.resource_id,
                "details": log.details,
                "ip": log.ip,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ]

    return {"results": results, "total": total, "page": page}


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
    import os

    health = {
        "database": True,
        "redis": False,
        "openai": False,
        "celery": False,
    }

    # Redis
    health["redis"] = cache.is_healthy()

    # OpenAI (check if API key is configured)
    health["openai"] = bool(os.getenv("OPENAI_API_KEY"))

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
                "id": log.id,
                "user_id": log.user_id,
                "action": log.action,
                "resource": log.resource,
                "resource_id": log.resource_id,
                "details": log.details,
                "ip": log.ip,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ]

    return {"results": results, "total": total, "page": page}
