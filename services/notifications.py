"""
Jobper Services — Email (Resend) + Web Push notifications
"""

from __future__ import annotations

import html
import json
import logging
from datetime import datetime

import requests

from config import Config
from core.database import UnitOfWork

logger = logging.getLogger(__name__)


def _escape(text: str) -> str:
    """Escape HTML to prevent XSS in email templates."""
    if not text:
        return ""
    return html.escape(str(text))


# =============================================================================
# EMAIL VIA RESEND (API, no SDK)
# =============================================================================

RESEND_API = "https://api.resend.com/emails"

# Retry config for transient failures
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 1


def send_email(to: str, template: str, data: dict, retry: int = 0) -> bool:
    """
    Send transactional email via Resend API.

    IMPORTANT: If using Resend's sandbox domain (onboarding@resend.dev),
    emails only send to verified addresses in the Resend dashboard.
    For production, configure your own domain in Resend.
    """
    import time

    if not Config.RESEND_API_KEY:
        logger.warning("Resend API key not configured, skipping email")
        return False

    # Validate email format (basic check)
    if not to or "@" not in to:
        logger.error(f"Invalid email address: {to}")
        return False

    subject, html = _render_template(template, data)

    try:
        resp = requests.post(
            RESEND_API,
            headers={
                "Authorization": f"Bearer {Config.RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "from": Config.RESEND_FROM_EMAIL,
                "to": [to],
                "subject": subject,
                "html": html,
            },
            timeout=15,  # Increased timeout
        )

        if resp.status_code in (200, 201):
            logger.info(f"Email sent: {template} → {to}")
            return True

        # Handle specific error codes
        error_body = resp.text
        logger.error(f"Resend error {resp.status_code}: {error_body}")

        # Sandbox domain warning
        if "not authorized" in error_body.lower() or "verify" in error_body.lower():
            logger.warning(
                f"Resend may be rejecting email to {to} - "
                "sandbox domain only sends to verified emails. "
                "Configure a custom domain in Resend for production."
            )

        # Retry on server errors (5xx) or rate limits (429)
        if resp.status_code in (429, 500, 502, 503, 504) and retry < MAX_RETRIES:
            time.sleep(RETRY_DELAY_SECONDS * (retry + 1))
            return send_email(to, template, data, retry + 1)

        return False

    except requests.exceptions.Timeout:
        logger.error(f"Email send timeout to {to}")
        if retry < MAX_RETRIES:
            time.sleep(RETRY_DELAY_SECONDS)
            return send_email(to, template, data, retry + 1)
        return False

    except requests.exceptions.RequestException as e:
        logger.error(f"Email send failed (network): {e}")
        if retry < MAX_RETRIES:
            time.sleep(RETRY_DELAY_SECONDS)
            return send_email(to, template, data, retry + 1)
        return False

    except Exception as e:
        logger.error(f"Email send failed: {e}")
        return False


# =============================================================================
# EMAIL TEMPLATES
# =============================================================================


def _render_template(template: str, data: dict) -> tuple[str, str]:
    """Return (subject, html) for a template."""
    templates = {
        "magic_link": _tmpl_magic_link,
        "welcome": _tmpl_welcome,
        "contract_alert": _tmpl_contract_alert,
        "trial_expiring": _tmpl_trial_expiring,
        "weekly_report": _tmpl_weekly_report,
        "payment_confirmed": _tmpl_payment_confirmed,
        "subscription_expiring": _tmpl_subscription_expiring,
        "payment_request": _tmpl_payment_request,
        "daily_digest": _tmpl_daily_digest,
        "renewal_reminder": _tmpl_renewal_reminder,
        "renewal_urgent": _tmpl_renewal_urgent,
        "subscription_expired": _tmpl_subscription_expired,
        # Payment verification templates
        "payment_review_needed": _tmpl_payment_review_needed,
        "payment_auto_approved": _tmpl_payment_auto_approved,
        "payment_rejected": _tmpl_payment_rejected,
    }

    fn = templates.get(template)
    if not fn:
        return f"Jobper — {template}", f"<p>{data}</p>"

    return fn(data)


