"""
Configuración centralizada de Jobper v4.0 — CRM de Contratos para Colombia
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuración cargada desde variables de entorno."""

    # ======================================================================
    # ENVIRONMENT
    # ======================================================================
    ENV: str = os.getenv("ENV", "development")  # development, staging, production
    IS_PRODUCTION: bool = ENV == "production"
    IS_DEVELOPMENT: bool = ENV == "development"

    # ======================================================================
    # RUTAS
    # ======================================================================
    BASE_DIR: Path = Path(__file__).parent
    DATABASE_PATH: Path = BASE_DIR / "jobper.db"

    # ======================================================================
    # BASE DE DATOS
    # ======================================================================
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{DATABASE_PATH}"
    )
    # Fix Railway/Heroku postgres:// → postgresql://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    # ======================================================================
    # JWT / AUTH
    # ======================================================================
    # SECURITY: JWT_SECRET must be set in production. Generate with:
    # python -c "import secrets; print(secrets.token_hex(32))"
    _jwt_secret = os.getenv("JWT_SECRET") or os.getenv("SECRET_KEY")

    # In production, JWT_SECRET is REQUIRED
    if not _jwt_secret:
        if IS_PRODUCTION:
            print("FATAL ERROR: JWT_SECRET environment variable must be set in production!", file=sys.stderr)
            print("Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\"", file=sys.stderr)
            sys.exit(1)
        else:
            # Development fallback
            _jwt_secret = "dev-fallback-INSECURE-change-in-prod"

    JWT_SECRET: str = _jwt_secret
    JWT_ACCESS_EXPIRY_MINUTES: int = 10080  # 7 days
    JWT_REFRESH_EXPIRY_DAYS: int = 30
    MAGIC_LINK_EXPIRY_MINUTES: int = 60  # 60 minutes (was 15 - too short with email delays)
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")

    # ======================================================================
    # REDIS
    # ======================================================================
    REDIS_URL: str = os.getenv("REDIS_URL", "")

    # ======================================================================
    # CELERY
    # ======================================================================
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", REDIS_URL)
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)

    # ======================================================================
    # ELASTICSEARCH
    # ======================================================================
    ELASTICSEARCH_URL: str = os.getenv("ELASTICSEARCH_URL", "")
    ELASTICSEARCH_INDEX: str = "jobper_contracts"

    # ======================================================================
    # RESEND (Email)
    # ======================================================================
    RESEND_API_KEY: str = os.getenv("RESEND_API_KEY", "")
    RESEND_FROM_EMAIL: str = os.getenv("RESEND_FROM_EMAIL", "Jobper <noreply@jobper.co>")

    # ======================================================================
    # PAGOS MANUALES (Nequi / Bancolombia)
    # ======================================================================
    NEQUI_NUMBER: str = os.getenv("NEQUI_NUMBER", "")
    BANCOLOMBIA_ACCOUNT: str = os.getenv("BANCOLOMBIA_ACCOUNT", "")
    BANCOLOMBIA_TYPE: str = os.getenv("BANCOLOMBIA_TYPE", "Ahorros")
    BANCOLOMBIA_HOLDER: str = os.getenv("BANCOLOMBIA_HOLDER", "")

    # ======================================================================
    # PAGOS AUTOMÁTICOS (Wompi)
    # ======================================================================
    # WOMPI_EVENTS_SECRET is used to verify webhook signatures
    # Get it from Wompi dashboard: https://comercios.wompi.co/webhooks
    WOMPI_EVENTS_SECRET: str = os.getenv("WOMPI_EVENTS_SECRET", "")
    WOMPI_PUBLIC_KEY: str = os.getenv("WOMPI_PUBLIC_KEY", "")
    WOMPI_PRIVATE_KEY: str = os.getenv("WOMPI_PRIVATE_KEY", "")

    # ======================================================================
    # WEB PUSH
    # ======================================================================
    VAPID_PRIVATE_KEY: str = os.getenv("VAPID_PRIVATE_KEY", "")
    VAPID_PUBLIC_KEY: str = os.getenv("VAPID_PUBLIC_KEY", "")
    VAPID_CLAIMS_EMAIL: str = os.getenv("VAPID_CLAIMS_EMAIL", "mailto:soporte@jobper.co")

    # ======================================================================
    # WHATSAPP CLOUD API (Meta)
    # ======================================================================
    WHATSAPP_API_TOKEN: str = os.getenv("WHATSAPP_API_TOKEN", "")
    WHATSAPP_PHONE_ID: str = os.getenv("WHATSAPP_PHONE_ID", "")

    # ======================================================================
    # FLASK
    # ======================================================================
    FLASK_HOST: str = os.getenv("FLASK_HOST", "0.0.0.0")
    FLASK_PORT: int = int(os.getenv("PORT", "5000"))
    FLASK_DEBUG: bool = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    SECRET_KEY: str = os.getenv("SECRET_KEY", os.getenv("JWT_SECRET", "dev-secret-change-me"))

    # CORS - In production, CORS_ORIGINS must be set explicitly
    # Set CORS_ORIGINS env var (comma-separated list) or defaults to FRONTEND_URL
    _cors_origins_env = os.getenv("CORS_ORIGINS")

    if _cors_origins_env:
        CORS_ORIGINS: list = [origin.strip() for origin in _cors_origins_env.split(",")]
    elif IS_PRODUCTION:
        # In production, default to FRONTEND_URL only (same-origin)
        CORS_ORIGINS: list = [FRONTEND_URL]
    else:
        # Development: allow localhost variants
        CORS_ORIGINS: list = [
            "http://localhost:3000",
            "http://localhost:5000",
            "http://localhost:5001",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5000",
            "http://127.0.0.1:5001",
        ]

    # ======================================================================
    # RATE LIMITING
    # ======================================================================
    RATE_LIMIT_GENERAL: int = 60       # req/min
    RATE_LIMIT_AUTH: int = 5           # req/min
    RATE_LIMIT_SEARCH: int = 30        # req/min

    # ======================================================================
    # ADMIN
    # ======================================================================
    ADMIN_TOKEN: str = os.getenv("ADMIN_TOKEN", "")
    # ADMIN_EMAIL is required for payment notifications - no default to avoid data leaks
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "")

    # ======================================================================
    # MONITORING & LOGGING
    # ======================================================================
    # Sentry for error tracking (optional but recommended in production)
    SENTRY_DSN: str = os.getenv("SENTRY_DSN", "")
    SENTRY_TRACES_SAMPLE_RATE: float = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1"))
    SENTRY_ENVIRONMENT: str = ENV  # Uses ENV value (development, staging, production)

    # ======================================================================
    # APIs DE LICITACIONES — GOBIERNO COLOMBIA
    # ======================================================================
    SECOP_API_URL: str = "https://www.datos.gov.co/resource/p6dx-8zbt.json"

    # ======================================================================
    # APIs DE LICITACIONES — MULTILATERALES
    # ======================================================================
    IDB_API_URL: str = "https://www.iadb.org/en/projects-search"
    WORLDBANK_API_URL: str = "https://projects.worldbank.org/en/projects-operations/procurement"
    UNGM_API_URL: str = "https://www.ungm.org/Public/Notice"

    # ======================================================================
    # APIs DE LICITACIONES — PRIVADOS COLOMBIA
    # ======================================================================
    ECOPETROL_URL: str = "https://csp.ecopetrol.com.co"
    EPM_URL: str = "https://www.epm.com.co/proveedores"

    # ======================================================================
    # NLP / EMBEDDINGS
    # ======================================================================
    EMBEDDING_MODEL: str = os.getenv(
        "EMBEDDING_MODEL",
        "paraphrase-multilingual-MiniLM-L12-v2"
    )
    EMBEDDING_DIMENSION: int = 384
    SEMANTIC_SIMILARITY_THRESHOLD: float = 0.3

    # ======================================================================
    # SCHEDULER
    # ======================================================================
    WEEKLY_REPORT_DAY: str = "monday"
    WEEKLY_REPORT_HOUR: str = "09:00"
    URGENT_ALERT_HOURS: list = ["08:00", "18:00"]
    URGENT_DEADLINE_DAYS: int = 3

    # ======================================================================
    # INDUSTRIAS PREDEFINIDAS
    # ======================================================================
    INDUSTRIES: dict = {
        "tecnologia": {
            "name": "Tecnología e Informática",
            "keywords": [
                "software", "desarrollo", "aplicación", "app", "sistema",
                "plataforma", "web", "móvil", "cloud", "nube", "datos",
                "inteligencia artificial", "machine learning", "ciberseguridad",
                "infraestructura", "redes", "telecomunicaciones", "iot",
                "base de datos", "api", "microservicios", "devops"
            ],
        },
        "construccion": {
            "name": "Construcción e Infraestructura",
            "keywords": [
                "construcción", "obra", "edificio", "carretera", "puente",
                "infraestructura", "arquitectura", "ingeniería civil",
                "urbanismo", "vivienda", "acueducto", "alcantarillado",
                "mantenimiento", "remodelación", "interventoría"
            ],
        },
        "salud": {
            "name": "Salud y Farmacéutica",
            "keywords": [
                "salud", "médico", "hospital", "farmacéutico", "medicamento",
                "equipo médico", "laboratorio", "clínico", "diagnóstico",
                "insumos médicos", "dispositivos médicos", "vacunas",
                "ambulancia", "eps", "ips"
            ],
        },
        "educacion": {
            "name": "Educación y Capacitación",
            "keywords": [
                "educación", "capacitación", "formación", "curso", "taller",
                "universidad", "escuela", "e-learning", "docente",
                "material educativo", "biblioteca", "investigación",
                "diplomado", "certificación"
            ],
        },
        "consultoria": {
            "name": "Consultoría y Servicios Profesionales",
            "keywords": [
                "consultoría", "asesoría", "auditoría", "gestión", "estrategia",
                "análisis", "estudio", "diagnóstico", "evaluación",
                "interventoría", "supervisión", "acompañamiento",
                "due diligence", "legal", "financiero"
            ],
        },
        "logistica": {
            "name": "Logística y Transporte",
            "keywords": [
                "transporte", "logística", "distribución", "almacenamiento",
                "cadena de suministro", "flota", "envío", "carga",
                "bodega", "inventario", "courier", "mensajería",
                "exportación", "importación"
            ],
        },
        "marketing": {
            "name": "Marketing y Comunicaciones",
            "keywords": [
                "marketing", "publicidad", "comunicación", "diseño", "branding",
                "redes sociales", "contenido", "evento", "btl", "atl",
                "producción audiovisual", "fotografía", "imprenta",
                "relaciones públicas", "prensa"
            ],
        },
        "energia": {
            "name": "Energía y Medio Ambiente",
            "keywords": [
                "energía", "renovable", "solar", "eólica", "ambiental",
                "sostenibilidad", "residuos", "reciclaje", "agua",
                "saneamiento", "gestión ambiental", "impacto ambiental",
                "carbono", "eficiencia energética"
            ],
        },
    }

    # ======================================================================
    # FUENTES DE DATOS — Colombia only
    # ======================================================================
    DATA_SOURCES: dict = {
        "secop": {
            "name": "SECOP II",
            "country": "colombia",
            "type": "government",
            "enabled": True,
        },
        "idb": {
            "name": "BID (IDB)",
            "country": "multilateral",
            "type": "multilateral",
            "enabled": True,
        },
        "worldbank": {
            "name": "Banco Mundial",
            "country": "multilateral",
            "type": "multilateral",
            "enabled": True,
        },
        "ungm": {
            "name": "ONU (UNGM)",
            "country": "multilateral",
            "type": "multilateral",
            "enabled": True,
        },
        "ecopetrol": {
            "name": "Ecopetrol",
            "country": "colombia",
            "type": "private",
            "enabled": True,
        },
        "epm": {
            "name": "EPM",
            "country": "colombia",
            "type": "private",
            "enabled": True,
        },
    }

    # ======================================================================
    # PLANES / PRICING (COP) — 4 Planes con FOMO brutal
    # ======================================================================
    PLANS: dict = {
        # ----------------------------------------------------------------
        # GRATIS — "Observador"
        # Ve contratos pero con información crucial bloqueada
        # ----------------------------------------------------------------
        "free": {
            "name": "Gratis",
            "display_name": "Observador",
            "price": 0,
            "tagline": "Descubre oportunidades",
            "features": ["search", "basic_filters"],
            "limits": {
                "alerts_per_week": 3,           # FIX: 3 alertas básicas/semana (solo título)
                "favorites_max": 10,            # Pocos favoritos
                "searches_per_day": 10,         # Limitado
                "show_full_description": False, # Solo primeras 100 chars
                "show_match_score": False,      # Ve "??%"
                "show_amount": False,           # Ve "$🔒🔒🔒"
                "show_deadline_days": True,     # Sí ve días restantes
                "export_per_month": 0,          # Sin exportar
                "history_days": 7,              # Solo 7 días de historial
            },
            "blocked_message": "Activa Cazador para ver todos los detalles",
        },
        # ----------------------------------------------------------------
        # CAZADOR — $29,900/mes
        # Información completa, alertas por email
        # ----------------------------------------------------------------
        "cazador": {
            "name": "Cazador",
            "display_name": "Cazador",
            "price": 29_900,
            "tagline": "Encuentra antes que otros",
            "features": [
                "search", "contracts_unlimited", "alerts_email", "favorites",
                "match", "email_digest", "full_description", "match_scores",
                "advanced_filters", "export", "show_amount",
            ],
            "limits": {
                "alerts_per_week": 50,          # 50 alertas/semana
                "favorites_max": 100,           # Muchos favoritos
                "searches_per_day": None,       # Ilimitadas
                "show_full_description": True,
                "show_match_score": True,
                "show_amount": True,
                "export_per_month": 50,         # 50 exports/mes
                "history_days": 30,             # 30 días
            },
            "blocked_message": "Activa Competidor para acceso a contratos privados",
        },
        # ----------------------------------------------------------------
        # COMPETIDOR — $149,900/mes
        # Contratos privados, IA, pipeline, alertas instantáneas
        # ----------------------------------------------------------------
        "competidor": {
            "name": "Competidor",
            "display_name": "Competidor",
            "price": 149_900,
            "tagline": "Gana más contratos",
            "features": [
                "search", "contracts_unlimited", "alerts_email", "alerts_push",
                "favorites_unlimited", "match", "email_digest", "full_description",
                "match_scores", "advanced_filters", "export_unlimited", "show_amount",
                "private_contracts", "ai_analysis", "pipeline", "documents",
                "instant_alerts", "webinars",
            ],
            "limits": {
                "alerts_per_week": None,        # Ilimitadas
                "favorites_max": None,          # Ilimitados
                "searches_per_day": None,
                "show_full_description": True,
                "show_match_score": True,
                "show_amount": True,
                "export_per_month": 500,        # 500/mes
                "history_days": 365,            # 1 año
            },
            "blocked_message": "Activa Dominador para inteligencia competitiva",
        },
        # ----------------------------------------------------------------
        # DOMINADOR — $599,900/mes
        # Todo + inteligencia competitiva + multi-usuario + auto-propuestas
        # ----------------------------------------------------------------
        "dominador": {
            "name": "Dominador",
            "display_name": "Dominador",
            "price": 599_900,
            "tagline": "Domina tu sector",
            "features": [
                "search", "contracts_unlimited", "alerts_email", "alerts_push",
                "favorites_unlimited", "match", "email_digest", "full_description",
                "match_scores", "advanced_filters", "export_unlimited", "show_amount",
                "private_contracts", "ai_analysis", "pipeline", "documents",
                "instant_alerts", "webinars",
                "competitive_intelligence", "team", "api_access", "auto_proposals",
                "consortium_network", "priority_support", "monthly_consultation",
                "custom_reports", "whitelabel",
            ],
            "limits": {
                "alerts_per_week": None,
                "favorites_max": None,
                "searches_per_day": None,
                "show_full_description": True,
                "show_match_score": True,
                "show_amount": True,
                "export_per_month": None,       # Ilimitado
                "history_days": None,           # Todo el historial
                "team_members": 5,              # 5 usuarios
            },
            "blocked_message": "Ya tienes el plan máximo",
        },
    }

    # Alias para compatibilidad con código existente
    PLAN_ALIASES: dict = {
        "alertas": "cazador",      # Alias antiguo
        "business": "competidor",  # Alias antiguo
        "enterprise": "dominador", # Alias antiguo
        "starter": "cazador",      # Alias antiguo
        "trial": "free",           # Trial = Free con limits
    }

    # Plan hierarchy for comparison (higher index = higher plan)
    PLAN_HIERARCHY: list = ["free", "trial", "cazador", "competidor", "dominador"]

    # Feature → minimum plan required (FOMO gates)
    FEATURE_GATES: dict = {
        # === CAZADOR ($30K) ===
        "full_description": "cazador",
        "match_scores": "cazador",
        "show_amount": "cazador",
        "alerts_email": "cazador",
        "favorites_unlimited": "cazador",
        "email_digest": "cazador",
        "advanced_filters": "cazador",
        "export": "cazador",

        # === COMPETIDOR ($150K) ===
        "private_contracts": "competidor",
        "ai_analysis": "competidor",
        "pipeline": "competidor",
        "alerts_push": "competidor",
        "instant_alerts": "competidor",
        "documents": "competidor",
        "webinars": "competidor",

        # === DOMINADOR ($600K) ===
        "competitive_intelligence": "dominador",
        "team": "dominador",
        "api_access": "dominador",
        "auto_proposals": "dominador",
        "consortium_network": "dominador",
        "priority_support": "dominador",
        "monthly_consultation": "dominador",
        "custom_reports": "dominador",
        "whitelabel": "dominador",
    }

    # FOMO messages for each blocked feature
    FOMO_MESSAGES: dict = {
        "full_description": "Ve la descripción completa con Cazador",
        "match_scores": "{count} contratos coinciden {percent}%+ con tu perfil",
        "show_amount": "Este contrato vale ${amount} — Desbloquea con Cazador",
        "private_contracts": "{count} contratos privados disponibles solo en Competidor",
        "ai_analysis": "Analiza este contrato con IA y conoce tu probabilidad de ganar",
        "competitive_intelligence": "Descubre quién gana contratos en tu sector",
        "alerts_email": "Recibe alertas cuando publiquen contratos para ti",
        "instant_alerts": "Sé el primero en enterarte — alertas en tiempo real",
    }

    # Marketplace featured pricing (COP)
    FEATURED_PRICING: dict = {
        1: 9_900,
        10: 60_000,
        20: 120_000,
    }

    # ======================================================================
    # REFERRALS
    # ======================================================================
    REFERRAL_MAX_PER_MONTH: int = 10
    REFERRAL_DISCOUNTS: dict = {
        1: 0.10,    # 10%
        10: 0.50,   # 50%
    }

    # ======================================================================
    # VALIDATION
    # ======================================================================
    @classmethod
    def validate(cls) -> tuple[bool, list[str]]:
        """Valida la configuración y retorna errores/warnings."""
        errors = []
        warnings = []

        # Critical errors (block startup in production)
        if not cls.JWT_SECRET and cls.IS_PRODUCTION:
            errors.append("CRITICAL: JWT_SECRET must be set in production")

        if not cls.DATABASE_URL:
            errors.append("CRITICAL: DATABASE_URL not configured")

        # Important warnings (should be set but not blocking)
        if not cls.RESEND_API_KEY:
            warnings.append("WARNING: RESEND_API_KEY not set - emails will not be sent")

        if not cls.ADMIN_EMAIL:
            warnings.append("WARNING: ADMIN_EMAIL not set - payment notifications will fail")

        if cls.CORS_ORIGINS == ["*"] and cls.IS_PRODUCTION:
            warnings.append("WARNING: CORS is set to '*' in production - security risk")

        if not cls.WOMPI_EVENTS_SECRET and cls.IS_PRODUCTION:
            warnings.append("WARNING: WOMPI_EVENTS_SECRET not set - payment webhooks cannot be verified")

        # Print all warnings
        for warning in warnings:
            print(f"⚠️  {warning}", file=sys.stderr)

        return len(errors) == 0, errors

    @classmethod
    def is_postgresql(cls) -> bool:
        return cls.DATABASE_URL.startswith("postgresql://")
