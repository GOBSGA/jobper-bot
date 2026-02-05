"""
Configuración centralizada de Jobper v4.0 — CRM de Contratos para Colombia
"""
from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuración cargada desde variables de entorno."""

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
    JWT_SECRET: str = os.getenv("JWT_SECRET", "")
    JWT_ACCESS_EXPIRY_MINUTES: int = 10080  # 7 days
    JWT_REFRESH_EXPIRY_DAYS: int = 30
    MAGIC_LINK_EXPIRY_MINUTES: int = 15  # 15 minutes
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
    # WEB PUSH
    # ======================================================================
    VAPID_PRIVATE_KEY: str = os.getenv("VAPID_PRIVATE_KEY", "")
    VAPID_PUBLIC_KEY: str = os.getenv("VAPID_PUBLIC_KEY", "")
    VAPID_CLAIMS_EMAIL: str = os.getenv("VAPID_CLAIMS_EMAIL", "mailto:soporte@jobper.co")

    # ======================================================================
    # FLASK
    # ======================================================================
    FLASK_HOST: str = os.getenv("FLASK_HOST", "0.0.0.0")
    FLASK_PORT: int = int(os.getenv("PORT", "5000"))
    FLASK_DEBUG: bool = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    SECRET_KEY: str = os.getenv("SECRET_KEY", os.getenv("JWT_SECRET", "dev-secret-change-me"))

    # CORS
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

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
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "gabriel.sanmiguel322@gmail.com")

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
    # PLANES / PRICING (COP)
    # ======================================================================
    PLANS: dict = {
        "free": {
            "name": "Free",
            "price": 0,
            "features": [
                "search", "contracts_unlimited",
            ],
            "limits": {
                "alerts_per_week": 3,
                "favorites_max": 5,
            },
        },
        "alertas": {
            "name": "Alertas",
            "price": 29_900,
            "features": [
                "search", "contracts_unlimited", "alerts", "favorites",
                "match", "email_digest",
            ],
        },
        "business": {
            "name": "Business",
            "price": 149_900,
            "features": [
                "search", "contracts_unlimited", "alerts", "favorites",
                "match", "email_digest",
                "ai_analysis", "pipeline", "marketplace", "push",
                "match_scores", "documents", "reports",
            ],
        },
        "enterprise": {
            "name": "Enterprise",
            "price": 599_900,
            "features": [
                "search", "contracts_unlimited", "alerts", "favorites",
                "match", "email_digest",
                "ai_analysis", "pipeline", "marketplace", "push",
                "match_scores", "documents", "reports",
                "team", "competitive_intelligence", "api_access", "priority_support",
            ],
        },
    }

    # Plan hierarchy for comparison (higher index = higher plan)
    PLAN_HIERARCHY: list = ["free", "trial", "alertas", "starter", "business", "enterprise"]

    # Feature → minimum plan required
    FEATURE_GATES: dict = {
        "alerts": "alertas",
        "favorites": "alertas",
        "match": "alertas",
        "email_digest": "alertas",
        "ai_analysis": "business",
        "pipeline": "business",
        "marketplace": "business",
        "push": "business",
        "match_scores": "business",
        "documents": "business",
        "reports": "business",
        "team": "enterprise",
        "competitive_intelligence": "enterprise",
        "api_access": "enterprise",
        "priority_support": "enterprise",
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
        """Valida la configuración y retorna errores si los hay."""
        errors = []
        if not cls.JWT_SECRET:
            errors.append("JWT_SECRET no configurado")
        if not cls.RESEND_API_KEY:
            errors.append("RESEND_API_KEY no configurado (emails no funcionarán)")
        if not cls.ADMIN_EMAIL:
            errors.append("ADMIN_EMAIL no configurado (notificaciones de pago no funcionarán)")
        return len(errors) == 0, errors

    @classmethod
    def is_postgresql(cls) -> bool:
        return cls.DATABASE_URL.startswith("postgresql://")
