"""
Wompi payment gateway integration for automatic plan activation.

Flow:
1. User selects plan → GET /payments/wompi/link?plan=competidor
   → Backend returns a Wompi checkout URL with encoded reference
2. User pays on Wompi → Wompi fires POST /payments/wompi/webhook
3. Backend verifies checksum, activates plan automatically
4. User is redirected to /payments/success?reference=...

Wompi docs: https://docs.wompi.co/
Reference format: jobper_{user_id}_{plan}_{nonce}
"""

from __future__ import annotations

import hashlib
import logging
import os
from datetime import datetime, timedelta

from core.database import Subscription, UnitOfWork, User

logger = logging.getLogger(__name__)

WOMPI_EVENTS_SECRET = os.environ.get("WOMPI_EVENTS_SECRET", "")
WOMPI_PUBLIC_KEY    = os.environ.get("WOMPI_PUBLIC_KEY", "")

PLAN_PRICES_COP = {
    "cazador":    29_900 * 100,   # Wompi uses centavos
    "competidor": 149_900 * 100,
    "estratega":  299_900 * 100,
    "dominador":  599_900 * 100,
}


def build_checkout_url(user_id: int, plan: str) -> dict:
    """
    Return a Wompi-hosted checkout URL.
    The reference encodes user_id + plan so the webhook can activate automatically.
    """
    if plan not in PLAN_PRICES_COP:
        return {"error": f"Plan inválido: {plan}"}

    if not WOMPI_PUBLIC_KEY:
        return {"error": "Pasarela de pago no configurada. Contacta a soporte."}

    import secrets
    nonce = secrets.token_hex(6)
    reference = f"jobper_{user_id}_{plan}_{nonce}"
    amount_cents = PLAN_PRICES_COP[plan]

    # Wompi widget redirect URL — works without backend SDK
    base = "https://checkout.wompi.co/p/"
    redirect_url = os.environ.get("APP_URL", "https://www.jobper.com.co") + "/payments/success"
    url = (
        f"{base}?public-key={WOMPI_PUBLIC_KEY}"
        f"&currency=COP"
        f"&amount-in-cents={amount_cents}"
        f"&reference={reference}"
        f"&redirect-url={redirect_url}"
    )
    return {"url": url, "reference": reference}


def verify_wompi_signature(data: dict) -> bool:
    """
    Verify Wompi webhook checksum.
    checksum = SHA256(prop1_value + prop2_value + ... + events_secret)
    """
    if not WOMPI_EVENTS_SECRET:
        logger.warning("WOMPI_EVENTS_SECRET not set — skipping signature check (dev mode)")
        return True  # Allow in dev; tighten in prod

    try:
        sig = data.get("signature", {})
        checksum = sig.get("checksum", "")
        props = sig.get("properties", [])

        # Walk the data dict with dot notation keys
        def get_nested(d, dotted_key):
            parts = dotted_key.split(".")
            v = d
            for p in parts:
                v = v.get(p, "")
            return str(v)

        concat = "".join(get_nested(data, p) for p in props) + WOMPI_EVENTS_SECRET
        expected = hashlib.sha256(concat.encode()).hexdigest()
        return expected == checksum
    except Exception as e:
        logger.error(f"Wompi signature check failed: {e}")
        return False


def process_webhook(payload: dict) -> dict:
    """
    Process a Wompi webhook event.
    Activates the plan if transaction is APPROVED.
    """
    if not verify_wompi_signature(payload):
        return {"error": "Firma inválida", "status": 401}

    event_type = payload.get("event", "")
    if event_type != "transaction.updated":
        return {"ok": True, "skipped": True}

    tx = payload.get("data", {}).get("transaction", {})
    status    = tx.get("status", "")
    reference = tx.get("reference", "")
    tx_id     = tx.get("id", "")

    logger.info(f"Wompi webhook: event={event_type} status={status} ref={reference}")

    if status != "APPROVED":
        return {"ok": True, "status": status}

    # Parse reference: jobper_{user_id}_{plan}_{nonce}
    parts = reference.split("_")
    if len(parts) < 4 or parts[0] != "jobper":
        logger.error(f"Wompi: unrecognized reference format: {reference}")
        return {"ok": True, "skipped": True}

    try:
        user_id = int(parts[1])
        plan    = parts[2]
    except (ValueError, IndexError):
        logger.error(f"Wompi: could not parse user_id/plan from reference: {reference}")
        return {"ok": True, "skipped": True}

    if plan not in PLAN_PRICES_COP:
        logger.error(f"Wompi: unknown plan in reference: {plan}")
        return {"ok": True, "skipped": True}

    # Activate plan
    result = _activate_plan(user_id, plan, tx_id)
    logger.info(f"Wompi: activated plan={plan} user={user_id} → {result}")
    return result


def _activate_plan(user_id: int, plan: str, tx_id: str) -> dict:
    """Same logic as admin_change_plan — idempotent."""
    with UnitOfWork() as uow:
        user = uow.users.get(user_id)
        if not user:
            return {"error": f"Usuario {user_id} no encontrado"}

        # Idempotency: don't re-activate if already on this plan with active sub
        existing = (
            uow.session.query(Subscription)
            .filter(
                Subscription.user_id == user_id,
                Subscription.plan == plan,
                Subscription.status == "active",
                Subscription.ends_at > datetime.utcnow(),
            )
            .first()
        )
        if existing:
            logger.info(f"Wompi: plan {plan} already active for user {user_id}, skipping")
            return {"ok": True, "skipped": "already_active"}

        old_plan = user.plan
        user.plan = plan

        now = datetime.utcnow()
        sub = Subscription(
            user_id=user_id,
            plan=plan,
            status="active",
            amount=PLAN_PRICES_COP.get(plan, 0) // 100,  # store in COP not centavos
            starts_at=now,
            ends_at=now + timedelta(days=30),
        )
        uow.session.add(sub)
        uow.commit()

    return {"ok": True, "old_plan": old_plan, "new_plan": plan, "tx_id": tx_id}
