"""
Jobper Services — Marketplace (publish, feature, contact reveal)
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from core.database import AuditLog, PrivateContract, UnitOfWork

logger = logging.getLogger(__name__)


def list_marketplace(
    page: int = 1,
    per_page: int = 20,
    category: str | None = None,
    city: str | None = None,
) -> dict:
    """List active marketplace contracts, featured first."""
    with UnitOfWork() as uow:
        q = uow.session.query(PrivateContract).filter(PrivateContract.status == "active")

        if category:
            q = q.filter(PrivateContract.category.ilike(f"%{category}%"))
        if city:
            q = q.filter(PrivateContract.city.ilike(f"%{city}%"))

        total = q.count()

        contracts = (
            q.order_by(
                PrivateContract.is_featured.desc(),
                PrivateContract.created_at.desc(),
            )
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        results = [_pc_to_dict(c) for c in contracts]

    return {
        "results": results,
        "total": total,
        "page": page,
        "pages": (total + per_page - 1) // per_page,
    }


def publish(user_id: int, data: dict) -> dict:
    """Publish a new private contract to marketplace."""
    if not data.get("title"):
        return {"error": "El título es obligatorio"}

    with UnitOfWork() as uow:
        user = uow.users.get(user_id)
        if not user:
            return {"error": "Usuario no encontrado"}

        pc = PrivateContract(
            publisher_id=user_id,
            title=data["title"],
            description=data.get("description"),
            category=data.get("category"),
            budget_min=data.get("budget_min"),
            budget_max=data.get("budget_max"),
            city=data.get("city"),
            is_remote=data.get("is_remote", False),
            deadline=data.get("deadline"),
            contact_email=user.email,
            contact_phone=data.get("contact_phone"),
            keywords=data.get("keywords", []),
            status="active",
        )
        uow.private_contracts.create(pc)
        uow.commit()

        return _pc_to_dict(pc)


def edit(user_id: int, contract_id: int, data: dict) -> dict:
    """Edit own marketplace contract."""
    with UnitOfWork() as uow:
        pc = uow.private_contracts.get(contract_id)
        if not pc or pc.publisher_id != user_id:
            return {"error": "Contrato no encontrado"}

        for field in (
            "title",
            "description",
            "category",
            "budget_min",
            "budget_max",
            "city",
            "is_remote",
            "deadline",
            "contact_phone",
            "keywords",
        ):
            if field in data:
                setattr(pc, field, data[field])

        pc.updated_at = datetime.utcnow()
        uow.commit()

        return _pc_to_dict(pc)


def feature(contract_id: int, user_id: int) -> dict:
    """
    Feature a marketplace contract.
    Free for paid plans with featured_unlimited, else charge per Config.FEATURED_PRICING.
    """
    from config import Config

    with UnitOfWork() as uow:
        pc = uow.private_contracts.get(contract_id)
        if not pc or pc.publisher_id != user_id:
            return {"error": "Contrato no encontrado"}

        user = uow.users.get(user_id)
        if not user:
            return {"error": "Usuario no encontrado"}

        # Check if user has unlimited featured (paid plan)
        plan_features = Config.PLANS.get(user.plan, {}).get("features", [])
        if "featured_unlimited" in plan_features:
            pc.is_featured = True
            pc.featured_until = datetime.utcnow() + timedelta(days=30)
            uow.commit()
            return {"ok": True, "featured_until": pc.featured_until.isoformat()}

        # Otherwise, needs separate payment
        return {
            "requires_payment": True,
            "pricing": Config.FEATURED_PRICING,
        }


def get_contact(contract_id: int, user_id: int) -> dict:
    """Reveal publisher contact info (audit logged)."""
    with UnitOfWork() as uow:
        pc = uow.private_contracts.get(contract_id)
        if not pc:
            return {"error": "Contrato no encontrado"}

        # Audit log
        log = AuditLog(
            user_id=user_id,
            action="contact_reveal",
            resource="private_contract",
            resource_id=str(contract_id),
        )
        uow.audit.create(log)
        uow.commit()

        return {
            "contact_email": pc.contact_email,
            "contact_phone": pc.contact_phone,
            "publisher_company": pc.publisher.company_name if pc.publisher else None,
        }


# =============================================================================
# HELPERS
# =============================================================================


def _pc_to_dict(pc: PrivateContract) -> dict:
    return {
        "id": pc.id,
        "publisher_id": pc.publisher_id,
        "title": pc.title,
        "description": (pc.description or "")[:500],
        "category": pc.category,
        "budget_min": pc.budget_min,
        "budget_max": pc.budget_max,
        "currency": pc.currency,
        "city": pc.city,
        "country": pc.country,
        "is_remote": pc.is_remote,
        "deadline": pc.deadline.isoformat() if pc.deadline else None,
        "status": pc.status,
        "is_featured": pc.is_featured,
        "featured_until": pc.featured_until.isoformat() if pc.featured_until else None,
        "keywords": pc.keywords or [],
        "created_at": pc.created_at.isoformat() if pc.created_at else None,
    }
