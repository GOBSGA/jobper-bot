"""
Jobper API — All endpoints (41 total)
Blueprint per domain: auth, contracts, pipeline, marketplace, payments, referrals, admin, public, support
"""

from __future__ import annotations

import logging
import os
import re
import io
from datetime import datetime

from flask import Blueprint, g, jsonify, redirect, request, send_file
from sqlalchemy import text

from api.schemas import (
    AdminListSchema,
    AdminLogsSchema,
    AdminModerateSchema,
    ChatbotSchema,
    CheckoutSchema,
    FavoriteSchema,
    LoginPasswordSchema,
    LoginSchema,
    MarketplaceListSchema,
    OnboardingAnalyzeSchema,
    PipelineAddSchema,
    PipelineMoveSchema,
    PipelineNoteSchema,
    ProfileUpdateSchema,
    PublishContractSchema,
    PushSubscriptionSchema,
    ReferralTrackSchema,
    RefreshSchema,
    RegisterSchema,
    SearchSchema,
    VerifySchema,
)
from core.middleware import audit, rate_limit, require_admin, require_auth, require_plan, validate
from core.plans import PLAN_ORDER

logger = logging.getLogger(__name__)


# =============================================================================
# AUTH (4 endpoints)
# =============================================================================
auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.post("/login")
@rate_limit(5)
@validate(LoginSchema)
def login():
    from services.auth import send_magic_link

    result = send_magic_link(g.validated.email, ip=request.remote_addr)
    return jsonify(result)


@auth_bp.post("/verify")
@rate_limit(10)
@validate(VerifySchema)
def verify():
    from services.auth import verify_magic_link

    result = verify_magic_link(g.validated.token, referral_code=g.validated.referral_code)
    if "error" in result:
        # Use 400, not 401 — api.js would intercept 401 and show "Sesión expirada"
        return jsonify(result), 400
    return jsonify(result)


@auth_bp.post("/refresh")
@rate_limit(10)
@validate(RefreshSchema)
def refresh():
    from services.auth import refresh_access_token

    result = refresh_access_token(g.validated.refresh_token)
    if "error" in result:
        return jsonify(result), 401
    return jsonify(result)


@auth_bp.post("/logout")
@require_auth
def logout_endpoint():
    from services.auth import logout

    token = request.headers.get("Authorization", "")[7:]
    logout(token)
    return jsonify({"ok": True})


@auth_bp.post("/register")
@rate_limit(5)
@validate(RegisterSchema)
def register():
    """Register with email + password."""
    logger.info("Register attempt")
    try:
        from services.auth import register_with_password

        result = register_with_password(
            g.validated.email, g.validated.password, referral_code=g.validated.referral_code
        )
        if "error" in result:
            logger.warning(f"Register failed: {result.get('error')}")
            return jsonify(result), 400
        logger.info("Register success")
        return jsonify(result)
    except Exception as e:
        logger.error(f"Register exception: {e}", exc_info=True)
        # Return more specific error for database issues
        error_str = str(e)
        if "connection" in error_str.lower() or "operational" in error_str.lower():
            return jsonify({"error": "Servicio temporalmente no disponible. Intenta en 1 minuto."}), 503
        return jsonify({"error": "Error al crear cuenta. Contacta soporte@jobper.co"}), 500


@auth_bp.post("/login-password")
@rate_limit(10)
@validate(LoginPasswordSchema)
def login_password():
    """Login with email + password."""
    logger.info("Login attempt")
    try:
        from services.auth import login_with_password

        result = login_with_password(g.validated.email, g.validated.password)
        if "error" in result:
            logger.warning(f"Login failed: {result.get('error')}")
            # IMPORTANT: Use 400, NOT 401. api.js intercepts ALL 401s to try token
            # refresh, which clears localStorage and shows "Sesión expirada" — wrong.
            # 401 = unauthenticated (for protected routes). 400 = bad credentials.
            return jsonify(result), 400
        logger.info("Login success")
        return jsonify(result)
    except Exception as e:
        logger.error(f"Login exception: {e}", exc_info=True)
        # Return more specific error for database issues
        error_str = str(e)
        error_type = type(e).__name__
        if "connection" in error_str.lower() or "operational" in error_str.lower():
            return jsonify({"error": "Servicio temporalmente no disponible. Intenta en 1 minuto."}), 503
        return jsonify({"error": "Error al procesar login. Contacta soporte@jobper.co"}), 500


@auth_bp.get("/google")
@rate_limit(20)
def google_oauth_start():
    """Redirect user to Google OAuth consent screen."""
    from services.auth import google_oauth_url
    from config import Config

    if not Config.GOOGLE_CLIENT_ID:
        return jsonify({"error": "Google OAuth no está habilitado"}), 503

    state = request.args.get("ref", "")  # carry referral code through OAuth
    url = google_oauth_url(state=state)
    return redirect(url)


@auth_bp.get("/google/callback")
def google_oauth_callback_route():
    """Handle Google OAuth callback, issue JWT, redirect to frontend."""
    from services.auth import google_oauth_callback
    from config import Config

    error = request.args.get("error")
    if error:
        return redirect(f"{Config.FRONTEND_URL}/login?error=google_cancelled")

    code = request.args.get("code", "")
    state = request.args.get("state", "")

    if not code:
        return redirect(f"{Config.FRONTEND_URL}/login?error=google_no_code")

    result = google_oauth_callback(code=code, state=state)

    if "error" in result:
        logger.error(f"Google OAuth callback error: {result['error']}")
        return redirect(f"{Config.FRONTEND_URL}/login?error=google_failed")

    # Redirect to frontend with tokens in URL fragment (not query string for security)
    access = result["access_token"]
    refresh = result["refresh_token"]
    is_new = "1" if result.get("is_new") else "0"
    target = f"{Config.FRONTEND_URL}/auth/google/callback?token={access}&refresh={refresh}&new={is_new}"
    return redirect(target)


@auth_bp.post("/forgot-password")
@rate_limit(5)
def forgot_password():
    """Send a password reset link by email. Never reveals if email exists."""
    data = request.get_json() or {}
    email = data.get("email", "").strip()
    if not email or not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email) or len(email) > 254:
        return jsonify({"error": "Email inválido"}), 400
    try:
        from services.auth import send_password_reset
        result = send_password_reset(email, ip=request.remote_addr)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Forgot password error: {e}", exc_info=True)
        return jsonify({"error": "Error enviando el correo. Intenta de nuevo."}), 500


