"""
Jobper Services — Payments (Manual: Nequi / Bancolombia transfer)
No external payment gateway. Admin verifies and activates manually.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta

from config import Config
from core.cache import cache
from core.database import UnitOfWork, Subscription, Payment, User

logger = logging.getLogger(__name__)


# =============================================================================
# PLANS
# =============================================================================

PLAN_ORDER = ["free", "alertas", "business", "enterprise"]


def get_plans() -> list[dict]:
    """Return available plans with pricing."""
    return [
        {"key": k, **v}
        for k, v in Config.PLANS.items()
    ]


def check_feature_access(user_plan: str, feature: str) -> bool:
    """Check if a plan has access to a feature."""
    required_plan = Config.FEATURE_GATES.get(feature)
    if not required_plan:
        return True  # Feature not gated

    user_idx = PLAN_ORDER.index(user_plan) if user_plan in PLAN_ORDER else -1
    req_idx = PLAN_ORDER.index(required_plan) if required_plan in PLAN_ORDER else 0
    return user_idx >= req_idx


# =============================================================================
# CHECKOUT (manual payment — Nequi / Bancolombia)
# =============================================================================

def create_checkout(user_id: int, plan: str) -> dict:
    """
    Create a pending payment request for manual payment (Nequi/Bancolombia).
    Returns payment info so the user can transfer.
    """
    if plan not in Config.PLANS:
        return {"error": "Plan inválido"}

    plan_info = Config.PLANS[plan]
    amount = plan_info["price"]

    if amount <= 0:
        return {"error": "Plan gratuito no requiere pago"}

    # Calculate referral discount
    discount = _get_referral_discount(user_id)
    if discount > 0:
        amount = int(amount * (1 - discount))

    reference = f"JOB-{user_id}-{plan}-{int(datetime.utcnow().timestamp())}"

    with UnitOfWork() as uow:
        # Create pending payment
        payment = Payment(
            user_id=user_id,
            amount=amount,
            currency="COP",
            type="subscription",
            wompi_ref=reference,
            status="pending",
            metadata_json={"plan": plan, "discount": discount, "method": "manual"},
        )
        uow.payments.create(payment)
        uow.commit()

    return {
        "reference": reference,
        "amount": amount,
        "currency": "COP",
        "plan": plan,
        "discount": discount,
        "nequi_number": Config.NEQUI_NUMBER,
        "bancolombia_account": Config.BANCOLOMBIA_ACCOUNT,
        "bancolombia_type": Config.BANCOLOMBIA_TYPE,
        "bancolombia_holder": Config.BANCOLOMBIA_HOLDER,
    }


# =============================================================================
# PAYMENT REQUEST (user reports payment)
# =============================================================================

def create_payment_request(user_id: int, plan: str) -> dict:
    """User reports they've made a manual payment (Nequi/transfer)."""
    if plan not in Config.PLANS:
        return {"error": "Plan inválido"}

    plan_info = Config.PLANS[plan]
    amount = plan_info["price"]

    discount = _get_referral_discount(user_id)
    if discount > 0:
        amount = int(amount * (1 - discount))

    reference = f"JOB-{user_id}-{plan}-{int(datetime.utcnow().timestamp())}"

    with UnitOfWork() as uow:
        payment = Payment(
            user_id=user_id,
            amount=amount,
            currency="COP",
            type="subscription",
            wompi_ref=reference,
            status="pending",
            metadata_json={"plan": plan, "discount": discount, "method": "manual"},
        )
        uow.payments.create(payment)
        uow.commit()

    # Notify admin via email
    from core.tasks import task_send_email
    task_send_email.delay(
        Config.ADMIN_EMAIL,
        "payment_request",
        {"user_id": user_id, "plan": plan, "amount": amount, "reference": reference},
    )

    logger.info(f"Payment request created: user={user_id}, plan={plan}, ref={reference}")
    return {"ok": True, "reference": reference}


# =============================================================================
# ADMIN ACTIVATION
# =============================================================================

def admin_activate(user_id: int, plan: str) -> dict:
    """Admin manually activates a subscription after verifying payment."""
    if plan not in Config.PLANS:
        return {"error": "Plan inválido"}

    plan_info = Config.PLANS[plan]
    amount = plan_info["price"]
    now = datetime.utcnow()

    with UnitOfWork() as uow:
        user = uow.users.get(user_id)
        if not user:
            return {"error": "Usuario no encontrado"}

        # Deactivate previous subscriptions
        prev = uow.subscriptions.get_active_for_user(user_id)
        if prev:
            prev.status = "cancelled"

        # Create new subscription (30 days)
        sub = Subscription(
            user_id=user_id,
            plan=plan,
            status="active",
            amount=amount,
            starts_at=now,
            ends_at=now + timedelta(days=30),
        )
        uow.subscriptions.create(sub)

        # Update user plan
        user.plan = plan

        # Approve any pending payment for this user+plan
        pending = (
            uow.session.query(Payment)
            .filter(
                Payment.user_id == user_id,
                Payment.status == "pending",
            )
            .order_by(Payment.created_at.desc())
            .first()
        )
        if pending:
            pending.status = "approved"

        uow.commit()

        # Track referral subscription
        try:
            from services.referrals import track_subscription
            track_subscription(user_id)
        except Exception:
            pass

    # Send confirmation email
    from core.tasks import task_send_email
    task_send_email.delay(
        user.email,
        "payment_confirmed",
        {"plan": plan, "amount": amount},
    )

    logger.info(f"Subscription activated by admin: user={user_id}, plan={plan}")
    return {"ok": True, "plan": plan, "user_id": user_id}


# =============================================================================
# SUBSCRIPTION MANAGEMENT
# =============================================================================

def get_subscription(user_id: int) -> dict | None:
    """Get current subscription info."""
    with UnitOfWork() as uow:
        sub = uow.subscriptions.get_active_for_user(user_id)
        if not sub:
            user = uow.users.get(user_id)
            if user and user.is_trial_active():
                return {
                    "plan": "trial",
                    "status": "active",
                    "ends_at": user.trial_ends_at.isoformat(),
                    "days_remaining": (user.trial_ends_at - datetime.utcnow()).days,
                }
            return None

        return {
            "id": sub.id,
            "plan": sub.plan,
            "status": sub.status,
            "amount": sub.amount,
            "starts_at": sub.starts_at.isoformat(),
            "ends_at": sub.ends_at.isoformat(),
            "days_remaining": max(0, (sub.ends_at - datetime.utcnow()).days),
            "auto_renew": sub.auto_renew,
        }


def cancel_subscription(user_id: int) -> dict:
    """Cancel active subscription (remains active until end date)."""
    with UnitOfWork() as uow:
        sub = uow.subscriptions.get_active_for_user(user_id)
        if not sub:
            return {"error": "No hay suscripción activa"}

        sub.auto_renew = False
        sub.status = "cancelled"
        uow.commit()

    cache.delete_pattern(f"user:{user_id}:*")
    return {"ok": True, "message": "Suscripción cancelada. Acceso activo hasta fin de período."}


# =============================================================================
# HELPERS
# =============================================================================

def _get_referral_discount(user_id: int) -> float:
    """Get referral discount for user."""
    try:
        from services.referrals import calculate_discount
        return calculate_discount(user_id)
    except Exception:
        return 0.0
