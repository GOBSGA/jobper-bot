"""
Jobper v4.0 — Flask Application Factory
========================================
SaaS CRM para contratos en Colombia.
"""
from __future__ import annotations

import logging
import os

from flask import Flask, send_from_directory
from flask_cors import CORS

from config import Config

# ---------------------------------------------------------------------------
# Logging - use stdout only in production (Railway), file + stdout in dev
# ---------------------------------------------------------------------------

_log_handlers = [logging.StreamHandler()]

# Only add file handler in local dev (Railway sets various env vars)
_is_production = any([
    os.environ.get("RAILWAY_ENVIRONMENT"),
    os.environ.get("RAILWAY_SERVICE_NAME"),
    os.environ.get("PORT") and os.environ.get("PORT") != "5001",  # Railway sets dynamic PORT
])
if not _is_production:
    try:
        _log_handlers.append(logging.FileHandler("jobper.log", encoding="utf-8"))
    except (PermissionError, OSError):
        pass  # Skip file logging if not writable

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=_log_handlers,
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def create_app() -> Flask:
    logger.info("create_app: Starting...")
    app = Flask(__name__)
    app.config["SECRET_KEY"] = Config.JWT_SECRET
    logger.info("create_app: Flask app created")

    # CORS
    CORS(app, origins=Config.CORS_ORIGINS, supports_credentials=True)
    logger.info("create_app: CORS configured")

    # Database — create tables on first run
    _init_db()
    logger.info("create_app: DB initialized")

    # Register all API blueprints
    logger.info("create_app: Importing blueprints...")
    from api.routes import ALL_BLUEPRINTS
    logger.info(f"create_app: Registering {len(ALL_BLUEPRINTS)} blueprints...")
    for bp in ALL_BLUEPRINTS:
        app.register_blueprint(bp)
    logger.info("create_app: Blueprints registered")

    # Error handlers (JSON responses for 400-500)
    logger.info("create_app: Registering error handlers...")
    from core.middleware import register_error_handlers
    register_error_handlers(app)
    logger.info("create_app: Error handlers registered")

    # Serve uploaded files (comprobantes) with path traversal protection
    uploads_dir = os.path.join(Config.BASE_DIR, "uploads")
    os.makedirs(uploads_dir, exist_ok=True)

    @app.route("/uploads/<path:filename>")
    def serve_upload(filename):
        # Security: prevent path traversal attacks (e.g., ../../../etc/passwd)
        if ".." in filename or filename.startswith("/"):
            return {"error": "Invalid filename"}, 400
        # Resolve and verify path is within uploads directory
        safe_path = os.path.normpath(os.path.join(uploads_dir, filename))
        if not safe_path.startswith(os.path.normpath(uploads_dir)):
            return {"error": "Invalid filename"}, 400
        return send_from_directory(uploads_dir, filename)

    # Serve built frontend in production (when dashboard/dist exists)
    frontend_dir = os.path.join(Config.BASE_DIR, "dashboard", "dist")
    logger.info(f"Frontend dir: {frontend_dir}")
    logger.info(f"Frontend dir exists: {os.path.isdir(frontend_dir)}")
    if os.path.isdir(frontend_dir):
        logger.info(f"Frontend files: {os.listdir(frontend_dir)}")
        @app.route("/", defaults={"path": ""})
        @app.route("/<path:path>")
        def serve_frontend(path):
            file_path = os.path.join(frontend_dir, path)
            if path and os.path.isfile(file_path):
                return send_from_directory(frontend_dir, path)
            return send_from_directory(frontend_dir, "index.html")
    else:
        # Dev mode: health endpoint only
        logger.warning(f"Frontend NOT found at {frontend_dir} - serving API only")
        # List what IS in the dashboard folder for debugging
        dashboard_dir = os.path.join(Config.BASE_DIR, "dashboard")
        if os.path.isdir(dashboard_dir):
            logger.info(f"Dashboard dir contents: {os.listdir(dashboard_dir)}")

        @app.route("/")
        def root():
            return {
                "status": "ok",
                "service": "Jobper",
                "version": "5.0.0",
            }

    # Start background ingestion + scheduler
    _start_background_services()

    logger.info("Jobper v5.0 ready")
    return app


# ---------------------------------------------------------------------------
# DB bootstrap
# ---------------------------------------------------------------------------

def _init_db():
    try:
        from core.database import get_engine, Base
        engine = get_engine()
        Base.metadata.create_all(engine)
        logger.info("Database tables verified")

        # Create GIN index for PostgreSQL FTS (no-op if already exists)
        if Config.is_postgresql():
            try:
                from sqlalchemy import text
                with engine.connect() as conn:
                    conn.execute(
                        text(
                            "CREATE INDEX IF NOT EXISTS idx_contracts_fts "
                            "ON contracts USING GIN ("
                            "to_tsvector('spanish', COALESCE(title, '') || ' ' || COALESCE(description, ''))"
                            ")"
                        )
                    )
                    conn.commit()
                    logger.info("PostgreSQL FTS index verified")
            except Exception as e:
                logger.warning(f"FTS index creation skipped: {e}")
    except Exception as e:
        logger.error(f"Database init failed: {e}")


# ---------------------------------------------------------------------------
# Background services: DISABLED for deployment stability
# ---------------------------------------------------------------------------

def _start_background_services():
    """Background scheduler disabled. Can be re-enabled after app is stable."""
    logger.info("Background scheduler DISABLED for deployment stability")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", 5001))
    logger.info(f"Starting on port {port}")
    app.run(host="0.0.0.0", port=port, debug=Config.FLASK_DEBUG)