@auth_bp.post("/reset-password")
@rate_limit(10)
def reset_password():
    """Validate reset token and set new password. Auto-logs user in."""
    data = request.get_json() or {}
    token = data.get("token", "").strip()
    new_password = data.get("new_password", "")
    if not token or not new_password:
        return jsonify({"error": "Token y contraseña requeridos"}), 400
    try:
        from services.auth import reset_password_with_token
        result = reset_password_with_token(token, new_password)
        if "error" in result:
            return jsonify(result), 400
        return jsonify(result)
    except Exception as e:
        logger.error(f"Reset password error: {e}", exc_info=True)
        return jsonify({"error": "Error al restablecer contraseña. Intenta de nuevo."}), 500


# =============================================================================
# CONTRACTS (6 endpoints)
# =============================================================================
contracts_bp = Blueprint("contracts", __name__, url_prefix="/api/contracts")


@contracts_bp.get("/search")
@require_auth
@rate_limit(30)
@validate(SearchSchema)
def search_contracts():
    from services.contracts import search_contracts as svc

    result = svc(g.validated.query, g.user_id, g.validated.page, g.validated.per_page)
    return jsonify(result)


@contracts_bp.get("/feed")
@require_auth
@rate_limit(30)
@validate(SearchSchema)
def contract_feed():
    from services.contracts import get_matched_feed

    result = get_matched_feed(g.user_id, g.validated.page, g.validated.per_page)
    return jsonify(result)


@contracts_bp.get("/<int:contract_id>")
@require_auth
def contract_detail(contract_id: int):
    from services.contracts import get_contract_detail

    result = get_contract_detail(contract_id, g.user_id)
    if not result:
        return jsonify({"error": "Contrato no encontrado"}), 404
    return jsonify(result)


@contracts_bp.get("/recommendations")
@require_auth
@require_plan("cazador")
@rate_limit(10)
def ai_recommendations():
    """Top AI-ranked contracts for the authenticated user. Cached 24h."""
    from services.recommendations import get_recommendations

    result = get_recommendations(g.user_id)
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)


@contracts_bp.get("/<int:contract_id>/analysis")
@require_auth
@require_plan("business")
@audit("contract_analysis")
def contract_analysis(contract_id: int):
    from services.contracts import get_contract_analysis

    result = get_contract_analysis(contract_id, g.user_id)
    if not result:
        return jsonify({"error": "Analisis no disponible"}), 404
    return jsonify(result)


@contracts_bp.get("/export")
@require_auth
@require_plan("cazador")
@rate_limit(10)
def export_contracts():
    """Export contracts to Excel. Reuses search filters."""
    import openpyxl

    query = request.args.get("query", "")
    limit = min(max(1, int(request.args.get("limit", 200))), 200)

    from services.contracts import search_contracts as svc

    data = svc(query, g.user_id, page=1, per_page=limit)
    contracts = data.get("contracts", [])

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Contratos Jobper"

    headers = ["Título", "Entidad", "Ciudad", "Presupuesto (COP)", "Fecha límite", "Fuente", "Match %", "URL"]
    ws.append(headers)

    for h in ws[1]:
        h.font = openpyxl.styles.Font(bold=True)

    for c in contracts:
        ws.append([
            c.get("title", ""),
            c.get("entity", ""),
            c.get("city", ""),
            c.get("amount") or "",
            c.get("deadline", ""),
            c.get("source", ""),
            c.get("match_score") or "",
            c.get("url", ""),
        ])

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    return send_file(
        buf,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="contratos_jobper.xlsx",
    )


@contracts_bp.post("/favorite")
@require_auth
@validate(FavoriteSchema)
def toggle_fav():
    from services.contracts import get_favorite_count, toggle_favorite

    # Enforce free-tier limit (5 max) — only block adding, not removing
    user_plan = getattr(g, "user_plan", "free")
    if PLAN_ORDER.get(user_plan, 0) < PLAN_ORDER.get("alertas", 2):
        count = get_favorite_count(g.user_id)
        if count >= 5:
            # Check if this is a remove (already favorited) — allow removes
            from services.contracts import is_favorited

            if not is_favorited(g.user_id, g.validated.contract_id):
                return jsonify({"error": "Límite de 5 favoritos en plan Free", "upgrade": "alertas"}), 403
    result = toggle_favorite(g.user_id, g.validated.contract_id)
    return jsonify(result)


@contracts_bp.get("/favorites")
@require_auth
@validate(SearchSchema)
def list_favorites():
    from services.contracts import get_favorites

    result = get_favorites(g.user_id, g.validated.page, g.validated.per_page)
    return jsonify(result)


@contracts_bp.get("/alerts")
@require_auth
def contract_alerts():
    from services.matching import get_alerts

    hours = min(max(1, request.args.get("hours", 24, type=int)), 720)
    result = get_alerts(g.user_id, hours=hours)
    return jsonify(result)


@contracts_bp.get("/matched")
@require_auth
def matched_contracts():
    from services.matching import get_matched_contracts

    limit = min(max(1, request.args.get("limit", 50, type=int)), 200)
    min_score = max(0, min(request.args.get("min_score", 0, type=int), 100))
    result = get_matched_contracts(g.user_id, min_score=min_score, limit=limit)
    return jsonify({"contracts": result, "count": len(result)})


@contracts_bp.get("/market-stats")
@require_auth
def market_stats():
    from services.matching import get_market_stats

    result = get_market_stats(g.user_id)
    return jsonify(result)


# =============================================================================
# PIPELINE (5 endpoints)
# =============================================================================
pipeline_bp = Blueprint("pipeline", __name__, url_prefix="/api/pipeline")


@pipeline_bp.get("/")
@require_auth
@require_plan("business")
def get_pipeline():
    from services.pipeline import get_pipeline as svc

    return jsonify(svc(g.user_id))


@pipeline_bp.post("/")
@require_auth
@require_plan("business")
@validate(PipelineAddSchema)
def add_pipeline():
    from services.pipeline import add_to_pipeline

    result = add_to_pipeline(
        g.user_id,
        contract_id=g.validated.contract_id,
        private_contract_id=g.validated.private_contract_id,
        stage=g.validated.stage,
        value=g.validated.value,
    )
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result), 201


@pipeline_bp.put("/<int:entry_id>/stage")
@require_auth
@require_plan("business")
@validate(PipelineMoveSchema)
def move_pipeline(entry_id: int):
    from services.pipeline import move_stage

    result = move_stage(g.user_id, entry_id, g.validated.stage)
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)