def _base_html(content: str) -> str:
    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f4f4f5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif">
<div style="max-width:560px;margin:40px auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.1)">
<div style="background:#0f172a;padding:24px 32px">
  <h1 style="color:#fff;margin:0;font-size:20px;font-weight:600">Jobper</h1>
</div>
<div style="padding:32px">
{content}
</div>
<div style="padding:16px 32px;background:#f8fafc;text-align:center;font-size:12px;color:#94a3b8">
  Jobper — Haz crecer tu empresa con los contratos correctos<br>
  <a href="{Config.FRONTEND_URL}" style="color:#3b82f6;text-decoration:none">jobper.co</a>
</div>
</div>
</body>
</html>"""


def _button(url: str, text: str) -> str:
    return f'<a href="{url}" style="display:inline-block;padding:12px 24px;background:#3b82f6;color:#fff;text-decoration:none;border-radius:8px;font-weight:600;margin:16px 0">{text}</a>'


def _tmpl_magic_link(data: dict) -> tuple[str, str]:
    url = data.get("url", "")
    # FIX: Config is 60 minutes, not 15. Also add fallback link for email clients that block buttons.
    content = f"""
<h2 style="margin:0 0 8px;color:#0f172a;font-size:18px">Inicia sesión en Jobper</h2>
<p style="color:#475569;line-height:1.6">Haz clic en el botón para acceder a tu cuenta. Este enlace expira en 60 minutos.</p>
{_button(url, "Iniciar sesión")}
<p style="color:#94a3b8;font-size:13px">Si no solicitaste este enlace, puedes ignorar este correo.</p>
<p style="color:#64748b;font-size:12px;margin-top:12px;border-top:1px solid #e2e8f0;padding-top:12px">¿El botón no funciona? Copia y pega este enlace en tu navegador:<br><span style="color:#3b82f6;word-break:break-all">{_escape(url)}</span></p>
"""
    return "Tu enlace de acceso a Jobper", _base_html(content)


def _tmpl_welcome(data: dict) -> tuple[str, str]:
    name = data.get("name", "")
    greeting = f"Hola {name}," if name else "Hola,"
    content = f"""
<h2 style="margin:0 0 8px;color:#0f172a;font-size:18px">Bienvenido a Jobper</h2>
<p style="color:#475569;line-height:1.6">{greeting}</p>
<p style="color:#475569;line-height:1.6">Tienes <strong>14 días gratis</strong> para explorar contratos, recibir alertas y hacer crecer tu empresa.</p>
<p style="color:#475569;line-height:1.6">Empieza configurando tu perfil para recibir contratos relevantes.</p>
{_button(Config.FRONTEND_URL + "/dashboard", "Ir al Dashboard")}
"""
    return "Bienvenido a Jobper — Tu CRM de contratos", _base_html(content)


def _tmpl_contract_alert(data: dict) -> tuple[str, str]:
    # FIX: Escape user-provided data to prevent XSS
    title = _escape(data.get("title", "Nuevo contrato"))
    entity = _escape(data.get("entity", ""))
    amount = data.get("amount", "")
    url = data.get("url", Config.FRONTEND_URL)
    match_pct = int(data.get("match_score", 0))

    amount_str = f"${amount:,.0f} COP" if amount else "No especificado"
    content = f"""
<h2 style="margin:0 0 8px;color:#0f172a;font-size:18px">Nuevo contrato relevante</h2>
<div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;padding:16px;margin:12px 0">
  <p style="margin:0 0 4px;font-weight:600;color:#166534">Match: {match_pct}%</p>
  <p style="margin:0 0 8px;font-weight:600;color:#0f172a;font-size:16px">{title}</p>
  <p style="margin:0;color:#475569">{entity}</p>
  <p style="margin:4px 0 0;color:#475569;font-weight:600">{amount_str}</p>
</div>
{_button(url, "Ver contrato")}
"""
    return f"Contrato relevante: {_escape(title[:60])}", _base_html(content)


def _tmpl_trial_expiring(data: dict) -> tuple[str, str]:
    days_left = data.get("days_left", 0)
    content = f"""
