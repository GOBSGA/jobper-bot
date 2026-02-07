"""
Jobper Services — Payments (Manual: Nequi / Bancolombia transfer)
User uploads comprobante → AI verifies → system activates if valid.
Includes duplicate detection and fraud prevention.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from pathlib import Path

from config import Config
from core.cache import cache
from core.database import UnitOfWork, Subscription, Payment, User
from services.receipt_verification import (
    generate_payment_reference,
    verify_payment_receipt,
    compute_image_hash,
)

logger = logging.getLogger(__name__)


# =============================================================================
# PLANS — Los 4 planes de Jobper
# =============================================================================

# Orden de planes (mayor índice = mejor plan)
PLAN_ORDER = ["free", "cazador", "competidor", "dominador"]

# Trust levels based on verified payments count
TRUST_LEVELS = {
    0: "new",       # No verified payments yet
    1: "bronze",    # 1 verified payment
    2: "silver",    # 2 verified payments → one-click renewal enabled
    4: "gold",      # 4+ verified payments
    8: "platinum",  # 8+ verified payments (loyal customer)
}

# Alias para compatibilidad con código/datos anteriores
PLAN_ALIASES = {
    "alertas": "cazador",
    "starter": "cazador",
    "business": "competidor",
    "enterprise": "dominador",
    "trial": "free",
}


def normalize_plan(plan: str) -> str:
    """Normaliza nombres de planes viejos a los nuevos."""
    return PLAN_ALIASES.get(plan, plan) or "free"


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

    normalized_user = normalize_plan(user_plan)
    normalized_req = normalize_plan(required_plan)

    user_idx = PLAN_ORDER.index(normalized_user) if normalized_user in PLAN_ORDER else -1
    req_idx = PLAN_ORDER.index(normalized_req) if normalized_req in PLAN_ORDER else 0
    return user_idx >= req_idx


# =============================================================================
# TRUSTED PAYER SYSTEM
# =============================================================================

def calculate_trust_level(verified_count: int) -> str:
    """Calculate trust level based on verified payments count."""
    level = "new"
    for threshold, level_name in sorted(TRUST_LEVELS.items()):
        if verified_count >= threshold:
            level = level_name
    return level


def update_user_trust(user_id: int, confidence: float) -> dict:
    """
    Update user's trust score after a verified payment.

    High-confidence payments (+95%) give extra trust points.

    Returns:
        dict with new trust info and any unlocked rewards
    """
    now = datetime.utcnow()
    rewards = []

    with UnitOfWork() as uow:
        user = uow.users.get(user_id)
        if not user:
            return {"error": "Usuario no encontrado"}

        # Calculate trust points based on confidence
        # 95%+ = 10 points, 90-95% = 7 points, 85-90% = 5 points
        if confidence >= 0.95:
            points = 10
        elif confidence >= 0.90:
            points = 7
        elif confidence >= 0.85:
            points = 5
        else:
            points = 3

        # Update trust score
        old_score = user.trust_score or 0.0
        old_count = user.verified_payments_count or 0
        old_level = user.trust_level or "new"

        user.trust_score = old_score + points
        user.verified_payments_count = old_count + 1
        user.last_verified_payment_at = now

        # Calculate new trust level
        new_level = calculate_trust_level(user.verified_payments_count)
        user.trust_level = new_level

        # Check for unlocked rewards
        if new_level != old_level:
            rewards.append({
                "type": "level_up",
                "old_level": old_level,
                "new_level": new_level,
                "message": f"¡Subiste a nivel {new_level.title()}!",
            })

        # Enable one-click renewal at silver level (2+ verified payments)
        if user.verified_payments_count >= 2 and not user.one_click_renewal_enabled:
            user.one_click_renewal_enabled = True
            rewards.append({
                "type": "feature_unlock",
                "feature": "one_click_renewal",
                "message": "¡Desbloqueaste la renovación con un clic!",
            })

        uow.commit()

        return {
            "trust_score": user.trust_score,
            "verified_payments_count": user.verified_payments_count,
            "trust_level": new_level,
            "one_click_renewal_enabled": user.one_click_renewal_enabled,
            "points_earned": points,
            "rewards": rewards,
        }


def get_user_trust_info(user_id: int) -> dict:
    """Get user's current trust status."""
    with UnitOfWork() as uow:
        user = uow.users.get(user_id)
        if not user:
            return {"error": "Usuario no encontrado"}

        return {
            "trust_score": user.trust_score or 0.0,
            "verified_payments_count": user.verified_payments_count or 0,
            "trust_level": user.trust_level or "new",
            "one_click_renewal_enabled": user.one_click_renewal_enabled or False,
            "is_verified_payer": (user.verified_payments_count or 0) >= 1,
            "last_verified_at": user.last_verified_payment_at.isoformat() if user.last_verified_payment_at else None,
        }