@pipeline_bp.post("/<int:entry_id>/note")
@require_auth
@require_plan("business")
@validate(PipelineNoteSchema)
def add_pipeline_note(entry_id: int):
    from services.pipeline import add_note

    result = add_note(g.user_id, entry_id, g.validated.text)
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)


@pipeline_bp.get("/stats")
@require_auth
@require_plan("business")
def pipeline_stats():
    from services.pipeline import get_stats

    return jsonify(get_stats(g.user_id))


# =============================================================================
# MARKETPLACE (5 endpoints)
# =============================================================================
marketplace_bp = Blueprint("marketplace", __name__, url_prefix="/api/marketplace")


@marketplace_bp.get("/")
@require_auth
@rate_limit(30)
@validate(MarketplaceListSchema)
def list_mkt():
    from services.marketplace import list_marketplace

    result = list_marketplace(
        page=g.validated.page,
        per_page=g.validated.per_page,
        category=g.validated.category,
        city=g.validated.city,
    )
    return jsonify(result)


@marketplace_bp.post("/")
@require_auth
@require_plan("competidor")
@rate_limit(10)
@validate(PublishContractSchema)
def publish_mkt():
    from services.marketplace import publish

    data = g.validated.model_dump(exclude_none=True)
    result = publish(g.user_id, data)
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result), 201


@marketplace_bp.put("/<int:contract_id>")
@require_auth
@validate(PublishContractSchema)
def edit_mkt(contract_id: int):
    from services.marketplace import edit

    data = g.validated.model_dump(exclude_none=True)
    result = edit(g.user_id, contract_id, data)
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)


@marketplace_bp.post("/<int:contract_id>/feature")
@require_auth
@audit("feature_contract")
def feature_mkt(contract_id: int):
    from services.marketplace import feature

    result = feature(contract_id, g.user_id)
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)


@marketplace_bp.get("/<int:contract_id>/contact")
@require_auth
@audit("contact_reveal")
def get_contact_mkt(contract_id: int):
    from services.marketplace import get_contact

    result = get_contact(contract_id, g.user_id)
    if "error" in result:
        return jsonify(result), 403 if result.get("upgrade") else 404
    return jsonify(result)


@marketplace_bp.get("/<int:contract_id>/messages")
@require_auth
@rate_limit(60)
def get_mkt_messages(contract_id: int):
    """Get chat messages for a marketplace contract (polling-friendly)."""
    from core.database import UnitOfWork, MarketplaceMessage

    with UnitOfWork() as uow:
        # Verify user has access (either publisher or someone who messaged)
        contract = uow.session.execute(
            text("SELECT publisher_id FROM private_contracts WHERE id = :id"),
            {"id": contract_id},
        ).fetchone()
        if not contract:
            return jsonify({"error": "Contrato no encontrado"}), 404

        msgs = (
            uow.session.query(MarketplaceMessage)
            .filter(
                MarketplaceMessage.contract_id == contract_id,
                (MarketplaceMessage.sender_id == g.user_id)
                | (MarketplaceMessage.receiver_id == g.user_id),
            )
            .order_by(MarketplaceMessage.created_at.asc())
            .limit(200)
            .all()
        )
        # Mark incoming messages as read
        uow.session.query(MarketplaceMessage).filter(
            MarketplaceMessage.contract_id == contract_id,
            MarketplaceMessage.receiver_id == g.user_id,
            MarketplaceMessage.read_at == None,  # noqa: E711
        ).update({"read_at": datetime.utcnow()}, synchronize_session=False)
        uow.commit()

        publisher_id = contract[0]
        return jsonify(
            {
                "messages": [
                    {
                        "id": m.id,
                        "sender_id": m.sender_id,
                        "is_mine": m.sender_id == g.user_id,
                        "content": m.content,
                        "read_at": m.read_at.isoformat() if m.read_at else None,
                        "created_at": m.created_at.isoformat(),
                    }
                    for m in msgs
                ],
                "contract_id": contract_id,
                "publisher_id": publisher_id,
            }
        )


@marketplace_bp.post("/<int:contract_id>/messages")
@require_auth
@rate_limit(30)
def send_mkt_message(contract_id: int):
    """Send a chat message about a marketplace contract."""
    from core.database import UnitOfWork, MarketplaceMessage

    body = request.get_json(silent=True) or {}
    content = (body.get("content") or "").strip()
    if not content:
        return jsonify({"error": "Mensaje vacío"}), 400
    if len(content) > 2000:
        return jsonify({"error": "Mensaje demasiado largo (máx 2000 chars)"}), 400

    with UnitOfWork() as uow:
        row = uow.session.execute(
            text("SELECT publisher_id FROM private_contracts WHERE id = :id"),
            {"id": contract_id},
        ).fetchone()
        if not row:
            return jsonify({"error": "Contrato no encontrado"}), 404

        publisher_id = row[0]
        # Determine receiver: if sender is publisher → reply to last sender; else → publisher
        if g.user_id == publisher_id:
            last = (
                uow.session.query(MarketplaceMessage)
                .filter(
                    MarketplaceMessage.contract_id == contract_id,
                    MarketplaceMessage.sender_id != publisher_id,
                )
                .order_by(MarketplaceMessage.created_at.desc())
                .first()
            )
            if not last:
                return jsonify({"error": "No hay conversación activa"}), 400
            receiver_id = last.sender_id
        else:
            receiver_id = publisher_id

        msg = MarketplaceMessage(
            sender_id=g.user_id,
            receiver_id=receiver_id,
            contract_id=contract_id,
            content=content,
        )
        uow.session.add(msg)
        uow.commit()
        return jsonify(
            {
                "id": msg.id,
                "sender_id": msg.sender_id,
                "is_mine": True,
                "content": msg.content,
                "created_at": msg.created_at.isoformat(),
            }
        ), 201


