"""
Jobper Services — Authentication (Magic Link + JWT)
No passwords. No age restrictions.
"""

from __future__ import annotations

import logging
import secrets
from datetime import datetime, timedelta, timezone

import jwt

from config import Config
from core.cache import cache
from core.database import MagicLink, UnitOfWork, User
from core.security import generate_secure_token, hash_token

logger = logging.getLogger(__name__)


# =============================================================================
# MAGIC LINK
# =============================================================================


def send_magic_link(email: str, ip: str = None) -> dict:
    """
    Generate magic link token, save hash in DB, queue email.
    Returns: {ok: True} or {error: str}
    """
    email = email.lower().strip()

    token = generate_secure_token(32)
    token_hash = hash_token(token)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=Config.MAGIC_LINK_EXPIRY_MINUTES)

    with UnitOfWork() as uow:
        link = MagicLink(
            email=email,
            token_hash=token_hash,
            expires_at=expires_at,
            ip_address=ip,
        )
        uow.magic_links.create(link)
        uow.commit()

    # Send email async
    verify_url = f"{Config.FRONTEND_URL}/verify?token={token}"
    from core.tasks import task_send_email

    task_send_email.delay(email, "magic_link", {"url": verify_url, "email": email})

    logger.info(f"Magic link sent to {email}")
    return {"ok": True}


def verify_magic_link(token: str, referral_code: str = None) -> dict:
    """
    Verify token, create/get user, return JWT tokens.
    Returns: {access_token, refresh_token, user} or {error: str, reason: str}
    """
    token_hash = hash_token(token)

    with UnitOfWork() as uow:
        link = uow.magic_links.get_valid_by_hash(token_hash)
        if not link:
            # Get specific failure reason for debugging
            reason = uow.magic_links.get_failure_reason(token_hash)
            error_messages = {
                "not_found": "Token no encontrado. Verifica el enlace o solicita uno nuevo.",
                "already_used": "Este enlace ya fue utilizado. Solicita uno nuevo.",
                "expired": "El enlace expiró. Los enlaces son válidos por 60 minutos.",
            }
            error_msg = error_messages.get(reason, "Token inválido o expirado")
            logger.warning(f"Magic link verification failed: reason={reason}, hash={token_hash[:16]}...")
            return {"error": error_msg, "reason": reason}

        # Mark as used
        link.used_at = datetime.now(timezone.utc)

        # Get or create user
        user = uow.users.get_by_email(link.email)
        is_new = False

        if not user:
            is_new = True
            user_referral_code = f"JOB-{secrets.token_hex(4).upper()}"
            user = User(
                email=link.email,
                email_verified=True,
                plan="trial",
                trial_ends_at=datetime.now(timezone.utc) + timedelta(days=14),
                referral_code=user_referral_code,
                privacy_policy_accepted_at=datetime.now(timezone.utc),
                privacy_policy_version=Config.PRIVACY_POLICY_VERSION,
            )
            uow.users.create(user)
        else:
            user.email_verified = True

        uow.commit()

        # Generate JWT
        access = _create_access_token(user)
        refresh = _create_refresh_token(user)

        user_data = _user_to_public(user)

    # Send welcome email for new users
    if is_new:
        from core.tasks import task_send_email

        task_send_email.delay(user_data["email"], "welcome", {"name": user_data.get("company_name", "")})

        # Track referral signup if code was provided
        if referral_code:
            try:
                from services.referrals import track_signup

                track_signup(referral_code, user_data["id"])
            except Exception as e:
                logger.error(f"Referral tracking failed: {e}")

    return {
        "access_token": access,
        "refresh_token": refresh,
        "user": user_data,
        "is_new": is_new,
    }


# =============================================================================
# PASSWORD AUTH
# =============================================================================