# =============================================================================
# CHECKOUT (manual payment — Nequi / Bancolombia)
# =============================================================================

def create_checkout(user_id: int, plan: str) -> dict:
    """
    Create a pending payment request for manual payment (Nequi/Bancolombia).
    Returns payment info with unique reference code for verification.
    """
    # Normalizar nombre de plan (compatibilidad con nombres viejos)
    plan = normalize_plan(plan)

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

    # Generate unique, verifiable reference code
    reference = generate_payment_reference(user_id, plan, amount)

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

    # Determine which payment method to show based on config
    payment_methods = {}
    if Config.NEQUI_NUMBER:
        payment_methods["nequi"] = {
            "number": Config.NEQUI_NUMBER,
            "name": "Nequi",
        }
    if Config.BANCOLOMBIA_ACCOUNT:
        payment_methods["bancolombia"] = {
            "account": Config.BANCOLOMBIA_ACCOUNT,
            "type": Config.BANCOLOMBIA_TYPE,
            "holder": Config.BANCOLOMBIA_HOLDER,
            "name": "Bancolombia",
        }

    return {
        "payment_id": payment_id,
        "reference": reference,
        "amount": amount,
        "amount_display": f"${amount:,.0f}".replace(",", "."),
        "currency": "COP",
        "plan": plan,
        "discount": discount,
        "instructions": (
            f"1. Transfiere exactamente {f'${amount:,.0f}'.replace(',', '.')} COP\n"
            f"2. En la descripción/concepto pon: {reference}\n"
            f"3. Sube tu comprobante para activar tu plan"
        ),
        "reference_instructions": (
            f"IMPORTANTE: Incluye este código en la descripción de tu transferencia:\n{reference}"
        ),
        "payment_methods": payment_methods,
    }


# =============================================================================
# CONFIRM PAYMENT (user uploads comprobante → AI verifies → activate if valid)
# =============================================================================