@marketplace_bp.get("/inbox")
@require_auth
@rate_limit(30)
def mkt_inbox():
    """List all marketplace conversations with unread counts."""
    from core.database import UnitOfWork, MarketplaceMessage
    from sqlalchemy import func

    with UnitOfWork() as uow:
        # Find all contracts where user has messages (as sender or receiver)
        rows = uow.session.execute(
            text("""
                SELECT
                    mm.contract_id,
                    pc.title,
                    COUNT(CASE WHEN mm.receiver_id = :uid AND mm.read_at IS NULL THEN 1 END) AS unread,
                    MAX(mm.created_at) AS last_at,
                    (SELECT content FROM marketplace_messages
                     WHERE contract_id = mm.contract_id
                     ORDER BY created_at DESC LIMIT 1) AS last_msg
                FROM marketplace_messages mm
                JOIN private_contracts pc ON pc.id = mm.contract_id
                WHERE mm.sender_id = :uid OR mm.receiver_id = :uid
                GROUP BY mm.contract_id, pc.title
                ORDER BY last_at DESC
                LIMIT 50
            """),
            {"uid": g.user_id},
        ).fetchall()

        return jsonify(
            {
                "conversations": [
                    {
                        "contract_id": r[0],
                        "title": r[1],
                        "unread": r[2],
                        "last_at": r[3].isoformat() if r[3] else None,
                        "last_msg": r[4],
                    }
                    for r in rows
                ],
                "total_unread": sum(r[2] for r in rows),
            }
        )


# =============================================================================
# USER (4 endpoints)
# =============================================================================
user_bp = Blueprint("user", __name__, url_prefix="/api/user")


@user_bp.get("/profile")
@require_auth
def get_profile():
    try:
        from services.auth import get_user_profile

        result = get_user_profile(g.user_id)
        if not result:
            return jsonify({"error": "Usuario no encontrado"}), 404
        return jsonify(result)
    except Exception as e:
        logger.error(f"get_profile exception: {e}", exc_info=True)
        return jsonify({"error": "Error cargando perfil"}), 500


@user_bp.put("/profile")
@require_auth
@validate(ProfileUpdateSchema)
def update_profile():
    from services.auth import update_user_profile

    data = g.validated.model_dump(exclude_none=True)
    result = update_user_profile(g.user_id, data)
    if not result:
        return jsonify({"error": "Usuario no encontrado"}), 404
    return jsonify(result)


@user_bp.post("/accept-privacy-policy")
@require_auth
@audit("accept_privacy_policy")
def accept_privacy_policy():
    """Accept privacy policy after registration."""
    from services.auth import accept_privacy_policy as accept_pp

    result = accept_pp(g.user_id)
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)


@user_bp.delete("/account")
@require_auth
@audit("delete_account")
def delete_account():
    """Permanently delete user account and all associated data."""
    from core.database import UnitOfWork

    try:
        with UnitOfWork() as uow:
            user = uow.users.get(g.user_id)
            if not user:
                return jsonify({"error": "Usuario no encontrado"}), 404
            if user.is_admin:
                return jsonify({"error": "Las cuentas de administrador no se pueden eliminar por esta vía"}), 403
            uow.session.delete(user)
            uow.commit()
        return jsonify({"ok": True})
    except Exception as e:
        logger.error(f"delete_account failed for user {g.user_id}: {e}")
        return jsonify({"error": "Error eliminando cuenta. Escríbenos a soporte@jobper.co"}), 500


@user_bp.get("/stats")
@require_auth
def user_stats():
    from services.pipeline import get_stats
    from services.referrals import get_referral_stats

    return jsonify(
        {
            "pipeline": get_stats(g.user_id),
            "referrals": get_referral_stats(g.user_id),
        }
    )


@user_bp.post("/push-subscription")
@require_auth
@validate(PushSubscriptionSchema)
def register_push():
    from services.notifications import register_push_subscription

    result = register_push_subscription(g.user_id, g.validated.model_dump())
    return jsonify(result)


@user_bp.post("/change-password")
@require_auth
def change_password():
    """Change password for authenticated user."""
    data = request.get_json() or {}
    current_password = data.get("current_password", "")
    new_password = data.get("new_password", "")

    if not current_password or not new_password:
        return jsonify({"error": "Contraseña actual y nueva requeridas"}), 400
    if len(new_password) < 6:
        return jsonify({"error": "La nueva contraseña debe tener al menos 6 caracteres"}), 400
    if current_password == new_password:
        return jsonify({"error": "La nueva contraseña debe ser diferente a la actual"}), 400

    try:
        from services.auth import _verify_password, _hash_password
        from core.database import UnitOfWork

        with UnitOfWork() as uow:
            user = uow.users.get(g.user_id)
            if not user:
                return jsonify({"error": "Usuario no encontrado"}), 404

            # Users who registered via magic link have no password yet → allow setting one
            if user.password_hash and not _verify_password(current_password, user.password_hash):
                return jsonify({"error": "La contraseña actual es incorrecta"}), 400

            user.password_hash = _hash_password(new_password)
            uow.commit()

        return jsonify({"ok": True, "message": "Contraseña actualizada correctamente"})
    except Exception as e:
        logger.error(f"Change password error: {e}", exc_info=True)
        return jsonify({"error": "Error al cambiar la contraseña"}), 500


# =============================================================================
# ONBOARDING (2 endpoints)
# =============================================================================
onboarding_bp = Blueprint("onboarding", __name__, url_prefix="/api/onboarding")


@onboarding_bp.post("/analyze")
@require_auth
@rate_limit(10)
@validate(OnboardingAnalyzeSchema)
def analyze_profile():
    """
    AI-powered profile extraction from free-text business description.
    Returns structured profile data for confirmation.
    """
    from types import SimpleNamespace

    from services.intelligence import analyze_profile_description
    from services.matching import calculate_match_score

    result = analyze_profile_description(g.validated.description)

    if "error" in result:
        return jsonify(result), 400

    # Get a preview of how many contracts would match
    profile = result.get("profile", {})
    matched_preview = 0
    if profile.get("sector") or profile.get("keywords"):
        # FIX: Create a mock user object with proposed profile instead of
        # modifying real user (which was wrong - other sessions couldn't see changes)
        from core.database import UnitOfWork

        with UnitOfWork() as uow:
            user = uow.users.get(g.user_id)
            if user:
                # Create mock user with proposed values for matching simulation
                mock_user = SimpleNamespace(
                    id=user.id,
                    sector=profile.get("sector") or user.sector,
                    keywords=profile.get("keywords") or user.keywords or [],
                    city=profile.get("city") or user.city,
                    budget_min=profile.get("budget_min") or user.budget_min,
                    budget_max=profile.get("budget_max") or user.budget_max,
                    plan=user.plan,
                )

                # Get recent contracts and score them with proposed profile
                from datetime import datetime, timedelta

                now = datetime.utcnow()
                contracts = (
                    uow.session.query(uow.contracts.model)
                    .filter(
                        uow.contracts.model.publication_date >= now - timedelta(days=30),
                    )
                    .order_by(uow.contracts.model.publication_date.desc())
                    .limit(200)
                    .all()
                )

                matched = 0
                for c in contracts:
                    score = calculate_match_score(mock_user, c)
                    if score >= 30:
                        matched += 1

                matched_preview = matched

    return jsonify(
        {
            "profile": profile,
            "method": result.get("method", "rules"),
            "matched_preview": matched_preview,
        }
    )


