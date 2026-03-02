"""
Jobper Services — Referral system
1 referral = 10%, 10 referrals = 50%, max 10/month
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from config import Config
from core.database import Referral, UnitOfWork

logger = logging.getLogger(__name__)


def generate_code(user_id: int) -> dict:
    """Get or return existing referral code for user."""
    with UnitOfWork() as uow:
        user = uow.users.get(user_id)
        if not user:
            return {"error": "Usuario no encontrado"}

        if user.referral_code:
            return {"code": user.referral_code}

        import secrets

        code = f"JOB-{secrets.token_hex(4).upper()}"
        user.referral_code = code
        uow.commit()

        return {"code": code}


def track_click(code: str) -> dict:
    """Track referral link click — always creates a new row per click."""
    with UnitOfWork() as uow:
        user = uow.users.get_by_referral_code(code)
        if not user:
            return {"error": "Código no válido"}

        # Always insert a new click row. track_signup will claim the most recent
        # unassigned one. Avoids a check-then-insert race condition.
        referral = Referral(
            referrer_id=user.id,
            code=code,
            status="clicked",
        )
        uow.referrals.create(referral)
        uow.commit()

        return {"ok": True}


def track_signup(code: str, new_user_id: int) -> dict:
    """Link referral to new user on signup."""
    with UnitOfWork() as uow:
        # Find most recent click with this code that hasn't been assigned
        referral = (
            uow.session.query(Referral)
            .filter(Referral.code == code, Referral.referred_id.is_(None))
            .order_by(Referral.clicked_at.desc())
            .first()
        )

        if not referral:
            return {"error": "No referral found"}

        referral.referred_id = new_user_id
        referral.status = "registered"
        referral.registered_at = datetime.now(timezone.utc)

        # Also mark user as referred
        new_user = uow.users.get(new_user_id)
        if new_user:
            new_user.referred_by = referral.referrer_id

        uow.commit()

    return {"ok": True}


def track_subscription(user_id: int):
    """Mark referral as converting when referred user subscribes."""
    with UnitOfWork() as uow:
        referral = (
            uow.session.query(Referral).filter(Referral.referred_id == user_id, Referral.status == "registered").first()
        )

        if referral:
            referral.status = "subscribed"
            referral.subscribed_at = datetime.now(timezone.utc)
            uow.commit()


def calculate_discount(user_id: int) -> float:
    """
    Calculate discount based on successful referrals.
    1 = 10%, 10 = 50%. Linear interpolation between.
    """
    with UnitOfWork() as uow:
        count = uow.referrals.count_for_referrer(user_id, status="subscribed")

    if count <= 0:
        return 0.0

    # Get applicable discount tier
    tiers = sorted(Config.REFERRAL_DISCOUNTS.items())  # [(1, 0.1), (10, 0.5)]

    for threshold, discount in reversed(tiers):
        if count >= threshold:
            return discount

    return 0.0


def get_referral_stats(user_id: int) -> dict:
    """Get referral stats for user."""
    with UnitOfWork() as uow:
        referrals = uow.referrals.get_for_referrer(user_id)

        clicks = sum(1 for r in referrals)
        signups = sum(1 for r in referrals if r.status in ("registered", "subscribed"))
        subscribed = sum(1 for r in referrals if r.status == "subscribed")

    discount = calculate_discount(user_id)

    return {
        "total_clicks": clicks,
        "total_signups": signups,
        "total_subscribed": subscribed,
        "current_discount": discount,
        "max_per_month": Config.REFERRAL_MAX_PER_MONTH,
    }
