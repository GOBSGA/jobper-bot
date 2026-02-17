"""
Jobper API — All endpoints (41 total)
Blueprint per domain: auth, contracts, pipeline, marketplace, payments, referrals, admin, public, support
"""

from __future__ import annotations

import logging

from flask import Blueprint, g, jsonify, request

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
from core.middleware import PLAN_ORDER, audit, rate_limit, require_admin, require_auth, require_plan, validate

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
        return jsonify(result), 401
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
            return jsonify(result), 401
        logger.info("Login success")
        return jsonify(result)
    except Exception as e:
        logger.error(f"Login exception: {e}", exc_info=True)
        # Return more specific error for database issues
        error_str = str(e)
        error_type = type(e).__name__
        if "connection" in error_str.lower() or "operational" in error_str.lower():
            return jsonify({"error": "Servicio temporalmente no disponible. Intenta en 1 minuto."}), 503
        # Return error details for debugging
        return jsonify({
            "error": "Error al procesar login. Contacta soporte@jobper.co",
            "debug": f"{error_type}: {str(e)[:200]}"
        }), 500


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

    hours = request.args.get("hours", 24, type=int)
    result = get_alerts(g.user_id, hours=hours)
    return jsonify(result)


@contracts_bp.get("/matched")
@require_auth
def matched_contracts():
    from services.matching import get_matched_contracts

    limit = request.args.get("limit", 50, type=int)
    min_score = request.args.get("min_score", 0, type=int)
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
        return jsonify(result), 404
    return jsonify(result)


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
        return jsonify({"error": "Error cargando perfil", "debug": f"{type(e).__name__}: {str(e)[:200]}"}), 500


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

    # Magic bytes for image formats
    MAGIC_SIGNATURES = {
        b"\xff\xd8\xff": "jpg",  # JPEG
        b"\x89PNG\r\n\x1a\n": "png",  # PNG
        b"RIFF": "webp",  # WebP (starts with RIFF)
    }

    detected_ext = None
    for magic, ext in MAGIC_SIGNATURES.items():
        if magic_bytes.startswith(magic):
            detected_ext = ext
            break

    # WebP has RIFF header, need to check for WEBP at byte 8
    if magic_bytes[:4] == b"RIFF" and len(magic_bytes) >= 12 and magic_bytes[8:12] == b"WEBP":
        detected_ext = "webp"
    elif magic_bytes[:4] == b"RIFF" and (len(magic_bytes) < 12 or magic_bytes[8:12] != b"WEBP"):
        detected_ext = None  # RIFF but not WebP

    if not detected_ext:
        return jsonify({"error": "Solo se aceptan imágenes válidas (JPG, PNG, WebP)"}), 400

    # Save file with detected extension (not user-provided)
    upload_dir = os.path.join("uploads", "comprobantes", str(g.user_id))
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
@rate_limit(20)
@validate(ChatbotSchema)
def chatbot_endpoint():
    from support.chatbot import find_answer

    result = find_answer(g.validated.question)
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
# ALL BLUEPRINTS (for app registration)
# =============================================================================

debug_bp = Blueprint("debug", __name__, url_prefix="/api/debug")


@debug_bp.get("/db")
def debug_db():
    """
    Debug endpoint: shows DB column status and tries a test login query.
    Visit /api/debug/db to diagnose login failures.
    """
    from sqlalchemy import inspect, text
    from core.database import get_engine

    engine = get_engine()
    result = {"status": "ok", "columns": {}, "test_query": None, "error": None}

    try:
        inspector = inspect(engine)
        user_cols = [c["name"] for c in inspector.get_columns("users")]
        critical = ["id", "email", "password_hash", "plan", "privacy_policy_accepted_at",
                    "trust_score", "trust_level", "one_click_renewal_enabled"]
        result["columns"] = {c: (c in user_cols) for c in critical}
        result["all_user_columns"] = sorted(user_cols)
    except Exception as e:
        result["error"] = f"inspect failed: {e}"

    try:
        with engine.connect() as conn:
            row = conn.execute(text("SELECT id, email, plan FROM users LIMIT 1")).fetchone()
            result["test_query"] = "SELECT id,email,plan OK" if row else "no users in DB"
    except Exception as e:
        result["test_query"] = f"FAILED: {e}"

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT id, email, password_hash, privacy_policy_accepted_at FROM users LIMIT 1"))
            result["full_select"] = "OK"
    except Exception as e:
        result["full_select"] = f"FAILED: {e}"

    return jsonify(result)


ALL_BLUEPRINTS = [
    health_bp,
    debug_bp,
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
]