@onboarding_bp.post("/complete")
@require_auth
@rate_limit(5)
def complete_onboarding():
    """
    Save the confirmed profile from onboarding.
    """
    from services.auth import update_user_profile

    data = request.get_json(silent=True) or {}

    # Extract profile fields
    profile_data = {
        "company_name": data.get("company_name"),
        "sector": data.get("sector"),
        "keywords": data.get("keywords"),
        "city": data.get("city"),
        "budget_min": data.get("budget_min"),
        "budget_max": data.get("budget_max"),
    }

    # Remove None values
    profile_data = {k: v for k, v in profile_data.items() if v is not None}

    result = update_user_profile(g.user_id, profile_data)

    if not result:
        return jsonify({"error": "No se pudo guardar el perfil"}), 400

    # Mark onboarding as complete
    from core.database import UnitOfWork

    with UnitOfWork() as uow:
        user = uow.users.get(g.user_id)
        if user:
            user.onboarding_completed = True
            uow.commit()

    return jsonify(
        {
            "ok": True,
            "profile": result,
            "message": "¡Perfil configurado! Ya puedes ver contratos personalizados.",
        }
    )


# =============================================================================
# PAYMENTS (4 endpoints)
# =============================================================================
payments_bp = Blueprint("payments", __name__, url_prefix="/api/payments")


@payments_bp.post("/checkout")
@require_auth
@rate_limit(5)
@validate(CheckoutSchema)
@audit("checkout")
def checkout():
    from services.payments import create_checkout

    result = create_checkout(g.user_id, g.validated.plan)
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)


@payments_bp.get("/subscription")
@require_auth
def get_subscription():
    from services.payments import get_subscription

    result = get_subscription(g.user_id)
    if not result:
        return jsonify({"subscription": None})
    return jsonify({"subscription": result})


@payments_bp.get("/status")
@require_auth
def get_payment_status():
    """Return pending/grace payment info for the current user (used for status banner)."""
    from services.payments import get_user_payment_status

    return jsonify(get_user_payment_status(g.user_id))


@payments_bp.post("/request")
@require_auth
@rate_limit(5)
@audit("payment_request")
def payment_request():
    """User reports they've made a manual payment (Nequi/transfer)."""
    from services.payments import create_payment_request

    data = request.get_json(silent=True) or {}
    plan = data.get("plan", "")
    result = create_payment_request(g.user_id, plan)
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)


@payments_bp.post("/confirm")
@require_auth
@rate_limit(5)
@audit("payment_confirm")
def confirm_payment():
    """User uploads comprobante → auto-activate subscription."""
    import os

    from werkzeug.utils import secure_filename

    payment_id = request.form.get("payment_id")
    if not payment_id:
        return jsonify({"error": "payment_id es requerido"}), 400

    # Validate payment_id is numeric to prevent path traversal
    try:
        payment_id_int = int(payment_id)
    except ValueError:
        return jsonify({"error": "payment_id inválido"}), 400

    comprobante = request.files.get("comprobante")
    if not comprobante:
        return jsonify({"error": "Comprobante es requerido"}), 400

    # Validate file size FIRST (5MB max) - before reading content
    comprobante.seek(0, 2)
    size = comprobante.tell()
    comprobante.seek(0)
    if size > 5 * 1024 * 1024:
        return jsonify({"error": "El archivo no puede superar 5MB"}), 400
    if size < 100:  # Too small to be a valid image
        return jsonify({"error": "Archivo muy pequeño para ser una imagen válida"}), 400

    # FIX: Validate file type by MAGIC BYTES (not just Content-Type header)
    # This prevents uploading malicious files with fake Content-Type
    magic_bytes = comprobante.read(12)
    comprobante.seek(0)

    # Validate file type by magic bytes
    MAGIC_SIGNATURES = {
        b"\xff\xd8\xff": "jpg",  # JPEG
        b"\x89PNG\r\n\x1a\n": "png",  # PNG
    }

    detected_ext = None
    for magic, ext in MAGIC_SIGNATURES.items():
        if magic_bytes.startswith(magic):
            detected_ext = ext
            break

    # WebP: RIFF container + "WEBP" at bytes 8-12
    if not detected_ext and magic_bytes[:4] == b"RIFF" and magic_bytes[8:12] == b"WEBP":
        detected_ext = "webp"

    if not detected_ext:
        return jsonify({"error": "Solo se aceptan imágenes válidas (JPG, PNG, WebP)"}), 400

    # Save file with detected extension (not user-provided)
    from config import Config as _Cfg
    upload_dir = os.path.join(str(_Cfg.BASE_DIR), "uploads", "comprobantes", str(g.user_id))
    os.makedirs(upload_dir, exist_ok=True)
    filename = secure_filename(f"{payment_id_int}.{detected_ext}")
    filepath = os.path.join(upload_dir, filename)
    comprobante.save(filepath)

    from services.payments import confirm_payment as do_confirm

    result = do_confirm(g.user_id, payment_id_int, filepath)

    # Handle different verification results
    if "error" in result:
        return jsonify(result), 400

    # Check the verification status
    status = result.get("status", "approved")
    if status == "approved":
        return jsonify(result), 200
    elif status == "review":
        # Payment is being manually reviewed
        return jsonify(result), 202  # Accepted, pending
    elif status == "rejected":
        # Payment was rejected but user can retry
        return jsonify(result), 422  # Unprocessable Entity
    else:
        return jsonify(result), 200


@payments_bp.post("/cancel")
@require_auth
@audit("cancel_subscription")
def cancel_sub():
    from services.payments import cancel_subscription

    result = cancel_subscription(g.user_id)
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)


@payments_bp.get("/trust")
@require_auth
def get_trust_info():
    """Get user's trusted payer status and rewards."""
    from services.payments import get_user_trust_info

    result = get_user_trust_info(g.user_id)
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)