def _hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    import bcrypt

    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash."""
    import bcrypt

    try:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    except Exception:
        return False


def register_with_password(email: str, password: str, referral_code: str = None) -> dict:
    """
    Register a new user with email + password.
    Returns: {access_token, refresh_token, user} or {error: str}
    """
    email = email.lower().strip()

    if len(password) < 6:
        return {"error": "La contraseña debe tener al menos 6 caracteres"}

    with UnitOfWork() as uow:
        # Check if user exists
        existing = uow.users.get_by_email(email)
        if existing:
            return {"error": "Ya existe una cuenta con este correo"}

        # Create user — auto-accept privacy policy at registration (user clicked "Crear cuenta")
        user_referral_code = f"JOB-{secrets.token_hex(4).upper()}"
        user = User(
            email=email,
            password_hash=_hash_password(password),
            email_verified=True,  # REVERTED: Auto-verify for password auth (UX priority)
            plan="trial",
            trial_ends_at=datetime.now(timezone.utc) + timedelta(days=14),
            referral_code=user_referral_code,
            privacy_policy_accepted_at=datetime.now(timezone.utc),
            privacy_policy_version=Config.PRIVACY_POLICY_VERSION,
        )
        uow.users.create(user)
        uow.commit()

        # Generate JWT tokens
        access = _create_access_token(user)
        refresh = _create_refresh_token(user)
        user_data = _user_to_public(user)

    # Track referral
    if referral_code:
        try:
            from services.referrals import track_signup

            track_signup(referral_code, user_data["id"])
        except Exception as e:
            logger.error(f"Referral tracking failed: {e}")

    logger.info(f"New user registered with password: {email}")
    return {
        "access_token": access,
        "refresh_token": refresh,
        "user": user_data,
        "is_new": True,
    }


def send_password_reset(email: str, ip: str = None) -> dict:
    """
    Send password reset email with a secure one-time link.
    Always returns {ok: True} — never reveals if the email exists.
    """
    email = email.lower().strip()

    with UnitOfWork() as uow:
        user = uow.users.get_by_email(email)
        if not user:
            logger.info(f"Password reset requested for unknown email: {email}")
            return {"ok": True}

    token = generate_secure_token(32)
    token_hash = hash_token(token)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)

    with UnitOfWork() as uow:
        link = MagicLink(
            email=email,
            token_hash=token_hash,
            expires_at=expires_at,
            ip_address=ip,
        )
        uow.magic_links.create(link)
        uow.commit()

    reset_url = f"{Config.FRONTEND_URL}/reset-password?token={token}"
    from core.tasks import task_send_email

    task_send_email.delay(email, "password_reset", {"url": reset_url, "email": email})
    logger.info(f"Password reset email sent to {email}")
    return {"ok": True}


def reset_password_with_token(token: str, new_password: str) -> dict:
    """
    Validate reset token and update password. Auto-logs user in on success.
    Returns: {access_token, refresh_token, user} or {error: str}
    """
    if len(new_password) < 6:
        return {"error": "La contraseña debe tener al menos 6 caracteres"}

    token_hash = hash_token(token)

    with UnitOfWork() as uow:
        link = uow.magic_links.get_valid_by_hash(token_hash)
        if not link:
            reason = uow.magic_links.get_failure_reason(token_hash)
            if reason == "already_used":
                return {"error": "Este enlace ya fue utilizado. Solicita uno nuevo desde ¿Olvidaste tu contraseña?"}
            return {"error": "El enlace expiró o es inválido. Solicita uno nuevo."}

        link.used_at = datetime.now(timezone.utc)

        user = uow.users.get_by_email(link.email)
        if not user:
            return {"error": "Usuario no encontrado"}

        user.password_hash = _hash_password(new_password)
        uow.commit()

        access = _create_access_token(user)
        refresh = _create_refresh_token(user)
        user_data = _user_to_public(user)

    logger.info(f"Password reset completed for {link.email}")
    return {"access_token": access, "refresh_token": refresh, "user": user_data}


def login_with_password(email: str, password: str) -> dict:
    """
    Login with email + password.
    Returns: {access_token, refresh_token, user} or {error: str}
    """
    email = email.lower().strip()

    with UnitOfWork() as uow:
        user = uow.users.get_by_email(email)

        if not user:
            return {"error": "Correo o contraseña incorrectos"}

        if not user.password_hash:
            return {"error": "Esta cuenta usa magic link. Revisa tu correo."}

        if not _verify_password(password, user.password_hash):
            return {"error": "Correo o contraseña incorrectos"}

        # Generate JWT
        access = _create_access_token(user)
        refresh = _create_refresh_token(user)
        user_data = _user_to_public(user)

    logger.info(f"User logged in with password: {email}")
    return {
        "access_token": access,
        "refresh_token": refresh,
        "user": user_data,
    }


# =============================================================================
# JWT
# =============================================================================


def _create_access_token(user: User) -> str:
    # Admins always get top-tier plan so they can test every feature freely
    effective_plan = "dominador" if user.is_admin else user.plan
    payload = {
        "sub": str(user.id),  # PyJWT 2.4+ requires sub to be a string (RFC 7519)
        "email": user.email,
        "plan": effective_plan,
        "admin": user.is_admin,
        "type": "access",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=Config.JWT_ACCESS_EXPIRY_MINUTES),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, Config.JWT_SECRET, algorithm="HS256")


def _create_refresh_token(user: User) -> str:
    payload = {
        "sub": str(user.id),  # PyJWT 2.4+ requires sub to be a string (RFC 7519)
        "type": "refresh",
        "exp": datetime.now(timezone.utc) + timedelta(days=Config.JWT_REFRESH_EXPIRY_DAYS),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, Config.JWT_SECRET, algorithm="HS256")


def refresh_access_token(refresh_token: str) -> dict:
    """
    Validate refresh token, return new access + refresh tokens.
    Old refresh token is blacklisted (rotation).
    """
    try:
        payload = jwt.decode(refresh_token, Config.JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return {"error": "Refresh token expirado"}
    except jwt.InvalidTokenError:
        return {"error": "Refresh token inválido"}

    if payload.get("type") != "refresh":
        return {"error": "Token inválido"}

    # Don't blacklist refresh tokens on rotation — without persistent
    # Redis the in-memory blacklist dies on server restart, which causes
    # instant "session expired" for every logged-in user. Only explicit
    # logout blacklists tokens.

    with UnitOfWork() as uow:
        user = uow.users.get(int(payload["sub"]))  # sub is string, DB needs int
        if not user:
            return {"error": "Usuario no encontrado"}

        access = _create_access_token(user)
        refresh = _create_refresh_token(user)

    return {"access_token": access, "refresh_token": refresh}


def logout(token: str):
    """Blacklist the current access token."""
    try:
        payload = jwt.decode(token, Config.JWT_SECRET, algorithms=["HS256"], options={"verify_exp": False})
        ttl = max(int(payload.get("exp", 0) - datetime.now(timezone.utc).timestamp()), 1)
        cache.set(f"jwt_blacklist:{token}", "1", ttl)
    except Exception:
        pass  # If token is already invalid, nothing to blacklist


# =============================================================================
# HELPERS
# =============================================================================


def _needs_privacy_acceptance(user: User) -> bool:
    """Check if user needs to accept (or re-accept) the privacy policy."""
    if not user.privacy_policy_accepted_at:
        return True
    version = getattr(user, "privacy_policy_version", None)
    if not version:
        return True
    return version != Config.PRIVACY_POLICY_VERSION


def _user_to_public(user: User) -> dict:
    # Admins always see top-tier plan so every feature gate opens in the UI
    effective_plan = "dominador" if user.is_admin else user.plan
    return {
        "id": user.id,
        "email": user.email,
        "company_name": user.company_name,
        "sector": user.sector,
        "keywords": user.keywords or [],
        "city": user.city,
        "budget_min": user.budget_min,
        "budget_max": user.budget_max,
        "plan": effective_plan,
        "trial_ends_at": user.trial_ends_at.isoformat() if user.trial_ends_at else None,
        "is_admin": user.is_admin,
        "referral_code": user.referral_code,
        "notifications_enabled": user.notifications_enabled,
        "whatsapp_number": user.whatsapp_number,
        "whatsapp_enabled": user.whatsapp_enabled,
        "telegram_chat_id": user.telegram_chat_id if hasattr(user, "telegram_chat_id") else None,
        "privacy_policy_accepted_at": user.privacy_policy_accepted_at.isoformat() if user.privacy_policy_accepted_at else None,
        "needs_privacy_acceptance": _needs_privacy_acceptance(user),
        "onboarding_completed": user.onboarding_completed,
        "email_verified": user.email_verified,
        "trust_level": user.trust_level,
        "trust_score": user.trust_score,
        "one_click_renewal_enabled": user.one_click_renewal_enabled,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


def get_user_profile(user_id: int) -> dict | None:
    """Get public user profile."""
    with UnitOfWork() as uow:
        user = uow.users.get(user_id)
        if not user:
            return None
        return _user_to_public(user)


def update_user_profile(user_id: int, data: dict) -> dict | None:
    """Update user profile fields."""
    with UnitOfWork() as uow:
        user = uow.users.get(user_id)
        if not user:
            return None

        if "company_name" in data:
            user.company_name = data["company_name"]
        if "sector" in data:
            user.sector = data["sector"]
        if "keywords" in data:
            user.keywords = data["keywords"]
        if "notifications_enabled" in data:
            user.notifications_enabled = data["notifications_enabled"]
        if "city" in data:
            user.city = data["city"]
        if "budget_min" in data:
            user.budget_min = data["budget_min"]
        if "budget_max" in data:
            user.budget_max = data["budget_max"]
        if "whatsapp_number" in data:
            user.whatsapp_number = data["whatsapp_number"]
        if "whatsapp_enabled" in data:
            user.whatsapp_enabled = data["whatsapp_enabled"]
        if "telegram_chat_id" in data:
            user.telegram_chat_id = data["telegram_chat_id"] or None
        if "daily_digest_enabled" in data:
            user.daily_digest_enabled = data["daily_digest_enabled"]

        uow.commit()
        return _user_to_public(user)


# =============================================================================
# GOOGLE OAUTH
# =============================================================================

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


def google_oauth_url(state: str = "") -> str:
    """
    Build the Google OAuth authorization URL.
    state is used to carry referral_code through the OAuth round-trip.
    """
    import urllib.parse

    params = {
        "client_id": Config.GOOGLE_CLIENT_ID,
        "redirect_uri": f"{Config.BACKEND_URL}/api/auth/google/callback",
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "online",
        "prompt": "select_account",
        "state": state or "",
    }
    return f"{GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"


def google_oauth_callback(code: str, state: str = "") -> dict:
    """
    Exchange OAuth code for Google user info, then find-or-create the Jobper user.
    Returns: {access_token, refresh_token, user, is_new} or {error: str}
    """
    import requests as req

    if not Config.GOOGLE_CLIENT_ID or not Config.GOOGLE_CLIENT_SECRET:
        return {"error": "Google OAuth no está configurado"}

    # 1. Exchange code for access token
    try:
        token_resp = req.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": Config.GOOGLE_CLIENT_ID,
                "client_secret": Config.GOOGLE_CLIENT_SECRET,
                "redirect_uri": f"{Config.BACKEND_URL}/api/auth/google/callback",
                "grant_type": "authorization_code",
            },
            timeout=10,
        )
        token_data = token_resp.json()
    except Exception as e:
        logger.error(f"Google token exchange failed: {e}")
        return {"error": "Error al conectar con Google"}

    if "error" in token_data:
        logger.error(f"Google token error: {token_data}")
        return {"error": "Código de autorización inválido o expirado"}

    google_access_token = token_data.get("access_token")
    if not google_access_token:
        return {"error": "No se obtuvo token de Google"}

    # 2. Get user info from Google
    try:
        userinfo_resp = req.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {google_access_token}"},
            timeout=10,
        )
        userinfo = userinfo_resp.json()
    except Exception as e:
        logger.error(f"Google userinfo failed: {e}")
        return {"error": "Error obteniendo datos de Google"}

    email = userinfo.get("email", "").lower().strip()
    name = userinfo.get("name") or userinfo.get("given_name") or ""
    if not email:
        return {"error": "No se pudo obtener el email de Google"}

    # 3. Find or create user
    is_new = False
    with UnitOfWork() as uow:
        user = uow.users.get_by_email(email)

        if not user:
            is_new = True
            user_referral_code = f"JOB-{secrets.token_hex(4).upper()}"
            user = User(
                email=email,
                company_name=name,
                email_verified=True,
                plan="trial",
                trial_ends_at=datetime.now(timezone.utc) + timedelta(days=14),
                referral_code=user_referral_code,
                privacy_policy_accepted_at=datetime.now(timezone.utc),
                privacy_policy_version=Config.PRIVACY_POLICY_VERSION,
            )
            uow.users.create(user)
            uow.commit()
            logger.info(f"New user via Google OAuth: {email}")
        else:
            # Ensure email_verified for existing users who sign in via Google
            if not user.email_verified:
                user.email_verified = True
                uow.commit()
            logger.info(f"Existing user signed in via Google: {email}")

        access = _create_access_token(user)
        refresh = _create_refresh_token(user)
        user_data = _user_to_public(user)

    # Track referral if state contains a referral code
    referral_code = state.strip() if state else None
    if is_new and referral_code:
        try:
            from services.referrals import track_signup
            track_signup(referral_code, user_data["id"])
        except Exception as e:
            logger.error(f"Referral tracking failed after Google OAuth: {e}")

    return {
        "access_token": access,
        "refresh_token": refresh,
        "user": user_data,
        "is_new": is_new,
    }


def accept_privacy_policy(user_id: int) -> dict:
    """
    Mark privacy policy as accepted by user (with version tracking).
    Returns: {ok: True} or {error: str}
    """
    with UnitOfWork() as uow:
        user = uow.users.get(user_id)
        if not user:
            return {"error": "Usuario no encontrado"}

        user.privacy_policy_accepted_at = datetime.now(timezone.utc)
        user.privacy_policy_version = Config.PRIVACY_POLICY_VERSION
        uow.commit()

        logger.info(f"User {user_id} accepted privacy policy v{Config.PRIVACY_POLICY_VERSION}")
        return {
            "ok": True,
            "accepted_at": user.privacy_policy_accepted_at.isoformat(),
            "version": Config.PRIVACY_POLICY_VERSION,
        }
