"""
Jobper v4.0 — Flask Application Factory
========================================
SaaS CRM para contratos en Colombia.
"""

from __future__ import annotations

import logging
import os

from flask import Flask, make_response, send_from_directory
from flask_cors import CORS

from config import Config

# ---------------------------------------------------------------------------
# Logging - use stdout only in production (Railway), file + stdout in dev
# ---------------------------------------------------------------------------

_log_handlers = [logging.StreamHandler()]

# Only add file handler in local dev (Railway sets various env vars)
_is_production = any(
    [
        os.environ.get("RAILWAY_ENVIRONMENT"),
        os.environ.get("RAILWAY_SERVICE_NAME"),
        os.environ.get("PORT") and os.environ.get("PORT") != "5001",  # Railway sets dynamic PORT
    ]
)
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
# Monitoring
# ---------------------------------------------------------------------------


def _init_sentry():
    """Initialize Sentry for error tracking (if configured)."""
    if not Config.SENTRY_DSN:
        logger.info("Sentry not configured (SENTRY_DSN not set)")
        return

    try:
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

        sentry_sdk.init(
            dsn=Config.SENTRY_DSN,
            environment=Config.SENTRY_ENVIRONMENT,
            traces_sample_rate=Config.SENTRY_TRACES_SAMPLE_RATE,
            integrations=[
                FlaskIntegration(),
                SqlalchemyIntegration(),
            ],
            # Capture specific errors
            before_send=_sentry_before_send,
        )
        logger.info(f"Sentry initialized for environment: {Config.SENTRY_ENVIRONMENT}")

    except ImportError:
        logger.warning("Sentry SDK not installed. Install with: pip install sentry-sdk")
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")


def _sentry_before_send(event, hint):
    """Filter events before sending to Sentry."""
    # Don't send certain errors that are expected/handled
    if "exc_info" in hint:
        exc_type, exc_value, tb = hint["exc_info"]

        # Ignore rate limit errors (expected behavior)
        if isinstance(exc_value, Exception) and "429" in str(exc_value):
            return None

        # Ignore validation errors (user input errors)
        if "ValidationError" in str(exc_type):
            return None

    return event


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def create_app() -> Flask:
    logger.info("create_app: Starting...")

    # Initialize Sentry for error tracking (if configured)
    _init_sentry()

    # Validate configuration
    is_valid, errors = Config.validate()
    if not is_valid:
        for error in errors:
            logger.error(f"Configuration error: {error}")
        raise RuntimeError("Configuration validation failed. Check logs for details.")

    app = Flask(__name__)
    app.url_map.strict_slashes = False  # Accept /foo and /foo/ interchangeably
    app.config["SECRET_KEY"] = Config.JWT_SECRET
    logger.info("create_app: Flask app created")

    # CORS
    CORS(app, origins=Config.CORS_ORIGINS, supports_credentials=True)
    logger.info(f"create_app: CORS configured with origins: {Config.CORS_ORIGINS}")

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
            # No-cache on index.html so browsers always fetch the latest JS bundle list
            resp = make_response(send_from_directory(frontend_dir, "index.html"))
            resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            resp.headers["Pragma"] = "no-cache"
            resp.headers["Expires"] = "0"
            return resp

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

    # Health check endpoint
    @app.route("/health")
    def health_check():
        """
        Health check endpoint that verifies all critical services.
        Returns 200 if healthy, 503 if any service is down.
        """
        import time
        from datetime import datetime

        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "5.0.0",
            "checks": {},
        }
        all_healthy = True

        # Check Database
        try:
            start = time.time()
            from sqlalchemy import text

            from core.database import get_engine

            engine = get_engine()
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                conn.commit()
            health_status["checks"]["database"] = {
                "status": "healthy",
                "response_time_ms": round((time.time() - start) * 1000, 2),
                "type": "postgresql" if Config.is_postgresql() else "sqlite",
            }
        except Exception as e:
            all_healthy = False
            health_status["checks"]["database"] = {"status": "unhealthy", "error": str(e)}

        # Check Redis (if configured)
        if Config.REDIS_URL:
            try:
                start = time.time()
                from core.cache import cache

                test_key = "health_check_test"
                cache.set(test_key, "ok", ttl=10)
                result = cache.get(test_key)
                cache.delete(test_key)
                if result == "ok":
                    health_status["checks"]["redis"] = {
                        "status": "healthy",
                        "response_time_ms": round((time.time() - start) * 1000, 2),
                    }
                else:
                    raise Exception("Redis test failed: value mismatch")
            except Exception as e:
                all_healthy = False
                health_status["checks"]["redis"] = {"status": "unhealthy", "error": str(e)}
        else:
            health_status["checks"]["redis"] = {"status": "not_configured", "message": "Redis is optional"}

        # Check Elasticsearch (if configured)
        if Config.ELASTICSEARCH_URL:
            try:
                start = time.time()
                import requests

                resp = requests.get(f"{Config.ELASTICSEARCH_URL}/_cluster/health", timeout=5)
                if resp.status_code == 200:
                    health_status["checks"]["elasticsearch"] = {
                        "status": "healthy",
                        "response_time_ms": round((time.time() - start) * 1000, 2),
                    }
                else:
                    raise Exception(f"HTTP {resp.status_code}")
            except Exception as e:
                # Elasticsearch is optional, don't mark as unhealthy
                health_status["checks"]["elasticsearch"] = {
                    "status": "degraded",
                    "error": str(e),
                    "message": "Elasticsearch is optional",
                }
        else:
            health_status["checks"]["elasticsearch"] = {
                "status": "not_configured",
                "message": "Elasticsearch is optional",
            }

        # Overall status
        if not all_healthy:
            health_status["status"] = "unhealthy"
            return health_status, 503

        return health_status, 200

    # Start background ingestion + scheduler
    _start_background_services()

    logger.info("Jobper v5.0 ready")
    return app