<h2 style="margin:0 0 8px;color:#0f172a;font-size:18px">Tu prueba gratis termina en {days_left} días</h2>
<p style="color:#475569;line-height:1.6">No pierdas acceso a contratos, alertas y análisis de mercado.</p>
<p style="color:#475569;line-height:1.6">Elige un plan desde <strong>$29.900/mes</strong> y sigue creciendo.</p>
{_button(Config.FRONTEND_URL + "/payments", "Ver planes")}
"""
    return f"Tu prueba gratis termina en {days_left} días", _base_html(content)


def _tmpl_weekly_report(data: dict) -> tuple[str, str]:
    count = int(data.get("count", 0))
    top = data.get("top_contracts", [])

    # FIX: Escape user-provided data to prevent XSS
    contracts_html = ""
    for c in top[:5]:
        title = _escape(str(c.get("title", ""))[:80])
        entity = _escape(str(c.get("entity", "")))
        amount = _escape(str(c.get("amount", "N/A")))
        contracts_html += f"""
<div style="border-bottom:1px solid #e2e8f0;padding:12px 0">
  <p style="margin:0;font-weight:600;color:#0f172a">{title}</p>
  <p style="margin:4px 0 0;color:#475569;font-size:13px">{entity} — {amount}</p>
</div>"""

    content = f"""
<h2 style="margin:0 0 8px;color:#0f172a;font-size:18px">Reporte semanal</h2>
<p style="color:#475569;line-height:1.6">Esta semana encontramos <strong>{count} contratos</strong> relevantes para tu empresa.</p>
{contracts_html}
{_button(Config.FRONTEND_URL + "/dashboard", "Ver todos")}
"""
    return f"Reporte semanal — {count} contratos nuevos", _base_html(content)


def _tmpl_subscription_expiring(data: dict) -> tuple[str, str]:
    days_left = data.get("days_left", 0)
    plan = data.get("plan", "")
    content = f"""
<h2 style="margin:0 0 8px;color:#0f172a;font-size:18px">Tu plan {plan.title()} vence en {days_left} días</h2>
<p style="color:#475569;line-height:1.6">Para seguir accediendo a contratos, alertas y todas las funcionalidades, renueva tu suscripción.</p>
<p style="color:#475569;line-height:1.6">Puedes renovar desde la app con Nequi o transferencia Bancolombia.</p>
{_button(Config.FRONTEND_URL + "/payments", "Renovar ahora")}
<p style="color:#94a3b8;font-size:13px">Si no renuevas, tu cuenta pasará al plan gratuito al vencer el período.</p>
"""
    return f"Tu plan vence en {days_left} días — Renueva ahora", _base_html(content)


def _tmpl_payment_request(data: dict) -> tuple[str, str]:
    user_id = data.get("user_id", "")
    plan = data.get("plan", "")
    amount = data.get("amount", 0)
    reference = data.get("reference", "")
    content = f"""
<h2 style="margin:0 0 8px;color:#0f172a;font-size:18px">Nueva solicitud de pago</h2>
<p style="color:#475569;line-height:1.6">Un usuario reportó haber realizado un pago manual.</p>
<div style="background:#f0f9ff;border:1px solid #bae6fd;border-radius:8px;padding:16px;margin:12px 0">
  <p style="margin:0 0 4px;color:#0f172a"><strong>Usuario ID:</strong> {user_id}</p>
  <p style="margin:0 0 4px;color:#0f172a"><strong>Plan:</strong> {plan}</p>
  <p style="margin:0 0 4px;color:#0f172a"><strong>Monto:</strong> ${amount:,.0f} COP</p>
  <p style="margin:0;color:#0f172a"><strong>Referencia:</strong> {reference}</p>
</div>
<p style="color:#475569;line-height:1.6">Verifica el pago en Nequi/Bancolombia y activa el plan desde el panel de admin.</p>
{_button(Config.FRONTEND_URL + "/admin", "Ir al Admin")}
"""
    return f"Solicitud de pago — {reference}", _base_html(content)


def _tmpl_payment_confirmed(data: dict) -> tuple[str, str]:
    plan = data.get("plan", "")
    amount = data.get("amount", 0)
    content = f"""
