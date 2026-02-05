"""
Jobper Core — Middleware stack: auth, plan gate, rate limit, validation, audit
"""
from __future__ import annotations

import functools
import logging
from datetime import datetime

import jwt
from flask import request, g, jsonify

from config import Config
from core.cache import cache
from core.security import rate_limiter

logger = logging.getLogger(__name__)

PLAN_ORDER = {"free": 0, "trial": 1, "alertas": 2, "starter": 2, "business": 3, "enterprise": 4}


# =============================================================================
# @require_auth — JWT validation, attach user to g
# =============================================================================

def require_auth(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Token requerido"}), 401

        token = auth_header[7:]

        # Check blacklist
        if cache.get(f"jwt_blacklist:{token}"):
            return jsonify({"error": "Token invalidado"}), 401

        try:
            payload = jwt.decode(token, Config.JWT_SECRET, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expirado"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Token inválido"}), 401

        g.user_id = payload["sub"]
        g.user_email = payload.get("email", "")
        g.user_plan = payload.get("plan", "trial")
        g.is_admin = payload.get("admin", False)

        return fn(*args, **kwargs)

    return wrapper


# =============================================================================
# @require_plan — Plan access gate
# =============================================================================

def require_plan(min_plan: str):
    """Block access if user's plan is below min_plan."""

    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            user_plan = getattr(g, "user_plan", "trial")
            user_level = PLAN_ORDER.get(user_plan, 0)
            required_level = PLAN_ORDER.get(min_plan, 0)

            if user_level < required_level:
                return jsonify({
                    "error": "Plan insuficiente",
                    "required": min_plan,
                    "current": user_plan,
                }), 403

            return fn(*args, **kwargs)

        return wrapper

    return decorator


def require_admin(fn):
    """Only allow admin users."""

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        if not getattr(g, "is_admin", False):
            return jsonify({"error": "Acceso denegado"}), 403
        return fn(*args, **kwargs)

    return wrapper


# =============================================================================
# @rate_limit — Per-IP and per-user rate limiting
# =============================================================================

def rate_limit(max_per_minute: int):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            ip = request.remote_addr or "unknown"
            ip_key = f"ip:{ip}:{fn.__qualname__}"

            if rate_limiter.is_limited(ip_key, max_per_minute):
                return jsonify({"error": "Demasiadas solicitudes"}), 429

            # Also limit per user if authenticated
            user_id = getattr(g, "user_id", None)
            if user_id:
                user_key = f"user:{user_id}:{fn.__qualname__}"
                if rate_limiter.is_limited(user_key, max_per_minute):
                    return jsonify({"error": "Demasiadas solicitudes"}), 429

            return fn(*args, **kwargs)

        return wrapper

    return decorator


# =============================================================================
# @validate — Pydantic input validation
# =============================================================================

def validate(schema_class):
    """Validate request body/args with a Pydantic schema. Result in g.validated."""

    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            if request.method in ("POST", "PUT", "PATCH"):
                data = request.get_json(silent=True) or {}
            else:
                data = request.args.to_dict()

            try:
                validated = schema_class(**data)
                g.validated = validated
            except Exception as e:
                errors = []
                if hasattr(e, "errors"):
                    errors = [
                        {"field": ".".join(str(x) for x in err["loc"]), "msg": err["msg"]}
                        for err in e.errors()
                    ]
                else:
                    errors = [{"field": "body", "msg": str(e)}]
                return jsonify({"error": "Datos inválidos", "details": errors}), 400

            return fn(*args, **kwargs)

        return wrapper

    return decorator


# =============================================================================
# @audit — Automatic audit logging
# =============================================================================

def audit(action: str):
    """Log action to AuditLog after request completes."""

    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            result = fn(*args, **kwargs)

            # Log asynchronously (best-effort)
            try:
                from core.database import UnitOfWork, AuditLog
                with UnitOfWork() as uow:
                    log = AuditLog(
                        user_id=getattr(g, "user_id", None),
                        action=action,
                        resource=request.endpoint,
                        resource_id=kwargs.get("id") or request.args.get("id"),
                        details={
                            "method": request.method,
                            "path": request.path,
                            "status": result[1] if isinstance(result, tuple) else 200,
                        },
                        ip=request.remote_addr,
                        user_agent=request.headers.get("User-Agent", "")[:255],
                    )
                    uow.audit.create(log)
                    uow.commit()
            except Exception as e:
                logger.warning(f"Audit log failed: {e}")

            return result

        return wrapper

    return decorator


# =============================================================================
# ERROR HANDLERS (register on Flask app)
# =============================================================================

def register_error_handlers(app):
    """Register standard JSON error handlers."""

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"error": "Solicitud inválida"}), 400

    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify({"error": "No autorizado"}), 401

    @app.errorhandler(403)
    def forbidden(e):
        return jsonify({"error": "Acceso denegado"}), 403

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "No encontrado"}), 404

    @app.errorhandler(429)
    def rate_limited(e):
        return jsonify({"error": "Demasiadas solicitudes"}), 429

    @app.errorhandler(500)
    def internal_error(e):
        logger.error(f"Internal error: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500