# ---------------------------------------------------------------------------
# DB bootstrap
# ---------------------------------------------------------------------------


def _run_alembic_migrations():
    """Run Alembic migrations automatically on startup."""
    try:
        from alembic import command
        from alembic.config import Config as AlembicConfig

        alembic_cfg = AlembicConfig("alembic.ini")
        # Set the database URL from our Config
        alembic_cfg.set_main_option("sqlalchemy.url", Config.DATABASE_URL)

        # Run migrations to head
        logger.info("Running Alembic migrations...")
        command.upgrade(alembic_cfg, "head")
        logger.info("Alembic migrations completed successfully")
    except Exception as e:
        # Don't fail startup if migrations fail - log and continue
        # This allows the app to run even if no migrations exist yet
        logger.warning(f"Alembic migrations skipped: {e}")


def _ensure_missing_columns():
    """
    Add missing columns using PostgreSQL's native ADD COLUMN IF NOT EXISTS.
    This is the final safety net - runs after Alembic migrations, catches anything
    that slipped through. 100% idempotent.
    """
    if not Config.is_postgresql():
        return
    try:
        from core.database import get_engine
        from sqlalchemy import text

        engine = get_engine()
        ddl_statements = [
            # From migration 002_add_trusted_payer_fields
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS trust_score FLOAT DEFAULT 0.0",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS verified_payments_count INTEGER DEFAULT 0",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS trust_level VARCHAR(20) DEFAULT 'new'",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS one_click_renewal_enabled BOOLEAN DEFAULT false",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_verified_payment_at TIMESTAMP",
            # From migration b299e2118e64
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255)",
            # From migration 0eced91c474b
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS privacy_policy_accepted_at TIMESTAMP",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS privacy_policy_version VARCHAR(20)",
            # From migration 001_add_verification_columns
            "ALTER TABLE payments ADD COLUMN IF NOT EXISTS comprobante_hash VARCHAR(64)",
            "ALTER TABLE payments ADD COLUMN IF NOT EXISTS verification_result TEXT",
            "ALTER TABLE payments ADD COLUMN IF NOT EXISTS verification_status VARCHAR(20)",
            # Telegram / contact
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS telegram_chat_id VARCHAR(50)",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS phone VARCHAR(20)",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS whatsapp_number VARCHAR(20)",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS whatsapp_enabled BOOLEAN DEFAULT false",
            # Onboarding & profile
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS onboarding_completed BOOLEAN DEFAULT false",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT false",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS notifications_enabled BOOLEAN DEFAULT true",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS city VARCHAR(100)",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS budget_min FLOAT",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS budget_max FLOAT",
            # Alerts
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS alerts_sent_this_week INTEGER DEFAULT 0",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS alerts_week_start TIMESTAMP",
            # Referrals
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS referral_code VARCHAR(20)",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS referred_by INTEGER",
            # Embeddings & renewal
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_embedding BYTEA",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS embedding_updated_at TIMESTAMP",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_renewal_prompt TIMESTAMP",
            # Subscriptions — columns added after initial schema
            "ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS reference VARCHAR(100)",
            "ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS auto_renew BOOLEAN DEFAULT true",
            "ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS renewal_reminded_at TIMESTAMP",
            # Cross-source contract deduplication
            "ALTER TABLE contracts ADD COLUMN IF NOT EXISTS content_hash VARCHAR(64)",
            # Indexes for FK columns (missing from original schema — prevent full table scans)
            "CREATE INDEX IF NOT EXISTS idx_fav_user ON favorites(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_fav_contract ON favorites(contract_id)",
            "CREATE INDEX IF NOT EXISTS idx_pc_publisher ON private_contracts(publisher_id)",
            "CREATE INDEX IF NOT EXISTS idx_app_contract ON contract_applications(contract_id)",
            "CREATE INDEX IF NOT EXISTS idx_app_applicant ON contract_applications(applicant_id)",
            "CREATE INDEX IF NOT EXISTS idx_push_user ON push_subscriptions(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_ref_referrer ON referrals(referrer_id)",
            "CREATE INDEX IF NOT EXISTS idx_ref_referred ON referrals(referred_id)",
            "CREATE INDEX IF NOT EXISTS idx_pipe_user_stage ON pipeline_entries(user_id, stage)",
            "CREATE INDEX IF NOT EXISTS idx_mkt_msg_contract ON marketplace_messages(contract_id)",
            "CREATE INDEX IF NOT EXISTS idx_mkt_msg_receiver ON marketplace_messages(receiver_id)",
        ]
        # Safety net: create pipeline_entries table if Base.metadata.create_all missed it
        create_pipeline_table = """
        CREATE TABLE IF NOT EXISTS pipeline_entries (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            contract_id INTEGER REFERENCES contracts(id) ON DELETE SET NULL,
            private_contract_id INTEGER REFERENCES private_contracts(id) ON DELETE SET NULL,
            stage VARCHAR(20) DEFAULT 'lead',
            notes JSON DEFAULT '[]',
            follow_up_date TIMESTAMP,
            value FLOAT,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
        """
        create_mkt_messages_table = """
        CREATE TABLE IF NOT EXISTS marketplace_messages (
            id SERIAL PRIMARY KEY,
            sender_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            receiver_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            contract_id INTEGER NOT NULL REFERENCES private_contracts(id) ON DELETE CASCADE,
            content TEXT NOT NULL,
            read_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW()
        )
        """
        ddl_statements = [create_pipeline_table, create_mkt_messages_table] + ddl_statements
        # Use a SEPARATE connection per statement — if one fails (PostgreSQL aborts
        # the whole transaction), it won't prevent the others from running.
        for stmt in ddl_statements:
            try:
                with engine.connect() as conn:
                    conn.execute(text(stmt))
                    conn.commit()
            except Exception as e:
                logger.warning(f"Column ensure skipped ({stmt[:50]}...): {e}")
        logger.info("Missing columns verified/added")
    except Exception as e:
        logger.error(f"_ensure_missing_columns failed: {e}")