<h2 style="margin:0 0 8px;color:#0f172a;font-size:18px">Pago confirmado</h2>
<p style="color:#475569;line-height:1.6">Tu plan <strong>{plan.title()}</strong> está activo.</p>
<p style="color:#475569;line-height:1.6">Monto: <strong>${amount:,.0f} COP</strong></p>
{_button(Config.FRONTEND_URL + "/dashboard", "Ir al Dashboard")}
"""
    return "Pago confirmado — Jobper", _base_html(content)


def _tmpl_payment_review_needed(data: dict) -> tuple[str, str]:
    """Admin notification: payment needs manual review."""
    user_id = data.get("user_id", "")
    payment_id = data.get("payment_id", "")
    plan = data.get("plan", "")
    amount = data.get("amount", 0)
    reference = data.get("reference", "")
    issues = data.get("issues", [])
    confidence = data.get("confidence", 0)

    issues_html = "".join(f"<li style='color:#dc2626'>{_escape(issue)}</li>" for issue in issues)

    content = f"""
<h2 style="margin:0 0 8px;color:#f59e0b;font-size:18px">⚠️ Pago requiere revisión manual</h2>
<p style="color:#475569;line-height:1.6">Un comprobante de pago no pudo ser verificado automáticamente.</p>
<div style="background:#fef3c7;border:1px solid #fcd34d;border-radius:8px;padding:16px;margin:12px 0">
  <p style="margin:0 0 4px;color:#0f172a"><strong>Usuario ID:</strong> {user_id}</p>
  <p style="margin:0 0 4px;color:#0f172a"><strong>Payment ID:</strong> {payment_id}</p>
  <p style="margin:0 0 4px;color:#0f172a"><strong>Plan:</strong> {plan}</p>
  <p style="margin:0 0 4px;color:#0f172a"><strong>Monto esperado:</strong> ${amount:,.0f} COP</p>
  <p style="margin:0 0 4px;color:#0f172a"><strong>Referencia:</strong> {reference}</p>
  <p style="margin:0;color:#0f172a"><strong>Confianza IA:</strong> {confidence:.0%}</p>
</div>
<p style="color:#475569;font-weight:600">Problemas detectados:</p>
<ul style="color:#dc2626;margin:8px 0">{issues_html}</ul>
<p style="color:#475569;line-height:1.6">Revisa el comprobante y aprueba o rechaza el pago desde el panel de admin.</p>
{_button(Config.FRONTEND_URL + "/admin/payments", "Revisar pagos")}
"""
    return f"⚠️ Pago requiere revisión — {reference}", _base_html(content)


def _tmpl_payment_auto_approved(data: dict) -> tuple[str, str]:
    """Admin notification: payment was auto-approved by AI."""
    user_id = data.get("user_id", "")
    plan = data.get("plan", "")
    amount = data.get("amount", 0)
    reference = data.get("reference", "")
    confidence = data.get("confidence", 0)

    content = f"""
<h2 style="margin:0 0 8px;color:#16a34a;font-size:18px">✅ Pago auto-aprobado</h2>
<p style="color:#475569;line-height:1.6">Un pago fue verificado y aprobado automáticamente.</p>
<div style="background:#dcfce7;border:1px solid #86efac;border-radius:8px;padding:16px;margin:12px 0">
  <p style="margin:0 0 4px;color:#0f172a"><strong>Usuario ID:</strong> {user_id}</p>
  <p style="margin:0 0 4px;color:#0f172a"><strong>Plan:</strong> {plan}</p>
  <p style="margin:0 0 4px;color:#0f172a"><strong>Monto:</strong> ${amount:,.0f} COP</p>
  <p style="margin:0 0 4px;color:#0f172a"><strong>Referencia:</strong> {reference}</p>
  <p style="margin:0;color:#0f172a"><strong>Confianza IA:</strong> {confidence:.0%}</p>
