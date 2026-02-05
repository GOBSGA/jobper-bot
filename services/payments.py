"""
Jobper Services — Payments (Manual: Nequi / Bancolombia transfer)
User uploads comprobante → system auto-activates. Admin can audit later.
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
        payment_id = payment.id

    return {
        "payment_id": payment_id,
        "reference": reference,
        "amount": amount,
        "amount_display": f"${amount:,.0f}".replace(",", "."),
        "currency": "COP",
        "plan": plan,
        "discount": discount,
        "instructions": "Transfiere el monto exacto y sube tu comprobante. Tu plan se activa inmediatamente.",
        "payment_methods": {
            "nequi": {
                "number": Config.NEQUI_NUMBER,
                "name": "Nequi",
            },
            "bancolombia": {
                "account": Config.BANCOLOMBIA_ACCOUNT,
                "type": Config.BANCOLOMBIA_TYPE,
                "holder": Config.BANCOLOMBIA_HOLDER,
                "name": "Bancolombia",
            },
        },
    }


# =============================================================================
# CONFIRM PAYMENT (user uploads comprobante → auto-activate)
# =============================================================================

def confirm_payment(user_id: int, payment_id: int, comprobante_url: str) -> dict:
    """User uploads comprobante. Auto-activates subscription immediately."""
    now = datetime.utcnow()

    with UnitOfWork() as uow:
        payment = uow.payments.get(payment_id)
        if not payment:
            return {"error": "Pago no encontrado"}
        if payment.user_id != user_id:
            return {"error": "Pago no pertenece a este usuario"}
        if payment.status != "pending":
            return {"error": "Este pago ya fue procesado"}

        plan = payment.metadata_json.get("plan")
        if not plan or plan not in Config.PLANS:
            return {"error": "Plan inválido en el pago"}

        # Mark payment as approved
        payment.status = "approved"
        payment.comprobante_url = comprobante_url
        payment.confirmed_at = now

        # Deactivate previous subscriptions
        prev = uow.subscriptions.get_active_for_user(user_id)
        if prev:
            prev.status = "cancelled"

        # Create new subscription (30 days)
        sub = Subscription(
            user_id=user_id,
            plan=plan,
            status="active",
            amount=payment.amount,
            starts_at=now,
            ends_at=now + timedelta(days=30),
        )
        uow.subscriptions.create(sub)

        # Update user plan
        user = uow.users.get(user_id)
        user.plan = plan

        uow.commit()

        # Track referral
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
        {"plan": plan, "amount": payment.amount},
    )

    # Notify admin for audit
    task_send_email.delay(
        Config.ADMIN_EMAIL,
        "payment_request",
        {"user_id": user_id, "plan": plan, "amount": payment.amount, "reference": payment.wompi_ref, "comprobante": comprobante_url},
    )

    logger.info(f"Payment confirmed by user: user={user_id}, plan={plan}, payment={payment_id}")
    return {
        "ok": True,
        "plan": plan,
        "ends_at": (now + timedelta(days=30)).isoformat(),
    }


# =============================================================================
# PAYMENT REQUEST (user reports payment — legacy)
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

        days_remaining = max(0, (sub.ends_at - datetime.utcnow()).days)
        return {
            "id": sub.id,
            "plan": sub.plan,
            "status": sub.status,
            "amount": sub.amount,
            "starts_at": sub.starts_at.isoformat(),
            "ends_at": sub.ends_at.isoformat(),
            "days_remaining": days_remaining,
            "needs_renewal": days_remaining <= 7,
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


# =============================================================================
# RENEWAL CHECKS (called by scheduler every 30 min)
# =============================================================================

def check_renewals():
    """Check subscriptions approaching expiry and send reminders / expire."""
    now = datetime.utcnow()
    from core.tasks import task_send_email

    with UnitOfWork() as uow:
        active_subs = (
            uow.session.query(Subscription)
            .filter(Subscription.status == "active")
            .all()
        )

        for sub in active_subs:
            days_left = (sub.ends_at - now).days
            user = uow.users.get(sub.user_id)
            if not user:
                continue

            already_reminded = sub.renewal_reminded_at
            today = now.date()

            # Expired: auto-downgrade to free
            if days_left < 0:
                sub.status = "expired"
                user.plan = "free"
                logger.info(f"Subscription expired: user={user.id}, plan={sub.plan}")
                task_send_email.delay(user.email, "subscription_expired", {
                    "plan": sub.plan,
                })
                continue

            # 7 days reminder
            if days_left <= 7 and days_left > 3:
                if not already_reminded or already_reminded.date() < today - timedelta(days=3):
                    sub.renewal_reminded_at = now
                    task_send_email.delay(user.email, "renewal_reminder", {
                        "days_left": days_left,
                        "plan": sub.plan,
                        "amount": sub.amount,
                    })

            # 3 days reminder (urgent)
            elif days_left <= 3 and days_left > 0:
                if not already_reminded or already_reminded.date() < today - timedelta(days=1):
                    sub.renewal_reminded_at = now
                    task_send_email.delay(user.email, "renewal_urgent", {
                        "days_left": days_left,
                        "plan": sub.plan,
                        "amount": sub.amount,
                    })
                    # Also send push + WhatsApp
                    try:
                        from services.notifications import send_push, send_whatsapp_renewal_reminder
                        send_push(user.id, f"Tu plan vence en {days_left} día{'s' if days_left > 1 else ''}",
                                  "Renueva para no perder acceso.", "/payments")
                        send_whatsapp_renewal_reminder(user.id, days_left, sub.plan)
                    except Exception:
                        pass

        uow.commit()

    logger.info("Renewal check completed")