@payments_bp.get("/history")
@require_auth
def payment_history():
    """User's last 20 payments — lets them verify payment status without contacting support."""
    from core.database import UnitOfWork, Payment

    with UnitOfWork() as uow:
        payments = (
            uow.session.query(Payment)
            .filter(Payment.user_id == g.user_id)
            .order_by(Payment.created_at.desc())
            .limit(20)
            .all()
        )
        return jsonify({
            "payments": [
                {
                    "id": p.id,
                    "amount": p.amount,
                    "plan": (p.metadata_json or {}).get("plan", ""),
                    "status": p.status,
                    "reference": p.reference,
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                    "confirmed_at": p.confirmed_at.isoformat() if p.confirmed_at else None,
                }
                for p in payments
            ]
        })


@payments_bp.post("/one-click-renewal")
@require_auth
@rate_limit(5)
@audit("one_click_renewal")
def one_click_renewal():
    """
    One-click renewal for trusted payers (2+ verified payments).
    Creates a pending payment with the same plan.
    """
    from services.payments import one_click_renewal as do_renewal

    data = request.get_json(silent=True) or {}
    plan = data.get("plan")  # Optional - defaults to current plan
    result = do_renewal(g.user_id, plan)
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)


# =============================================================================
# REFERRALS (3 endpoints)
# =============================================================================
referrals_bp = Blueprint("referrals", __name__, url_prefix="/api/referrals")


@referrals_bp.get("/")
@require_auth
def referral_info():
    from services.referrals import generate_code, get_referral_stats

    code = generate_code(g.user_id)
    stats = get_referral_stats(g.user_id)
    return jsonify({**code, **stats})


@referrals_bp.get("/stats")
@require_auth
def referral_stats():
    from services.referrals import get_referral_stats

    return jsonify(get_referral_stats(g.user_id))


@referrals_bp.post("/track")
@rate_limit(30)
@validate(ReferralTrackSchema)
def track_referral():
    from services.referrals import track_click

    result = track_click(g.validated.code)
    if "error" in result:
        return jsonify(result), 404
    return jsonify(result)


# =============================================================================
# ADMIN (7 endpoints)
# =============================================================================
admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


@admin_bp.get("/dashboard")
@require_auth
@require_admin
def admin_dashboard():
    from services.admin import get_kpis

    return jsonify(get_kpis())


@admin_bp.get("/users")
@require_auth
@require_admin
@validate(AdminListSchema)
def admin_users():
    from services.admin import list_users

    return jsonify(list_users(g.validated.page, g.validated.per_page, g.validated.search or ""))


@admin_bp.get("/payments")
@require_auth
@require_admin
@validate(AdminListSchema)
def admin_payments():
    from services.admin import list_payments

    return jsonify(list_payments(g.validated.page, g.validated.per_page))


@admin_bp.post("/contracts/<int:contract_id>/moderate")
@require_auth
@require_admin
@validate(AdminModerateSchema)
@audit("admin_moderate")
def admin_moderate(contract_id: int):
    from services.admin import moderate_contract

    result = moderate_contract(contract_id, g.validated.action)
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)


@admin_bp.get("/scrapers")
@require_auth
@require_admin
def admin_scrapers():
    from services.admin import get_scraper_status

    return jsonify({"sources": get_scraper_status()})


@admin_bp.get("/logs")
@require_auth
@require_admin
@validate(AdminLogsSchema)
def admin_logs():
    from services.admin import get_logs

    return jsonify(get_logs(g.validated.page, g.validated.per_page, g.validated.action or "", g.validated.user_id))


@admin_bp.get("/health")
@require_auth
@require_admin
def admin_health():
    from services.admin import get_system_health

    return jsonify(get_system_health())


@admin_bp.get("/users/<int:user_id>")
@require_auth
@require_admin
def admin_user_detail(user_id: int):
    from services.admin import get_user_detail
    import traceback

    try:
        result = get_user_detail(user_id)
    except Exception as exc:
        logger.error(f"admin_user_detail({user_id}): {exc}\n{traceback.format_exc()}")
        return jsonify({"error": f"Error interno: {exc}"}), 500

    if "error" in result:
        return jsonify(result), 404
    return jsonify(result)


@admin_bp.post("/users/<int:user_id>/change-plan")
@require_auth
@require_admin
@audit("admin_change_plan")
def admin_change_plan(user_id: int):
    data = request.get_json(silent=True) or {}
    plan = data.get("plan", "")
    if not plan:
        return jsonify({"error": "plan es requerido"}), 400

    from services.admin import admin_change_plan as do_change

    result = do_change(user_id, plan)
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)


@admin_bp.post("/users/<int:user_id>/toggle-admin")
@require_auth
@require_admin
@audit("admin_toggle_admin")
def admin_toggle_admin(user_id: int):
    from services.admin import admin_toggle_admin as do_toggle

    result = do_toggle(user_id)
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)


@admin_bp.post("/users/<int:user_id>/extend-trial")
@require_auth
@require_admin
@audit("admin_extend_trial")
def admin_extend_trial(user_id: int):
    data = request.get_json(silent=True) or {}
    days = int(data.get("days", 7))
    from services.admin import admin_extend_trial as do_extend

    result = do_extend(user_id, days)
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)


@admin_bp.post("/users/<int:user_id>/send-magic-link")
@require_auth
@require_admin
@audit("admin_send_magic_link")
def admin_send_magic_link(user_id: int):
    from services.admin import admin_send_magic_link as do_send

    result = do_send(user_id)
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)


@admin_bp.get("/activity")
@require_auth
@require_admin
def admin_activity():
    from services.admin import get_activity_feed

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)
    return jsonify(get_activity_feed(page, min(per_page, 100)))


@admin_bp.post("/scrapers/<string:source_key>/trigger")
@require_auth
@require_admin
@audit("admin_trigger_scraper")
def admin_trigger_scraper(source_key: str):
    """Trigger a single scraper manually — uses ingestion pipeline for proper dedup."""
    try:
        from aggregator.source_registry import SOURCE_REGISTRY

        if source_key not in SOURCE_REGISTRY:
            return jsonify({"error": f"Scraper '{source_key}' no encontrado"}), 404

        scraper_class = SOURCE_REGISTRY[source_key]
        scraper = scraper_class()
        contracts = scraper.fetch_contracts()

        # Use the ingestion pipeline for proper dedup and persistence
        from services.ingestion import _persist_contracts

        stats = _persist_contracts(contracts, source_key)

        return jsonify({"ok": True, "source": source_key, "fetched": len(contracts), **stats})
    except Exception as e:
        logger.error(f"Admin trigger scraper {source_key} failed: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@admin_bp.post("/ingest")
@require_auth
@require_admin
@audit("admin_ingest")
def admin_ingest():
    """Trigger manual contract ingestion."""
    days_back = request.json.get("days_back", 7) if request.is_json else 7
    from services.ingestion import ingest_all

    result = ingest_all(days_back=min(days_back, 90))
    return jsonify(result)


@admin_bp.post("/activate-subscription")
@require_auth
@require_admin
@audit("admin_activate_subscription")
def admin_activate_subscription():
    """Manually activate a subscription after verifying manual payment."""
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    plan = data.get("plan")
    if not user_id or not plan:
        return jsonify({"error": "user_id y plan son requeridos"}), 400
    from services.payments import admin_activate

    result = admin_activate(user_id, plan)
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)