</div>
<p style="color:#94a3b8;font-size:13px">Este pago fue verificado automáticamente. El comprobante queda guardado para auditoría.</p>
"""
    return f"✅ Pago auto-aprobado — {reference}", _base_html(content)


def _tmpl_payment_rejected(data: dict) -> tuple[str, str]:
    """User notification: their payment was rejected."""
    plan = data.get("plan", "")
    reason = data.get("reason", "El comprobante no pudo ser verificado.")

    content = f"""
<h2 style="margin:0 0 8px;color:#dc2626;font-size:18px">Pago no verificado</h2>
<p style="color:#475569;line-height:1.6">No pudimos verificar tu comprobante de pago para el plan <strong>{plan.title()}</strong>.</p>
<div style="background:#fef2f2;border:1px solid #fecaca;border-radius:8px;padding:16px;margin:12px 0">
  <p style="margin:0;color:#dc2626"><strong>Motivo:</strong> {_escape(reason)}</p>
</div>
<p style="color:#475569;line-height:1.6">Puedes intentar nuevamente con un comprobante más claro, o contactarnos si crees que es un error.</p>
{_button(Config.FRONTEND_URL + "/payments", "Intentar de nuevo")}
<p style="color:#94a3b8;font-size:13px">Si tienes dudas, responde a este correo o escríbenos a soporte@jobper.co</p>
"""
    return "Pago no verificado — Jobper", _base_html(content)


# =============================================================================
# WEB PUSH
# =============================================================================


def send_push(user_id: int, title: str, body: str, url: str = "") -> bool:
    """Send web push notification to all user's subscriptions."""
    if not Config.VAPID_PRIVATE_KEY:
        return False

    try:
        from pywebpush import WebPushException, webpush

        with UnitOfWork() as uow:
            subs = uow.push_subs.session.query(uow.push_subs.model).filter_by(user_id=user_id).all()

            if not subs:
                return False

            payload = json.dumps(
                {
                    "title": title,
                    "body": body,
                    "url": url or Config.FRONTEND_URL,
                    "icon": f"{Config.FRONTEND_URL}/icon-192.png",
                }
            )

            for sub in subs:
                try:
                    webpush(
                        subscription_info={
                            "endpoint": sub.endpoint,
                            "keys": {"p256dh": sub.p256dh, "auth": sub.auth},
                        },
                        data=payload,
                        vapid_private_key=Config.VAPID_PRIVATE_KEY,
                        vapid_claims={"sub": Config.VAPID_CLAIMS_EMAIL},
                    )
                except WebPushException as e:
                    if "410" in str(e) or "404" in str(e):
                        uow.push_subs.delete(sub)
                    else:
                        logger.warning(f"Push failed for sub {sub.id}: {e}")

            uow.commit()

        return True
    except ImportError:
        logger.warning("pywebpush not installed")
        return False
    except Exception as e:
        logger.error(f"Push notification failed: {e}")
        return False


def register_push_subscription(user_id: int, subscription_info: dict) -> dict:
    """Register a new push subscription for a user."""
    from core.database import PushSubscription

    with UnitOfWork() as uow:
        sub = PushSubscription(
            user_id=user_id,
            endpoint=subscription_info["endpoint"],
            p256dh=subscription_info["keys"]["p256dh"],
            auth=subscription_info["keys"]["auth"],
        )
        uow.push_subs.create(sub)
        uow.commit()

    return {"ok": True}


# =============================================================================
# WHATSAPP (Meta Cloud API)
# =============================================================================

WHATSAPP_API = "https://graph.facebook.com/v21.0"


def send_whatsapp(to: str, message: str) -> bool:
    """
    Send a WhatsApp message via Meta Cloud API.
    `to` must be international format: +573001234567
    """
    if not Config.WHATSAPP_API_TOKEN or not Config.WHATSAPP_PHONE_ID:
        return False

    # Normalize Colombian numbers
    number = to.strip().replace(" ", "").replace("-", "")
    if number.startswith("0"):
        number = "+57" + number[1:]
    elif not number.startswith("+"):
        number = "+57" + number

    try:
        resp = requests.post(
            f"{WHATSAPP_API}/{Config.WHATSAPP_PHONE_ID}/messages",
            headers={
                "Authorization": f"Bearer {Config.WHATSAPP_API_TOKEN}",
                "Content-Type": "application/json",
            },
            json={
                "messaging_product": "whatsapp",
                "to": number,
                "type": "text",
                "text": {"body": message},
            },
            timeout=10,
        )
        if resp.status_code in (200, 201):
            logger.info(f"WhatsApp sent to {number[:8]}***")
            return True
        else:
            logger.error(f"WhatsApp error {resp.status_code}: {resp.text}")
            return False
    except Exception as e:
        logger.error(f"WhatsApp send failed: {e}")
        return False