def confirm_payment(user_id: int, payment_id: int, comprobante_path: str) -> dict:
    """
    User uploads comprobante. AI verifies before activating.

    Flow:
    1. Verify receipt with AI (amount, reference, destination, authenticity)
    2. Check for duplicate receipts
    3. If valid and confident → auto-activate
    4. If uncertain → mark for manual review
    5. If invalid → reject with reason

    Args:
        user_id: The user ID
        payment_id: The payment ID to confirm
        comprobante_path: Local file path to the uploaded receipt image

    Returns:
        dict with status and details
    """
    now = datetime.utcnow()

    # Validate payment exists and belongs to user
    with UnitOfWork() as uow:
        payment = uow.payments.get(payment_id)
        if not payment:
            return {"error": "Pago no encontrado"}
        if payment.user_id != user_id:
            return {"error": "Pago no pertenece a este usuario"}
        if payment.status not in ("pending", "review"):
            return {"error": "Este pago ya fue procesado"}

        plan = payment.metadata_json.get("plan")
        if not plan or plan not in Config.PLANS:
            return {"error": "Plan inválido en el pago"}

        # Capture values for verification
        payment_amount = payment.amount
        payment_ref = payment.wompi_ref

    # Verify the receipt with AI
    verification = verify_payment_receipt(
        user_id=user_id,
        payment_id=payment_id,
        image_path=comprobante_path,
    )

    # Handle verification result
    if not verification["valid"]:
        if verification.get("requires_review"):
            # Borderline case - needs manual review
            with UnitOfWork() as uow:
                payment = uow.payments.get(payment_id)
                if payment:
                    payment.status = "review"
                    payment.comprobante_url = comprobante_path
                    payment.verification_status = "manual_review"
                    payment.verification_result = verification.get("verification", {})
                    uow.commit()

            # Notify admin for manual review
            from core.tasks import task_send_email
            task_send_email.delay(
                Config.ADMIN_EMAIL,
                "payment_review_needed",
                {
                    "user_id": user_id,
                    "payment_id": payment_id,
                    "plan": plan,
                    "amount": payment_amount,
                    "reference": payment_ref,
                    "issues": verification.get("issues", []),
                    "confidence": verification.get("verification", {}).get("confidence", 0),
                },
            )

            logger.warning(f"Payment requires review: user={user_id}, payment={payment_id}, issues={verification.get('issues')}")
            return {
                "ok": False,
                "status": "review",
                "message": "Tu comprobante está siendo verificado. Te notificaremos en breve.",
                "issues": verification.get("issues", []),
            }
        else:
            # Invalid - reject
            with UnitOfWork() as uow:
                payment = uow.payments.get(payment_id)
                if payment:
                    payment.verification_status = "rejected"
                    payment.verification_result = verification.get("verification", {})
                    # Don't change status to allow retry
                    uow.commit()

            logger.warning(f"Payment rejected: user={user_id}, payment={payment_id}, issues={verification.get('issues')}")
            return {
                "ok": False,
                "status": "rejected",
                "message": "El comprobante no pudo ser verificado.",
                "issues": verification.get("issues", []),
                "can_retry": True,
            }

    # Valid - activate subscription
    user_email = None
    with UnitOfWork() as uow:
        payment = uow.payments.get(payment_id)
        if not payment:
            return {"error": "Pago no encontrado"}

        # Mark payment as approved
        payment.status = "approved"
        payment.comprobante_url = comprobante_path
        payment.confirmed_at = now
        payment.verification_status = "auto_approved"
        payment.verification_result = verification.get("verification", {})

        # Deactivate previous subscriptions
        prev = uow.subscriptions.get_active_for_user(user_id)
        if prev:
            prev.status = "cancelled"

        # Create new subscription (30 days)
        sub = Subscription(
            user_id=user_id,
            plan=plan,
            status="active",
            amount=payment_amount,
            starts_at=now,
            ends_at=now + timedelta(days=30),
        )
        uow.subscriptions.create(sub)

        # Update user plan
        user = uow.users.get(user_id)
        if not user:
            return {"error": "Usuario no encontrado"}
        user.plan = plan
        user_email = user.email

        uow.commit()

        # Track referral
        try:
            from services.referrals import track_subscription
            track_subscription(user_id)
        except Exception:
            pass

    # Invalidate user cache so new plan takes effect immediately
    cache.delete_pattern(f"user:{user_id}:*")
    cache.delete_pattern(f"matched:{user_id}:*")

    # Update trust score for high-confidence payments
    confidence = verification.get("verification", {}).get("confidence", 0)
    trust_update = None
    if confidence >= 0.85:  # Only update trust for verified payments
        trust_update = update_user_trust(user_id, confidence)
        if trust_update and not trust_update.get("error"):
            logger.info(f"Trust updated: user={user_id}, points={trust_update.get('points_earned')}, level={trust_update.get('trust_level')}")

    # Send confirmation email
    from core.tasks import task_send_email
    task_send_email.delay(
        user_email,
        "payment_confirmed",
        {"plan": plan, "amount": payment_amount},
    )

    # Notify admin for audit (even auto-approved ones)
    task_send_email.delay(
        Config.ADMIN_EMAIL,
        "payment_auto_approved",
        {
            "user_id": user_id,
            "plan": plan,
            "amount": payment_amount,
            "reference": payment_ref,
            "comprobante": comprobante_path,
            "confidence": confidence,
        },
    )

    logger.info(f"Payment auto-approved: user={user_id}, plan={plan}, payment={payment_id}, confidence={confidence}")

    # Build response with trust info
    response = {
        "ok": True,
        "status": "approved",
        "plan": plan,
        "ends_at": (now + timedelta(days=30)).isoformat(),
        "message": "¡Tu plan ha sido activado!",
    }

    # Add trust rewards if any were earned
    if trust_update and not trust_update.get("error"):
        response["trust"] = {
            "level": trust_update.get("trust_level"),
            "points_earned": trust_update.get("points_earned"),
            "one_click_renewal": trust_update.get("one_click_renewal_enabled"),
        }
        if trust_update.get("rewards"):
            response["rewards"] = trust_update.get("rewards")

    return response