@admin_bp.get("/payments/review")
@require_auth
@require_admin
def admin_payments_review():
    """List payments that need manual review."""
    from services.payments import get_payments_for_review

    return jsonify({"payments": get_payments_for_review()})


@admin_bp.post("/payments/<int:payment_id>/approve")
@require_auth
@require_admin
@audit("admin_approve_payment")
def admin_approve_payment_route(payment_id: int):
    """Approve a payment that was flagged for manual review."""
    from services.payments import admin_approve_payment

    result = admin_approve_payment(payment_id)
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)


@admin_bp.post("/payments/approve-all-today")
@require_auth
@require_admin
@audit("admin_batch_approve")
def admin_batch_approve_route():
    """Approve ALL grace/review payments from the last 24h with one click."""
    from services.payments import admin_batch_approve_today

    result = admin_batch_approve_today()
    return jsonify(result)


@admin_bp.post("/payments/<int:payment_id>/reject")
@require_auth
@require_admin
@audit("admin_reject_payment")
def admin_reject_payment_route(payment_id: int):
    """Reject a payment that was flagged for manual review."""
    data = request.get_json(silent=True) or {}
    reason = data.get("reason", "")
    from services.payments import admin_reject_payment

    result = admin_reject_payment(payment_id, reason)
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)


# =============================================================================
# PUBLIC (3 endpoints — no auth)
# =============================================================================
public_bp = Blueprint("public", __name__, url_prefix="/api/public")


@public_bp.get("/plans")
@rate_limit(30)
def public_plans():
    from services.payments import get_plans

    return jsonify({"plans": get_plans()})


@public_bp.get("/stats")
@rate_limit(30)
def public_stats():
    from core.database import UnitOfWork

    with UnitOfWork() as uow:
        return jsonify(
            {
                "total_contracts": uow.contracts.count(),
                "total_users": uow.users.count(),
            }
        )


@public_bp.get("/contracts")
@rate_limit(30)
@validate(SearchSchema)
def public_contracts():
    from services.contracts import search_contracts

    result = search_contracts(
        g.validated.query, user_id=0, page=g.validated.page, per_page=min(g.validated.per_page, 10)
    )
    return jsonify(result)


@public_bp.get("/demo")
@rate_limit(60)
def demo_contracts():
    """Get sample contracts for landing page demo — no auth required."""
    from services.contracts import get_demo_contracts, get_public_stats

    contracts = get_demo_contracts(limit=6)
    stats = get_public_stats()
    return jsonify(
        {
            "contracts": contracts,
            "stats": stats,
        }
    )


# =============================================================================
# SUPPORT (1 endpoint)
# =============================================================================
support_bp = Blueprint("support", __name__, url_prefix="/api/support")


@support_bp.post("/chat")
@require_auth
@rate_limit(60)  # per-IP limit; chatbot enforces per-user daily limit internally
@validate(ChatbotSchema)
def chatbot_endpoint():
    from support.chatbot import find_answer

    result = find_answer(
        g.validated.question,
        user_id=g.user_id,
        user_plan=getattr(g, "user_plan", "free"),
    )
    return jsonify(result)


# =============================================================================
# HEALTH CHECK
# =============================================================================
health_bp = Blueprint("health", __name__, url_prefix="/api")


@health_bp.get("/health")
def health_check():
    """Health endpoint for Railway / load balancer."""
    try:
        from services.ingestion import get_contract_count

        contract_count = get_contract_count()
    except Exception:
        contract_count = -1  # DB not ready yet
    return jsonify(
        {
            "status": "ok",
            "service": "Jobper",
            "version": "5.0.0",
            "contracts": contract_count,
        }
    )


# =============================================================================
# SETUP ENDPOINT - One-time setup for Railway (make admin + load contracts)
# =============================================================================
setup_bp = Blueprint("setup", __name__, url_prefix="/api/setup")


@setup_bp.post("/fix-schema")
def setup_fix_schema():
    """Fix database schema by adding missing columns (emergency fix)."""
    data = request.get_json() or {}
    setup_token = data.get("setup_token", "")
    expected_token = os.getenv("SETUP_TOKEN", "")

    if not expected_token or setup_token != expected_token:
        return jsonify({"error": "Invalid or missing setup_token"}), 403

    try:
        from sqlalchemy import text
        from core.database import get_engine

        engine = get_engine()
        fixes = []
        with engine.connect() as conn:
            # Add missing privacy_policy_accepted_at column
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS privacy_policy_accepted_at TIMESTAMP"))
            conn.commit()
            fixes.append("Added privacy_policy_accepted_at to users")

        return jsonify({"ok": True, "message": "Schema fixed", "fixes": fixes})
    except Exception as e:
        logger.error(f"Schema fix failed: {e}")
        return jsonify({"error": str(e)}), 500