def send_whatsapp_contract_alert(user_id: int, contract: dict) -> bool:
    """Send a WhatsApp alert for a matching contract."""
    with UnitOfWork() as uow:
        user = uow.users.get(user_id)
        if not user or not user.whatsapp_enabled or not user.whatsapp_number:
            return False

    title = contract.get("title", "")[:100]
    entity = contract.get("entity", "")
    amount = contract.get("amount")
    url = contract.get("url", Config.FRONTEND_URL)

    amount_str = f"${amount:,.0f} COP" if amount else "No especificado"

    msg = f"📋 *Nuevo contrato relevante*\n\n" f"*{title}*\n" f"🏢 {entity}\n" f"💰 {amount_str}\n\n" f"👉 {url}"
    return send_whatsapp(user.whatsapp_number, msg)


def send_whatsapp_renewal_reminder(user_id: int, days_left: int, plan: str) -> bool:
    """Send WhatsApp renewal reminder."""
    with UnitOfWork() as uow:
        user = uow.users.get(user_id)
        if not user or not user.whatsapp_enabled or not user.whatsapp_number:
            return False

    urgency = "mañana" if days_left <= 1 else f"en {days_left} días"
    msg = (
        f"⚠️ Tu plan *{plan}* vence {urgency}.\n\n"
        f"Renueva para seguir recibiendo contratos, alertas y match score.\n\n"
        f"👉 {Config.FRONTEND_URL}/payments"
    )
    return send_whatsapp(user.whatsapp_number, msg)


# =============================================================================
# BULK ALERTS
# =============================================================================


def send_contract_alert_to_matching_users(contract: dict):
    """Send alert to users whose profile matches this contract (>70% match).
    Respects weekly alert limit for free tier users (3/week).
    """
    from core.tasks import task_send_email, task_send_push

    with UnitOfWork() as uow:
        users = uow.users.get_active_with_notifications()
        alerts_sent = 0

        for user in users:
            # Simple keyword matching (semantic matching done separately)
            score = _quick_match_score(user, contract)
            if score >= 70:
                # Check if user can receive more alerts (free tier limit)
                if not uow.users.can_receive_alert(user):
                    logger.debug(f"User {user.id} hit weekly alert limit, skipping")
                    continue

                task_send_email.delay(
                    user.email,
                    "contract_alert",
                    {
                        "title": contract.get("title", ""),
                        "entity": contract.get("entity", ""),
                        "amount": contract.get("amount"),
                        "match_score": score,
                        "url": f"{Config.FRONTEND_URL}/contracts/{contract.get('id', '')}",
                    },
                )
                task_send_push.delay(
                    user.id,
                    "Nuevo contrato relevante",
                    contract.get("title", "")[:100],
                    f"{Config.FRONTEND_URL}/contracts/{contract.get('id', '')}",
                )

                # WhatsApp alert (if enabled)
                if user.whatsapp_enabled and user.whatsapp_number:
                    try:
                        send_whatsapp_contract_alert(
                            user.id,
                            {
                                **contract,
                                "url": f"{Config.FRONTEND_URL}/contracts/{contract.get('id', '')}",
                            },
                        )
                    except Exception:
                        pass  # Non-blocking

                # Increment alert count for this user
                uow.users.increment_alert_count(user)
                alerts_sent += 1

        # Commit the alert count updates
        uow.commit()
        logger.info(f"Sent {alerts_sent} alerts for contract {contract.get('id', 'unknown')}")