# =============================================================================
# PAYMENT REQUEST (user reports payment — legacy)
# =============================================================================

def create_payment_request(user_id: int, plan: str) -> dict:
    """User reports they've made a manual payment (Nequi/transfer)."""
    plan = normalize_plan(plan)
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
# ONE-CLICK RENEWAL (for trusted payers)
# =============================================================================

def one_click_renewal(user_id: int, plan: str = None) -> dict:
    """
    One-click renewal for trusted payers (users with 2+ verified payments).

    This creates a pending payment that the user can then confirm with a single
    comprobante upload, without needing to re-enter payment details.

    If they have a very high trust level (gold+), we can even auto-approve
    based on their payment history.
    """
    now = datetime.utcnow()

    with UnitOfWork() as uow:
        user = uow.users.get(user_id)
        if not user:
            return {"error": "Usuario no encontrado"}

        # Check if user has one-click renewal enabled
        if not user.one_click_renewal_enabled:
            return {
                "error": "No tienes habilitada la renovación con un clic",
                "required_payments": 2,
                "current_payments": user.verified_payments_count or 0,
            }

        # Use current plan if not specified
        if not plan:
            plan = normalize_plan(user.plan)
            if plan not in Config.PLANS or Config.PLANS[plan]["price"] <= 0:
                plan = "cazador"  # Default to starter paid plan

        plan = normalize_plan(plan)
        if plan not in Config.PLANS:
            return {"error": "Plan inválido"}

        plan_info = Config.PLANS[plan]
        amount = plan_info["price"]

        if amount <= 0:
            return {"error": "Plan gratuito no requiere pago"}

        # Apply referral discount if any
        discount = _get_referral_discount(user_id)
        if discount > 0:
            amount = int(amount * (1 - discount))

        # Generate reference
        reference = generate_payment_reference(user_id, plan, amount)

        # Create pending payment marked as one-click renewal
        payment = Payment(
            user_id=user_id,
            amount=amount,
            currency="COP",
            type="subscription",
            wompi_ref=reference,
            status="pending",
            metadata_json={
                "plan": plan,
                "discount": discount,
                "method": "one_click_renewal",
                "trust_level": user.trust_level,
            },
        )
        uow.payments.create(payment)
        uow.commit()
        payment_id = payment.id

    logger.info(f"One-click renewal initiated: user={user_id}, plan={plan}, payment={payment_id}")

    # Return same info as regular checkout but with one-click flag
    return {
        "ok": True,
        "one_click": True,
        "payment_id": payment_id,
        "reference": reference,
        "amount": amount,
        "amount_display": f"${amount:,.0f}".replace(",", "."),
        "plan": plan,
        "message": "Transferencia lista. Sube tu comprobante para renovar tu plan.",
        "payment_methods": _get_payment_methods(),
    }


def _get_payment_methods() -> dict:
    """Get available payment methods from config."""
    methods = {}
    if Config.NEQUI_NUMBER:
        methods["nequi"] = {
            "number": Config.NEQUI_NUMBER,
            "name": "Nequi",
        }
    if Config.BANCOLOMBIA_ACCOUNT:
        methods["bancolombia"] = {
            "account": Config.BANCOLOMBIA_ACCOUNT,
            "type": Config.BANCOLOMBIA_TYPE,
            "holder": Config.BANCOLOMBIA_HOLDER,
            "name": "Bancolombia",
        }
    return methods


# =============================================================================
# ADMIN ACTIVATION
# =============================================================================

def admin_activate(user_id: int, plan: str) -> dict:
    """Admin manually activates a subscription after verifying payment."""
    plan = normalize_plan(plan)
    if plan not in Config.PLANS:
        return {"error": "Plan inválido"}

    plan_info = Config.PLANS[plan]
    amount = plan_info["price"]
    now = datetime.utcnow()

    # FIX: Capture user_email inside session to avoid DetachedInstanceError
    user_email = None

    with UnitOfWork() as uow:
        user = uow.users.get(user_id)
        if not user:
            return {"error": "Usuario no encontrado"}

        user_email = user.email  # Capture before session closes

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

    # Invalidate user cache so new plan takes effect
    cache.delete_pattern(f"user:{user_id}:*")
    cache.delete_pattern(f"matched:{user_id}:*")

    # Send confirmation email
    from core.tasks import task_send_email
    task_send_email.delay(
        user_email,
        "payment_confirmed",
        {"plan": plan, "amount": amount},
    )

    logger.info(f"Subscription activated by admin: user={user_id}, plan={plan}")
    return {"ok": True, "plan": plan, "user_id": user_id}