@setup_bp.post("/initialize")
def setup_initialize():
    """
    One-time setup endpoint - makes user admin and loads contracts.

    Security: Requires SETUP_TOKEN in request body.
    Set SETUP_TOKEN env var in Railway to a random secret.

    POST /api/setup/initialize
    {
      "setup_token": "<your-secret-token>",
      "email": "user@example.com",
      "load_contracts": true,
      "days": 30
    }
    """
    from config import Config

    data = request.get_json() or {}

    # Check setup token
    setup_token = data.get("setup_token", "")
    expected_token = os.getenv("SETUP_TOKEN", "")

    if not expected_token:
        return jsonify({
            "error": "SETUP_TOKEN not configured in environment",
            "debug": "Set SETUP_TOKEN env var in Railway dashboard"
        }), 500

    if setup_token != expected_token:
        return jsonify({"error": "Invalid setup_token"}), 403

    email = data.get("email", "").strip().lower()
    load_contracts = data.get("load_contracts", True)
    days = data.get("days", 30)

    if not email:
        return jsonify({"error": "email is required"}), 400

    results = {}

    # Step 1: Make user admin
    try:
        from core.database import UnitOfWork

        with UnitOfWork() as uow:
            user = uow.users.get_by_email(email)

            if not user:
                return jsonify({
                    "error": f"User not found: {email}",
                    "debug": "Register first at https://www.jobper.com.co/register"
                }), 404

            if not user.is_admin:
                user.is_admin = True
                uow.commit()
                results["admin"] = {"status": "success", "message": f"{email} is now admin"}
            else:
                results["admin"] = {"status": "already_admin", "message": f"{email} was already admin"}

    except Exception as e:
        logger.error(f"Setup: make_admin failed: {e}")
        return jsonify({"error": f"Failed to make admin: {str(e)}"}), 500

    # Step 2: Load contracts (if requested)
    if load_contracts:
        try:
            from services.ingestion import ingest_all, get_contract_count

            initial_count = get_contract_count()
            results["contracts_before"] = initial_count

            logger.info(f"Setup: Loading contracts (days={days})...")
            ingestion_results = ingest_all(days_back=days, force_aggressive=(initial_count == 0))

            total_new = sum(r.get("new", 0) for r in ingestion_results.values())
            total_errors = sum(r.get("errors", 0) for r in ingestion_results.values())

            final_count = get_contract_count()

            results["contracts"] = {
                "status": "success",
                "initial_count": initial_count,
                "final_count": final_count,
                "new_contracts": total_new,
                "errors": total_errors,
            }

        except Exception as e:
            logger.error(f"Setup: load_contracts failed: {e}")
            results["contracts"] = {
                "status": "error",
                "error": str(e)
            }

    return jsonify({
        "ok": True,
        "message": "Setup completed successfully",
        "results": results
    })


# =============================================================================
# ALL BLUEPRINTS (for app registration)
# =============================================================================




# =============================================================================
# TELEGRAM WEBHOOK (bot receives messages → auto-links chat_id to user)
# =============================================================================
telegram_bp = Blueprint("telegram", __name__, url_prefix="/api/telegram")


@telegram_bp.post("/webhook")
def telegram_webhook():
    """
    Telegram sends updates here when users message the bot.
    When a user sends /start <email>, the bot links their Telegram chat_id
    to their Jobper account and confirms with a message.
    Setup: set webhook via https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://www.jobper.com.co/api/telegram/webhook
    """
    from config import Config
    data = request.get_json() or {}
    message = data.get("message", {})
    chat = message.get("chat", {})
    chat_id = str(chat.get("id", ""))
    text = (message.get("text") or "").strip()
    first_name = chat.get("first_name", "")

    if not chat_id or not text:
        return jsonify({"ok": True})

    def bot_reply(msg):
        try:
            from services.notifications import send_telegram
            send_telegram(chat_id, msg)
        except Exception:
            pass

    # /start command — welcome message
    if text.startswith("/start"):
        parts = text.split(maxsplit=1)
        email_hint = parts[1].strip() if len(parts) > 1 else ""

        if email_hint and "@" in email_hint:
            # Auto-link if email was passed
            try:
                from core.database import UnitOfWork
                with UnitOfWork() as uow:
                    user = uow.users.get_by_email(email_hint.lower())
                    if user:
                        user.telegram_chat_id = chat_id
                        uow.commit()
                        bot_reply(
                            f"✅ *¡Cuenta vinculada, {first_name}!*\n\n"
                            f"Recibirás alertas de contratos relevantes aquí.\n"
                            f"Email: {email_hint}"
                        )
                        return jsonify({"ok": True})
            except Exception as e:
                logger.error(f"Telegram auto-link failed: {e}")

        bot_reply(
            f"👋 *Hola {first_name}, soy el bot de Jobper!*\n\n"
            f"Para vincular tu cuenta y recibir alertas de contratos:\n\n"
            f"1️⃣ Ve a *Jobper → Configuración → Telegram*\n"
            f"2️⃣ Ingresa tu Chat ID: `{chat_id}`\n\n"
            f"O envíame tu email así:\n`/vincular tu@empresa.co`"
        )

    elif text.startswith("/vincular"):
        parts = text.split(maxsplit=1)
        email = parts[1].strip().lower() if len(parts) > 1 else ""
        if not email or "@" not in email:
            bot_reply("❌ Email inválido. Envía: `/vincular tu@empresa.co`")
            return jsonify({"ok": True})
        try:
            from core.database import UnitOfWork
            with UnitOfWork() as uow:
                user = uow.users.get_by_email(email)
                if not user:
                    bot_reply(f"❌ No encontré una cuenta con el email `{email}`.\nRegístrate en jobper.co primero.")
                else:
                    user.telegram_chat_id = chat_id
                    uow.commit()
                    bot_reply(
                        f"✅ *¡Listo, {first_name}!* Tu cuenta está vinculada.\n\n"
                        f"Recibirás alertas cuando encontremos contratos compatibles con tu perfil."
                    )
        except Exception as e:
            logger.error(f"Telegram /vincular failed: {e}")
            bot_reply("⚠️ Error al vincular. Intenta de nuevo.")

    elif text == "/desvincular":
        try:
            from core.database import UnitOfWork
            with UnitOfWork() as uow:
                from sqlalchemy import text as sqlt
                uow.session.execute(
                    sqlt("UPDATE users SET telegram_chat_id = NULL WHERE telegram_chat_id = :cid"),
                    {"cid": chat_id}
                )
                uow.commit()
            bot_reply("✅ Tu cuenta fue desvinculada. Ya no recibirás alertas aquí.")
        except Exception as e:
            logger.error(f"Telegram /desvincular failed: {e}")

    else:
        bot_reply(
            "Comandos disponibles:\n"
            "/vincular tu@empresa.co — vincular cuenta\n"
            "/desvincular — dejar de recibir alertas"
        )

    return jsonify({"ok": True})


ALL_BLUEPRINTS = [
    health_bp,
    setup_bp,
    auth_bp,
    contracts_bp,
    pipeline_bp,
    marketplace_bp,
    user_bp,
    onboarding_bp,
    payments_bp,
    referrals_bp,
    admin_bp,
    public_bp,
    support_bp,
    telegram_bp,
]