def _quick_match_score(user, contract: dict) -> int:
    """Quick keyword-based match score (0-100)."""
    if not user.keywords:
        return 0

    text = f"{contract.get('title', '')} {contract.get('description', '')}".lower()
    matches = sum(1 for kw in user.keywords if kw.lower() in text)
    total = len(user.keywords)

    if total == 0:
        return 0

    return min(100, int((matches / total) * 100))


# =============================================================================
# DAILY DIGEST
# =============================================================================


def send_daily_digest():
    """
    Send daily email digest to eligible users (Alertas plan and above).
    Includes top matching contracts from the last 24 hours.
    """
    from core.middleware import PLAN_ORDER
    from services.matching import get_matched_contracts

    with UnitOfWork() as uow:
        # Get users with Alertas plan or higher
        users = uow.users.get_active_with_notifications()
        sent_count = 0
        skipped_count = 0

        for user in users:
            # Daily digest only for alertas+ plans
            user_plan_level = PLAN_ORDER.get(user.plan, 0)
            alertas_level = PLAN_ORDER.get("alertas", 2)

            if user_plan_level < alertas_level:
                skipped_count += 1
                continue

            try:
                # Get top matched contracts for this user
                matched = get_matched_contracts(user.id, min_score=50, limit=10, days_back=1)

                if not matched:
                    continue

                # Format contracts for email
                top_contracts = []
                for c in matched[:5]:
                    top_contracts.append(
                        {
                            "title": c.get("title", "")[:100],
                            "entity": c.get("entity", ""),
                            "amount": f"${c.get('amount', 0):,.0f} COP" if c.get("amount") else "N/A",
                            "match_score": c.get("match_score", 0),
                        }
                    )

                if top_contracts:
                    send_email(
                        user.email,
                        "daily_digest",
                        {
                            "count": len(matched),
                            "top_contracts": top_contracts,
                            "name": user.company_name or "",
                        },
                    )
                    sent_count += 1

            except Exception as e:
                logger.error(f"Daily digest failed for user {user.id}: {e}")

        logger.info(f"Daily digest: sent={sent_count}, skipped={skipped_count}")
        return {"sent": sent_count, "skipped": skipped_count}


def _tmpl_daily_digest(data: dict) -> tuple[str, str]:
    """Daily digest email template."""
    count = data.get("count", 0)
    top = data.get("top_contracts", [])
    name = data.get("name", "")

    greeting = f"Hola {name}," if name else "Hola,"

    contracts_html = ""
    for c in top[:5]:
        score_color = (
            "#16a34a" if c.get("match_score", 0) >= 80 else "#3b82f6" if c.get("match_score", 0) >= 60 else "#6b7280"
        )
        contracts_html += f"""
<div style="border-bottom:1px solid #e2e8f0;padding:12px 0">
  <div style="display:flex;justify-content:space-between;align-items:center">
    <p style="margin:0;font-weight:600;color:#0f172a">{c.get('title', '')[:80]}</p>
    <span style="background:{score_color};color:#fff;padding:2px 8px;border-radius:12px;font-size:11px;font-weight:600">{c.get('match_score', 0)}%</span>
  </div>
  <p style="margin:4px 0 0;color:#475569;font-size:13px">{c.get('entity', '')} — {c.get('amount', 'N/A')}</p>
</div>"""

    content = f"""
<h2 style="margin:0 0 8px;color:#0f172a;font-size:18px">Digest diario</h2>
<p style="color:#475569;line-height:1.6">{greeting}</p>
<p style="color:#475569;line-height:1.6">Hoy encontramos <strong>{count} contratos</strong> que coinciden con tu perfil. Aquí los mejores:</p>
{contracts_html}
{_button(Config.FRONTEND_URL + "/contracts", "Ver todos los contratos")}
<p style="color:#94a3b8;font-size:12px;margin-top:16px">Recibes este email porque tienes el plan Alertas o superior. <a href="{Config.FRONTEND_URL}/settings" style="color:#3b82f6">Ajustar notificaciones</a></p>
"""
    return f"Digest diario — {count} contratos para ti", _base_html(content)