def admin_approve_payment(payment_id: int) -> dict:
    """Admin approves a payment that was flagged for manual review."""
    now = datetime.utcnow()
    user_email = None
    plan = None
    payment_amount = None

    with UnitOfWork() as uow:
        payment = uow.payments.get(payment_id)
        if not payment:
            return {"error": "Pago no encontrado"}
        if payment.status != "review":
            return {"error": f"Este pago no está en revisión (status: {payment.status})"}

        plan = payment.metadata_json.get("plan")
        if not plan or plan not in Config.PLANS:
            return {"error": "Plan inválido en el pago"}

        user_id = payment.user_id
        payment_amount = payment.amount

        # Approve the payment
        payment.status = "approved"
        payment.confirmed_at = now
        payment.verification_status = "admin_approved"

        # Deactivate previous subscriptions
        prev = uow.subscriptions.get_active_for_user(user_id)
        if prev:
            prev.status = "cancelled"

        # Create new subscription (30 days)
        sub = Subscription(
            user_id=user_id,
            plan=plan,
            status="active",
            amount=payment_amount,
            starts_at=now,
            ends_at=now + timedelta(days=30),
        )
        uow.subscriptions.create(sub)

        # Update user plan
        user = uow.users.get(user_id)
        if not user:
            return {"error": "Usuario no encontrado"}
        user.plan = plan
        user_email = user.email

        uow.commit()

        # Track referral
        try:
            from services.referrals import track_subscription
            track_subscription(user_id)
        except Exception:
            pass

    # Invalidate cache
    cache.delete_pattern(f"user:{user_id}:*")
    cache.delete_pattern(f"matched:{user_id}:*")

    # Send confirmation email
    from core.tasks import task_send_email
    task_send_email.delay(
        user_email,
        "payment_confirmed",
        {"plan": plan, "amount": payment_amount},
    )

    logger.info(f"Payment approved by admin: payment={payment_id}, plan={plan}")
    return {"ok": True, "plan": plan, "payment_id": payment_id}


def admin_reject_payment(payment_id: int, reason: str = "") -> dict:
    """Admin rejects a payment that was flagged for manual review."""
    user_email = None
    plan = None

    with UnitOfWork() as uow:
        payment = uow.payments.get(payment_id)
        if not payment:
            return {"error": "Pago no encontrado"}
        if payment.status not in ("pending", "review"):
            return {"error": f"Este pago no puede ser rechazado (status: {payment.status})"}

        plan = payment.metadata_json.get("plan")
        user_id = payment.user_id

        # Reject the payment
        payment.status = "declined"
        payment.verification_status = "admin_rejected"
        if reason:
            verification = payment.verification_result or {}
            verification["admin_rejection_reason"] = reason
            payment.verification_result = verification

        user = uow.users.get(user_id)
        if user:
            user_email = user.email

        uow.commit()

    # Notify user of rejection
    if user_email:
        from core.tasks import task_send_email
        task_send_email.delay(
            user_email,
            "payment_rejected",
            {"plan": plan, "reason": reason or "El comprobante no pudo ser verificado."},
        )

    logger.info(f"Payment rejected by admin: payment={payment_id}, reason={reason}")
    return {"ok": True, "payment_id": payment_id}


def get_payments_for_review() -> list[dict]:
    """Get all payments that need manual review."""
    with UnitOfWork() as uow:
        payments = (
            uow.session.query(Payment)
            .filter(Payment.status == "review")
            .order_by(Payment.created_at.desc())
            .all()
        )

        result = []
        for p in payments:
            user = uow.users.get(p.user_id)
            result.append({
                "id": p.id,
                "user_id": p.user_id,
                "user_email": user.email if user else None,
                "amount": p.amount,
                "plan": p.metadata_json.get("plan"),
                "reference": p.wompi_ref,
                "comprobante_url": p.comprobante_url,
                "verification_result": p.verification_result,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            })

        return result


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