def _init_db():
    try:
        from core.database import Base, get_engine

        engine = get_engine()
        Base.metadata.create_all(engine)
        logger.info("Database tables verified")

        if Config.is_postgresql():
            # Ensure all columns exist (safe even if Alembic migrations failed)
            _ensure_missing_columns()

            # Create GIN index for PostgreSQL FTS (no-op if already exists)
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

            # Run Alembic migrations automatically (records versions even if columns already exist)
            _run_alembic_migrations()
    except Exception as e:
        logger.error(f"Database init failed: {e}")


# ---------------------------------------------------------------------------
# Background services
# ---------------------------------------------------------------------------


def _start_background_services():
    """Start background scheduler for periodic tasks."""
    import threading
    import time
    from datetime import datetime

    _last_digest_day = [None]  # mutable cell to track when daily digest last ran
    _consecutive_scraper_failures = [0]  # mutable cell: count of consecutive all-error runs

    def scheduler_loop():
        """Run periodic tasks in background."""
        # Wait 5 minutes after startup before first run
        time.sleep(300)

        iteration = 0
        while True:
            try:
                # Run ingestion every 6 hours (moderate: 7 days back)
                logger.info("Scheduler: Starting periodic ingestion...")
                from services.ingestion import ingest_all

                result = ingest_all(days_back=7)
                total_new = result.get("total_new", 0)
                total_errors = result.get("total_errors", 0)
                sources = result.get("sources", {})
                logger.info(f"Scheduler: Ingestion complete - {total_new} new contracts, {total_errors} errors")

                # Heartbeat: detect silent failures (errors > 0 AND zero new contracts)
                if total_errors > 0 and total_new == 0:
                    _consecutive_scraper_failures[0] += 1
                    failed_sources = [k for k, v in sources.items() if v.get("errors", 0) > 0]
                    logger.warning(
                        f"Scraper heartbeat: run #{_consecutive_scraper_failures[0]} with "
                        f"{total_errors} errors, 0 new contracts. Failed: {failed_sources}"
                    )
                    # Alert admin after 2 consecutive bad runs
                    if _consecutive_scraper_failures[0] >= 2:
                        try:
                            from services.notifications import send_email
                            send_email(
                                Config.ADMIN_EMAIL,
                                "scraper_alert",
                                {
                                    "failed_sources": failed_sources,
                                    "total_errors": total_errors,
                                    "run_time": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
                                    "consecutive_failures": _consecutive_scraper_failures[0],
                                },
                            )
                            logger.warning(f"Scraper alert email sent to {Config.ADMIN_EMAIL}")
                        except Exception as e:
                            logger.error(f"Failed to send scraper alert: {e}")
                else:
                    # Reset counter on any successful run
                    if _consecutive_scraper_failures[0] > 0:
                        logger.info(f"Scraper heartbeat: recovered after {_consecutive_scraper_failures[0]} failed runs")
                    _consecutive_scraper_failures[0] = 0

                # Check subscription renewals every 6 hours
                logger.info("Scheduler: Checking subscription renewals...")
                from services.payments import check_renewals

                check_renewals()
                logger.info("Scheduler: Renewal check complete")

                # Clean up expired contracts (older than 30 days past deadline)
                logger.info("Scheduler: Cleaning up expired contracts...")
                from services.contracts import cleanup_expired_contracts

                cleanup_result = cleanup_expired_contracts(days_grace=30)
                logger.info(f"Scheduler: Cleanup complete - {cleanup_result['deleted']} contracts removed")

                # Send daily digest once per day (on first run after midnight Bogotá time)
                today = datetime.utcnow().date()
                current_hour = datetime.utcnow().hour  # 8am Bogotá = 13:00 UTC
                if _last_digest_day[0] != today and current_hour >= 13:
                    try:
                        logger.info("Scheduler: Sending daily digest emails...")
                        from services.notifications import send_daily_digest

                        digest_result = send_daily_digest()
                        logger.info(f"Scheduler: Daily digest complete - {digest_result}")
                        _last_digest_day[0] = today
                    except Exception as e:
                        logger.error(f"Daily digest failed: {e}")

            except Exception as e:
                logger.error(f"Scheduler error: {e}")

            iteration += 1
            # Sleep 6 hours (grace period check runs hourly via separate loop)
            time.sleep(6 * 60 * 60)

    def grace_checker_loop():
        """Check and expire grace subscriptions every hour."""
        time.sleep(60)  # short initial delay
        while True:
            try:
                from services.payments import check_grace_periods
                result = check_grace_periods()
                if result.get("revoked"):
                    logger.info(f"Grace checker: revoked {result['revoked']} expired subscriptions")
            except Exception as e:
                logger.error(f"Grace checker error: {e}")
            time.sleep(60 * 60)  # every hour

    # Start scheduler in daemon thread
    thread = threading.Thread(target=scheduler_loop, daemon=True, name="scheduler")
    thread.start()
    logger.info("Background scheduler started (first run in 5 minutes, then every 6 hours)")

    # Start grace period checker (every hour)
    grace_thread = threading.Thread(target=grace_checker_loop, daemon=True, name="grace-checker")
    grace_thread.start()
    logger.info("Grace period checker started (runs every hour)")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", 5001))
    logger.info(f"Starting on port {port}")
    app.run(host="0.0.0.0", port=port, debug=Config.FLASK_DEBUG)