def _tmpl_renewal_reminder(data: dict) -> tuple[str, str]:
    """Soft renewal reminder — sent 7 days before expiry."""
    days_left = data.get("days_left", 7)
    plan = data.get("plan", "")
    amount = data.get("amount", 0)
    content = f"""
<h2 style="margin:0 0 8px;color:#0f172a;font-size:18px">Tu plan {plan.title()} vence en {days_left} días</h2>
<p style="color:#475569;line-height:1.6">Para seguir disfrutando de contratos ilimitados, alertas personalizadas y todas las funcionalidades de tu plan, renueva antes de que expire.</p>
<div style="background:#f0f9ff;border:1px solid #bae6fd;border-radius:8px;padding:16px;margin:12px 0">
  <p style="margin:0 0 4px;color:#0369a1;font-weight:600">Renovación</p>
  <p style="margin:0;color:#0f172a">Plan {plan.title()} — ${amount:,.0f} COP/mes</p>
</div>
<p style="color:#475569;line-height:1.6">Renueva en segundos con Nequi o Bancolombia desde la app.</p>
{_button(Config.FRONTEND_URL + "/payments", "Renovar ahora")}
<p style="color:#94a3b8;font-size:13px">Si no renuevas, tu cuenta pasará al plan gratuito al vencer el período.</p>
"""
    return f"Tu plan vence en {days_left} días — Renueva tu suscripción", _base_html(content)


def _tmpl_renewal_urgent(data: dict) -> tuple[str, str]:
    """Urgent renewal reminder — sent 1-3 days before expiry."""
    days_left = data.get("days_left", 1)
    plan = data.get("plan", "")
    amount = data.get("amount", 0)
    urgency = "mañana" if days_left <= 1 else f"en {days_left} días"
    content = f"""
<div style="background:#fef2f2;border:1px solid #fecaca;border-radius:8px;padding:16px;margin:0 0 16px">
  <p style="margin:0;color:#991b1b;font-weight:600;font-size:16px">⚠️ Tu plan vence {urgency}</p>
</div>
<h2 style="margin:0 0 8px;color:#0f172a;font-size:18px">Último aviso: tu plan {plan.title()} está por expirar</h2>
<p style="color:#475569;line-height:1.6">Si no renuevas, perderás acceso a:</p>
<ul style="color:#475569;line-height:1.8">
  <li>Contratos completos con descripción y documentos</li>
  <li>Alertas personalizadas ilimitadas</li>
  <li>Match score y filtros avanzados</li>
  <li>Exportar contratos a Excel</li>
</ul>
<p style="color:#475569;line-height:1.6"><strong>Renueva ahora</strong> por solo ${amount:,.0f} COP/mes.</p>
{_button(Config.FRONTEND_URL + "/payments", "Renovar ahora — No pierdas acceso")}
"""
    return f"⚠️ ÚLTIMO AVISO: tu plan vence {urgency}", _base_html(content)


def _tmpl_subscription_expired(data: dict) -> tuple[str, str]:
    """Notification that subscription expired and user downgraded to free."""
    plan = data.get("plan", "")
    content = f"""
<h2 style="margin:0 0 8px;color:#0f172a;font-size:18px">Tu plan {plan.title()} ha expirado</h2>
<p style="color:#475569;line-height:1.6">Tu suscripción al plan {plan.title()} venció y tu cuenta ahora está en el <strong>plan gratuito</strong>.</p>
<p style="color:#475569;line-height:1.6">Con el plan gratuito puedes:</p>
<ul style="color:#475569;line-height:1.8">
  <li>Ver títulos de contratos (sin descripción completa)</li>
  <li>5 búsquedas por día</li>
  <li>3 alertas por semana</li>
</ul>
<p style="color:#475569;line-height:1.6">¿Quieres recuperar tu acceso completo? Reactiva tu plan en cualquier momento.</p>
{_button(Config.FRONTEND_URL + "/payments", "Reactivar mi plan")}
<p style="color:#94a3b8;font-size:13px">No te preocupes, tus favoritos y configuración están guardados.</p>
"""
    return f"Tu plan {plan.title()} ha expirado", _base_html(content)
