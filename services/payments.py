"""
Jobper Services — Payments (Manual: Nequi / Bancolombia transfer)
User uploads comprobante → AI verifies → system activates if valid.
Includes duplicate detection and fraud prevention.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import text as _sa_text

from config import Config
from core.cache import cache
from core.database import Payment, Subscription, UnitOfWork, User
from core.plans import normalize_plan, PLAN_ORDER
from services.receipt_verification import compute_image_hash, generate_payment_reference, verify_payment_receipt

logger = logging.getLogger(__name__)


# =============================================================================
# PAYMENT-SPECIFIC CONSTANTS
# =============================================================================

# Trust levels based on verified payments count
TRUST_LEVELS = {
    0: "new",  # No verified payments yet
    1: "bronze",  # 1 verified payment
    2: "silver",  # 2 verified payments → one-click renewal enabled
    4: "gold",  # 4+ verified payments
    8: "platinum",  # 8+ verified payments (loyal customer)
}


def get_plans() -> list[dict]:
    """Return available plans with pricing."""
    return [{"key": k, **v} for k, v in Config.PLANS.items()]


def check_feature_access(user_plan: str, feature: str) -> bool:
    """Check if a plan has access to a feature."""
    required_plan = Config.FEATURE_GATES.get(feature)
    if not required_plan:
        return True  # Feature not gated

    normalized_user = normalize_plan(user_plan)
    normalized_req = normalize_plan(required_plan)

    user_level = PLAN_ORDER.get(normalized_user, -1)
    req_level = PLAN_ORDER.get(normalized_req, 0)
    return user_level >= req_level


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
    now = datetime.now(timezone.utc)
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
            rewards.append(
                {
                    "type": "level_up",
                    "old_level": old_level,
                    "new_level": new_level,
                    "message": f"¡Subiste a nivel {new_level.title()}!",
                }
            )

        # Enable one-click renewal at silver level (2+ verified payments)
        if user.verified_payments_count >= 2 and not user.one_click_renewal_enabled:
            user.one_click_renewal_enabled = True
            rewards.append(
                {
                    "type": "feature_unlock",
                    "feature": "one_click_renewal",
                    "message": "¡Desbloqueaste la renovación con un clic!",
                }
            )

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
        # Cancel any existing pending payments for this user (keep admin panel clean)
        uow.session.query(Payment).filter(
            Payment.user_id == user_id,
            Payment.status == "pending",
        ).update({"status": "cancelled"}, synchronize_session=False)

        # Create pending payment
        payment = Payment(
            user_id=user_id,
            amount=amount,
            currency="COP",
            type="subscription",
            reference=reference,
            status="pending",
            metadata_json={"plan": plan, "discount": discount, "method": "manual"},
        )
        uow.payments.create(payment)
        uow.commit()
        payment_id = payment.id

    # Determine which payment method to show based on config
    payment_methods = {}
    # Bre-B is the primary payment method (interbank instant transfer)
    if Config.BREB_HANDLE:
        payment_methods["breb"] = {
            "handle": Config.BREB_HANDLE,
            "name": "Bre-B",
        }
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
    now = datetime.now(timezone.utc)

    # Validate payment exists and belongs to user
    with UnitOfWork() as uow:
        payment = uow.payments.get(payment_id)
        if not payment:
            return {"error": "Pago no encontrado"}
        if payment.user_id != user_id:
            return {"error": "Pago no pertenece a este usuario"}
        if payment.status not in ("pending", "review"):
            return {"error": "Este pago ya fue procesado"}

        plan = (payment.metadata_json or {}).get("plan")
        if not plan or plan not in Config.PLANS:
            return {"error": "Plan inválido en el pago"}

        # Capture values for verification
        payment_amount = payment.amount
        payment_ref = payment.reference

        # FRAUD: Rate limit — max 3 comprobante uploads per user per 24 hours
        cutoff_24h = now - timedelta(hours=24)
        recent_uploads = (
            uow.session.query(Payment)
            .filter(
                Payment.user_id == user_id,
                Payment.comprobante_url.isnot(None),
                Payment.created_at >= cutoff_24h,
            )
            .count()
        )
        if recent_uploads >= 3:
            logger.warning(f"FRAUD: Rate limit hit — user={user_id} tried {recent_uploads} uploads in 24h")
            return {
                "error": "Demasiados intentos en 24 horas. Contacta soporte@jobper.co si el problema persiste."
            }

    # Verify the receipt with AI
    verification = verify_payment_receipt(
        user_id=user_id,
        payment_id=payment_id,
        image_path=comprobante_path,
    )

    # Handle verification result
    if not verification["valid"]:
        confidence = verification.get("verification", {}).get("confidence", 0)

        if verification.get("grace_eligible"):
            # SECURITY: Check for grace period abuse (prevent repeated fake receipts)
            with UnitOfWork() as uow:
                grace_abuse_window = now - timedelta(days=30)
                recent_grace_count = (
                    uow.session.query(Subscription)
                    .filter(
                        Subscription.user_id == user_id,
                        Subscription.status.in_(["grace", "cancelled"]),
                        Subscription.starts_at >= grace_abuse_window,
                    )
                    .count()
                )
                if recent_grace_count >= 2:
                    logger.warning(
                        f"FRAUD: Grace abuse detected — user={user_id} has {recent_grace_count} grace periods in 30 days"
                    )
                    payment = uow.payments.get(payment_id)
                    if payment:
                        payment.status = "review"
                        payment.comprobante_url = comprobante_path
                        payment.verification_status = "flagged_abuse"
                        payment.verification_result = verification.get("verification", {})
                        uow.commit()
                    return {
                        "error": "Tu pago requiere revisión manual. Te contactaremos pronto.",
                        "requires_manual_review": True,
                    }

            # Comprobante looks plausible (72-95% confidence) — grant 24h grace access
            # Admin must confirm before grace expires; if not, access is revoked.
            grace_until = now + timedelta(hours=24)
            with UnitOfWork() as uow:
                payment = uow.payments.get(payment_id)
                if payment:
                    payment.status = "grace"
                    payment.comprobante_url = comprobante_path
                    payment.verification_status = "grace_review"
                    payment.verification_result = verification.get("verification", {})
                    meta = payment.metadata_json or {}
                    meta["grace_until"] = grace_until.isoformat()
                    payment.metadata_json = meta
                    uow.commit()

                # Advisory lock: prevent duplicate grace subs from concurrent uploads
                try:
                    uow.session.execute(_sa_text("SELECT pg_advisory_xact_lock(:uid)"), {"uid": user_id})
                except Exception:
                    pass  # SQLite / non-PG fallback: no lock but rare race is acceptable

                # Only create grace sub if user has no active subscription already
                existing_active = uow.subscriptions.get_active_for_user(user_id)
                if not existing_active:
                    # Cancel any previous grace sub for this user
                    prev_grace = (
                        uow.session.query(Subscription)
                        .filter(Subscription.user_id == user_id, Subscription.status == "grace")
                        .first()
                    )
                    if prev_grace:
                        prev_grace.status = "cancelled"

                    grace_sub = Subscription(
                        user_id=user_id,
                        plan=plan,
                        status="grace",
                        amount=payment_amount,
                        starts_at=now,
                        ends_at=grace_until,
                    )
                    uow.subscriptions.create(grace_sub)

                    user = uow.users.get(user_id)
                    if user:
                        user.plan = plan

                    uow.commit()

            # Notify admin
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
                    "confidence": confidence,
                    "grace": True,
                },
            )
            cache.delete_pattern(f"user:{user_id}:*")
            logger.info(f"Payment grace period granted: user={user_id}, payment={payment_id}, until={grace_until}")
            return {
                "ok": True,
                "status": "grace",
                "plan": plan,
                "grace_until": grace_until.isoformat(),
                "message": (
                    "Tu pago está siendo verificado. Tienes acceso al plan durante 24 horas "
                    "mientras confirmamos el pago. Te avisaremos por email."
                ),
            }

        elif verification.get("requires_review"):
            # Low confidence or suspicious — no access, just queue for admin review
            with UnitOfWork() as uow:
                payment = uow.payments.get(payment_id)
                if payment:
                    payment.status = "review"
                    payment.comprobante_url = comprobante_path
                    payment.verification_status = "manual_review"
                    payment.verification_result = verification.get("verification", {})
                    uow.commit()

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
                    "confidence": confidence,
                    "grace": False,
                },
            )
            logger.warning(
                f"Payment flagged for review (low confidence): user={user_id}, payment={payment_id}, conf={confidence:.0%}"
            )
            return {
                "ok": False,
                "status": "review",
                "message": "Tu comprobante está en revisión manual. Te notificaremos en máximo 24 horas.",
                "issues": verification.get("issues", []),
            }

        else:
            # Clearly invalid / fraud — reject, allow retry
            with UnitOfWork() as uow:
                payment = uow.payments.get(payment_id)
                if payment:
                    payment.verification_status = "rejected"
                    payment.verification_result = verification.get("verification", {})
                    uow.commit()

            logger.warning(
                f"Payment rejected (invalid receipt): user={user_id}, payment={payment_id}, issues={verification.get('issues')}"
            )
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
            logger.info(
                f"Trust updated: user={user_id}, points={trust_update.get('points_earned')}, level={trust_update.get('trust_level')}"
            )

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

    reference = f"JOB-{user_id}-{plan}-{int(datetime.now(timezone.utc).timestamp())}"

    with UnitOfWork() as uow:
        payment = Payment(
            user_id=user_id,
            amount=amount,
            currency="COP",
            type="subscription",
            reference=reference,
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
    now = datetime.now(timezone.utc)

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
            reference=reference,
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
        "currency": "COP",
        "plan": plan,
        "message": "Transferencia lista. Sube tu comprobante para renovar tu plan.",
        "instructions": (
            f"1. Transfiere exactamente {f'${amount:,.0f}'.replace(',', '.')} COP\n"
            f"2. En la descripción/concepto pon: {reference}\n"
            f"3. Sube tu comprobante para activar tu plan"
        ),
        "reference_instructions": (
            f"IMPORTANTE: Incluye este código en la descripción de tu transferencia:\n{reference}"
        ),
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
    now = datetime.now(timezone.utc)

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
    now = datetime.now(timezone.utc)
    user_email = None
    plan = None
    payment_amount = None

    with UnitOfWork() as uow:
        payment = uow.payments.get(payment_id)
        if not payment:
            return {"error": "Pago no encontrado"}
        if payment.status not in ("review", "grace", "pending"):
            return {"error": f"Este pago no está pendiente de aprobación (status: {payment.status})"}

        plan = (payment.metadata_json or {}).get("plan")
        if not plan or plan not in Config.PLANS:
            return {"error": "Plan inválido en el pago"}

        user_id = payment.user_id
        payment_amount = payment.amount

        # Approve the payment — check status BEFORE overwriting
        was_grace = payment.status == "grace"
        payment.status = "approved"
        payment.confirmed_at = now
        payment.verification_status = "admin_approved"

        if was_grace:
            # Grace → extend existing grace subscription to full 30 days
            grace_sub = (
                uow.session.query(Subscription)
                .filter(Subscription.user_id == user_id, Subscription.status == "grace")
                .first()
            )
            if grace_sub:
                grace_sub.status = "active"
                grace_sub.ends_at = now + timedelta(days=30)
            else:
                # Fallback: create fresh subscription
                prev = uow.subscriptions.get_active_for_user(user_id)
                if prev:
                    prev.status = "cancelled"
                sub = Subscription(
                    user_id=user_id, plan=plan, status="active",
                    amount=payment_amount, starts_at=now, ends_at=now + timedelta(days=30),
                )
                uow.subscriptions.create(sub)
        else:
            # Review (no grace sub exists) → create fresh subscription
            prev = uow.subscriptions.get_active_for_user(user_id)
            if prev:
                prev.status = "cancelled"
            sub = Subscription(
                user_id=user_id, plan=plan, status="active",
                amount=payment_amount, starts_at=now, ends_at=now + timedelta(days=30),
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
        if payment.status not in ("pending", "review", "grace"):
            return {"error": f"Este pago no puede ser rechazado (status: {payment.status})"}

        plan = (payment.metadata_json or {}).get("plan")
        user_id = payment.user_id
        was_grace = payment.status == "grace"

        # Reject the payment
        payment.status = "declined"
        payment.verification_status = "admin_rejected"
        if reason:
            verification = payment.verification_result or {}
            verification["admin_rejection_reason"] = reason
            payment.verification_result = verification

        # If grace: revoke the temporary subscription and revert user plan
        if was_grace:
            grace_sub = (
                uow.session.query(Subscription)
                .filter(Subscription.user_id == user_id, Subscription.status == "grace")
                .first()
            )
            if grace_sub:
                grace_sub.status = "cancelled"

        user = uow.users.get(user_id)
        if user:
            user_email = user.email
            # Revert plan to free if grace is being revoked and plan was set by this grace
            if was_grace and user.plan == plan:
                user.plan = "free"

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
    """Get all payments pending admin review (review, grace, and pending status)."""
    with UnitOfWork() as uow:
        payments = (
            uow.session.query(Payment)
            .filter(Payment.status.in_(["review", "grace", "pending"]))
            .order_by(Payment.created_at.desc())
            .all()
        )

        result = []
        for p in payments:
            user = uow.users.get(p.user_id)
            meta = p.metadata_json or {}
            result.append(
                {
                    "id": p.id,
                    "user_id": p.user_id,
                    "user_email": user.email if user else None,
                    "amount": p.amount,
                    "plan": meta.get("plan"),
                    "reference": p.reference,
                    "comprobante_url": p.comprobante_url,
                    "verification": p.verification_result,
                    "verification_status": p.verification_status,
                    "status": p.status,
                    "grace_until": meta.get("grace_until"),
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                }
            )

        return result


def get_user_payment_status(user_id: int) -> dict:
    """Return pending/grace payment info for the user (used by frontend for status banner)."""
    with UnitOfWork() as uow:
        payment = (
            uow.session.query(Payment)
            .filter(
                Payment.user_id == user_id,
                Payment.status.in_(["grace", "review", "pending"]),
            )
            .order_by(Payment.created_at.desc())
            .first()
        )

        if not payment:
            return {"pending": False}

        meta = payment.metadata_json or {}
        result = {
            "pending": True,
            "status": payment.status,
            "plan": meta.get("plan"),
            "amount": payment.amount,
            "payment_id": payment.id,
            "created_at": payment.created_at.isoformat() if payment.created_at else None,
        }

        if payment.status == "grace":
            result["grace_until"] = meta.get("grace_until")
            # Check if grace subscription is still alive
            grace_sub = (
                uow.session.query(Subscription)
                .filter(Subscription.user_id == user_id, Subscription.status == "grace")
                .first()
            )
            result["grace_active"] = bool(grace_sub and grace_sub.ends_at > datetime.now(timezone.utc))

        return result


def admin_batch_approve_today() -> dict:
    """
    Approve ALL grace/review payments submitted in the last 24h — one-button daily workflow.
    Admin opens Bre-B, verifies all arrived, clicks this button.
    """
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=24)
    approved = 0
    skipped = []

    with UnitOfWork() as uow:
        pending_ids = [
            p.id
            for p in uow.session.query(Payment)
            .filter(
                Payment.status.in_(["grace", "review"]),
                Payment.created_at >= cutoff,
            )
            .all()
        ]

    for payment_id in pending_ids:
        result = admin_approve_payment(payment_id)
        if "error" in result:
            skipped.append({"payment_id": payment_id, "error": result["error"]})
        else:
            approved += 1
            logger.info(f"Batch approved payment {payment_id}")

    logger.info(f"Batch approval complete: approved={approved}, skipped={len(skipped)}")
    return {"ok": True, "approved": approved, "skipped": skipped, "total": len(pending_ids)}


def check_grace_periods() -> dict:
    """
    Scheduler task: revoke grace subscriptions that expired without admin approval.
    Call this every hour from the background scheduler.
    """
    now = datetime.now(timezone.utc)
    revoked = 0

    with UnitOfWork() as uow:
        expired_subs = (
            uow.session.query(Subscription)
            .filter(
                Subscription.status == "grace",
                Subscription.ends_at <= now,
            )
            .all()
        )

        for sub in expired_subs:
            user = uow.users.get(sub.user_id)
            if user and user.plan == sub.plan:
                user.plan = "free"
                # Notify user that grace expired
                from core.tasks import task_send_email
                task_send_email.delay(
                    user.email,
                    "grace_expired",
                    {"plan": sub.plan},
                )

            sub.status = "expired"
            revoked += 1

            # Also mark the payment as needing re-upload
            expired_payment = (
                uow.session.query(Payment)
                .filter(
                    Payment.user_id == sub.user_id,
                    Payment.status == "grace",
                )
                .order_by(Payment.created_at.desc())
                .first()
            )
            if expired_payment:
                expired_payment.status = "declined"
                expired_payment.verification_status = "grace_expired"

        uow.commit()

    if revoked:
        logger.info(f"Grace period expiry: revoked {revoked} temporary subscriptions")
        # Invalidate cache for affected users
        from core.cache import cache
        # (cache invalidation per-user happens above when plan changes)

    return {"revoked": revoked}


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
                    "days_remaining": (user.trial_ends_at - datetime.now(timezone.utc)).days,
                }
            return None

        days_remaining = max(0, (sub.ends_at - datetime.now(timezone.utc)).days)
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
    """Cancel active subscription (remains active until end date, status stays active)."""
    with UnitOfWork() as uow:
        sub = uow.subscriptions.get_active_for_user(user_id)
        if not sub:
            return {"error": "No hay suscripción activa"}

        sub.auto_renew = False
        # Keep status="active" until ends_at passes — don't revoke paid access early
        uow.commit()

    cache.delete_pattern(f"user:{user_id}:*")
    return {"ok": True, "message": "Auto-renovación desactivada. Tu acceso continúa hasta fin de período."}


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
    now = datetime.now(timezone.utc)
    from core.tasks import task_send_email

    with UnitOfWork() as uow:
        active_subs = uow.session.query(Subscription).filter(Subscription.status == "active").all()

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
                task_send_email.delay(
                    user.email,
                    "subscription_expired",
                    {
                        "plan": sub.plan,
                    },
                )
                continue

            # 7 days reminder
            if days_left <= 7 and days_left > 3:
                if not already_reminded or already_reminded.date() < today - timedelta(days=3):
                    sub.renewal_reminded_at = now
                    task_send_email.delay(
                        user.email,
                        "renewal_reminder",
                        {
                            "days_left": days_left,
                            "plan": sub.plan,
                            "amount": sub.amount,
                        },
                    )

            # 3 days reminder (urgent)
            elif days_left <= 3 and days_left > 0:
                if not already_reminded or already_reminded.date() < today - timedelta(days=1):
                    sub.renewal_reminded_at = now
                    task_send_email.delay(
                        user.email,
                        "renewal_urgent",
                        {
                            "days_left": days_left,
                            "plan": sub.plan,
                            "amount": sub.amount,
                        },
                    )
                    # Also send push + WhatsApp
                    try:
                        from services.notifications import send_push, send_whatsapp_renewal_reminder

                        send_push(
                            user.id,
                            f"Tu plan vence en {days_left} día{'s' if days_left > 1 else ''}",
                            "Renueva para no perder acceso.",
                            "/payments",
                        )
                        send_whatsapp_renewal_reminder(user.id, days_left, sub.plan)
                    except Exception:
                        pass

        uow.commit()

    logger.info("Renewal check completed")
