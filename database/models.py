"""
Modelos de base de datos para Jobper Bot v3.0 (Premium)
Soporta PostgreSQL (producción) y SQLite (desarrollo)
"""

from __future__ import annotations

import json
from datetime import datetime
from enum import Enum
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
    Text,
    create_engine,
)
from sqlalchemy.dialects.postgresql import JSON as PostgresJSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.types import TEXT, TypeDecorator

from config import Config

Base = declarative_base()


# =============================================================================
# TIPOS PERSONALIZADOS
# =============================================================================


class JSONType(TypeDecorator):
    """
    Tipo JSON compatible con PostgreSQL y SQLite.
    PostgreSQL usa JSON nativo, SQLite usa TEXT con serialización.
    """

    impl = TEXT
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return json.dumps(value)
        return None

    def process_result_value(self, value, dialect):
        if value is not None:
            return json.loads(value)
        return None


# =============================================================================
# ENUMS
# =============================================================================


class ConversationState(str, Enum):
    """Estados del flujo conversacional."""

    NEW = "new"
    AWAITING_INDUSTRY = "awaiting_industry"
    AWAITING_INCLUDE = "awaiting_include"
    AWAITING_EXCLUDE = "awaiting_exclude"
    AWAITING_BUDGET = "awaiting_budget"
    AWAITING_COUNTRY = "awaiting_country"
    ACTIVE = "active"
    PAUSED = "paused"
    # Estados para publicación de contratos privados
    POSTING_CONTRACT = "posting_contract"
    POSTING_AWAITING_BUDGET = "posting_awaiting_budget"
    POSTING_AWAITING_DEADLINE = "posting_awaiting_deadline"
    POSTING_AWAITING_LOCATION = "posting_awaiting_location"
    POSTING_AWAITING_CONFIRM = "posting_awaiting_confirm"


class PrivateContractStatus(str, Enum):
    """Estados de contratos privados publicados por usuarios."""

    DRAFT = "draft"
    ACTIVE = "active"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Country(str, Enum):
    """Países/regiones soportados."""

    COLOMBIA = "colombia"
    USA = "usa"
    MULTILATERAL = "multilateral"
    ALL = "all"


class SourceType(str, Enum):
    """Tipos de fuentes de datos."""

    GOVERNMENT = "government"
    PRIVATE = "private"
    MULTILATERAL = "multilateral"


# =============================================================================
# MODELOS
# =============================================================================


class User(Base):
    """Modelo de usuario del bot."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    phone = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=True)

    # Estado de la conversación
    state = Column(String(50), default=ConversationState.NEW.value)

    # Preferencias del usuario
    industry = Column(String(50), nullable=True)
    include_keywords = Column(JSONType, default=list)
    exclude_keywords = Column(JSONType, default=list)
    countries = Column(String(50), default=Country.ALL.value)

    # Filtros de presupuesto
    min_budget = Column(Float, nullable=True)
    max_budget = Column(Float, nullable=True)

    # Configuración de notificaciones
    notifications_enabled = Column(Boolean, default=True)
    notification_frequency = Column(String(20), default="weekly")

    # Embedding del perfil (para matching semántico)
    profile_embedding = Column(LargeBinary, nullable=True)
    embedding_updated_at = Column(DateTime, nullable=True)

    # Metadatos
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_interaction = Column(DateTime, default=datetime.utcnow)

    # Datos temporales durante el flujo de registro
    temp_data = Column(JSONType, default=dict)

    # Relaciones
    contracts = relationship("UserContract", back_populates="user")
    deadline_alerts = relationship("DeadlineAlert", back_populates="user")

    def __repr__(self):
        return f"<User(phone={self.phone}, state={self.state})>"

    def is_registered(self) -> bool:
        """Verifica si el usuario completó el registro."""
        return self.state == ConversationState.ACTIVE.value

    def get_all_keywords(self) -> List[str]:
        """Obtiene todas las palabras clave (industria + personalizadas)."""
        keywords = []

        if self.industry and self.industry in Config.INDUSTRIES:
            keywords.extend(Config.INDUSTRIES[self.industry]["keywords"])

        if self.include_keywords:
            keywords.extend(self.include_keywords)

        return list(set(keywords))


class Contract(Base):
    """Modelo de contrato/licitación."""

    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True)
    external_id = Column(String(100), unique=True, nullable=False, index=True)

    # Información del contrato
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    entity = Column(String(300), nullable=True)
    amount = Column(Float, nullable=True)
    currency = Column(String(10), default="COP")

    # Origen
    country = Column(String(50), nullable=False)
    source = Column(String(50), nullable=False)
    source_type = Column(String(20), default=SourceType.GOVERNMENT.value)
    url = Column(String(500), nullable=True)

    # Fechas
    publication_date = Column(DateTime, nullable=True)
    deadline = Column(DateTime, nullable=True)

    # Embedding del contrato (para matching semántico)
    embedding = Column(LargeBinary, nullable=True)
    embedding_model = Column(String(50), nullable=True)
    embedding_updated_at = Column(DateTime, nullable=True)

    # Datos crudos
    raw_data = Column(JSONType, default=dict)

    # Metadatos
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    users = relationship("UserContract", back_populates="contract")
    addendums = relationship("ContractAddendum", back_populates="contract")
    deadline_alerts = relationship("DeadlineAlert", back_populates="contract")

    # Índices
    __table_args__ = (
        Index("idx_contract_deadline", "deadline"),
        Index("idx_contract_source", "source"),
        Index("idx_contract_country", "country"),
    )

    def __repr__(self):
        return f"<Contract(id={self.external_id}, title={self.title[:50]})>"


class UserContract(Base):
    """Relación entre usuarios y contratos (contratos enviados)."""

    __tablename__ = "user_contracts"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False)

    # Score de relevancia para este usuario
    relevance_score = Column(Float, default=0.0)
    semantic_score = Column(Float, default=0.0)  # Score de similitud semántica

    # Estado del envío
    sent_at = Column(DateTime, default=datetime.utcnow)
    opened = Column(Boolean, default=False)

    # Relaciones
    user = relationship("User", back_populates="contracts")
    contract = relationship("Contract", back_populates="users")

    def __repr__(self):
        return f"<UserContract(user={self.user_id}, contract={self.contract_id})>"


class IndustryEmbedding(Base):
    """Embeddings pre-computados para cada industria."""

    __tablename__ = "industry_embeddings"

    id = Column(Integer, primary_key=True)
    industry_key = Column(String(50), unique=True, nullable=False)
    embedding = Column(LargeBinary, nullable=False)
    keywords_hash = Column(String(64), nullable=True)  # Para detectar cambios
    model_name = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<IndustryEmbedding(industry={self.industry_key})>"


class DataSource(Base):
    """Registro de fuentes de datos."""

    __tablename__ = "data_sources"

    id = Column(Integer, primary_key=True)
    source_key = Column(String(50), unique=True, nullable=False)
    display_name = Column(String(100), nullable=False)
    country = Column(String(50), nullable=False)
    source_type = Column(String(20), default=SourceType.GOVERNMENT.value)
    is_enabled = Column(Boolean, default=True)
    last_successful_fetch = Column(DateTime, nullable=True)
    error_count = Column(Integer, default=0)
    config = Column(JSONType, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<DataSource(key={self.source_key}, name={self.display_name})>"


class DeadlineAlert(Base):
    """Alertas de deadline enviadas (evita duplicados)."""

    __tablename__ = "deadline_alerts"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False)
    urgency_level = Column(Integer, nullable=False)  # 1=hoy, 2=mañana, 3=3 días
    sent_at = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    user = relationship("User", back_populates="deadline_alerts")
    contract = relationship("Contract", back_populates="deadline_alerts")

    # Índice único para evitar alertas duplicadas
    __table_args__ = (Index("idx_deadline_alert_unique", "user_id", "contract_id", "urgency_level", unique=True),)

    def __repr__(self):
        return f"<DeadlineAlert(user={self.user_id}, contract={self.contract_id}, level={self.urgency_level})>"


class ContractAddendum(Base):
    """Adendas/modificaciones a contratos."""

    __tablename__ = "contract_addendums"

    id = Column(Integer, primary_key=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False)
    addendum_number = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)
    new_deadline = Column(DateTime, nullable=True)
    detected_at = Column(DateTime, default=datetime.utcnow)
    notified_users = Column(JSONType, default=list)  # IDs de usuarios notificados

    # Relaciones
    contract = relationship("Contract", back_populates="addendums")

    def __repr__(self):
        return f"<ContractAddendum(contract={self.contract_id}, number={self.addendum_number})>"


class PrivateContract(Base):
    """
    Contratos privados publicados por usuarios del marketplace.
    Permite a empresas publicar trabajos y encontrar contratistas.
    """

    __tablename__ = "private_contracts"

    id = Column(Integer, primary_key=True)

    # Usuario que publica el contrato
    publisher_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Información del contrato
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)  # pintura, construcción, TI, etc.

    # Presupuesto
    budget_min = Column(Float, nullable=True)
    budget_max = Column(Float, nullable=True)
    currency = Column(String(10), default="COP")

    # Ubicación
    city = Column(String(100), nullable=True)
    country = Column(String(50), default="colombia")
    is_remote = Column(Boolean, default=False)

    # Fechas
    deadline = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Estado
    status = Column(String(20), default=PrivateContractStatus.DRAFT.value)

    # Keywords extraídas para matching
    keywords = Column(JSONType, default=list)

    # Embedding para matching semántico
    embedding = Column(LargeBinary, nullable=True)

    # Contratista seleccionado (si aplica)
    selected_contractor_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relaciones
    publisher = relationship("User", foreign_keys=[publisher_id], backref="published_contracts")
    selected_contractor = relationship("User", foreign_keys=[selected_contractor_id])
    applications = relationship("ContractApplication", back_populates="contract")

    # Índices
    __table_args__ = (
        Index("idx_private_contract_status", "status"),
        Index("idx_private_contract_category", "category"),
        Index("idx_private_contract_country", "country"),
    )

    def __repr__(self):
        return f"<PrivateContract(id={self.id}, title={self.title[:50]})>"


class ContractApplication(Base):
    """
    Aplicaciones/propuestas de contratistas a contratos privados.
    """

    __tablename__ = "contract_applications"

    id = Column(Integer, primary_key=True)

    # Contrato al que se aplica
    contract_id = Column(Integer, ForeignKey("private_contracts.id"), nullable=False)

    # Usuario que aplica (contratista)
    applicant_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Propuesta
    proposed_amount = Column(Float, nullable=True)
    message = Column(Text, nullable=True)
    estimated_days = Column(Integer, nullable=True)

    # Estado
    status = Column(String(20), default="pending")  # pending, accepted, rejected

    # Score de matching
    match_score = Column(Float, default=0.0)

    # Fechas
    applied_at = Column(DateTime, default=datetime.utcnow)
    responded_at = Column(DateTime, nullable=True)

    # Relaciones
    contract = relationship("PrivateContract", back_populates="applications")
    applicant = relationship("User", backref="contract_applications")

    # Índice único para evitar aplicaciones duplicadas
    __table_args__ = (Index("idx_application_unique", "contract_id", "applicant_id", unique=True),)

    def __repr__(self):
        return f"<ContractApplication(contract={self.contract_id}, applicant={self.applicant_id})>"


# =============================================================================
# INICIALIZACIÓN DE LA BASE DE DATOS
# =============================================================================

_engine = None
_SessionFactory = None


def get_engine():
    """Obtiene o crea el engine de base de datos (singleton)."""
    global _engine
    if _engine is None:
        _engine = create_engine(
            Config.DATABASE_URL,
            echo=False,
            pool_pre_ping=True,  # Verifica conexiones antes de usar
            pool_recycle=300,  # Recicla conexiones cada 5 min
        )
    return _engine


def init_database() -> sessionmaker:
    """
    Inicializa la base de datos y retorna el Session factory.

    Returns:
        sessionmaker: Factory para crear sesiones de base de datos.
    """
    global _SessionFactory

    if _SessionFactory is None:
        engine = get_engine()
        Base.metadata.create_all(engine)
        _SessionFactory = sessionmaker(bind=engine)

    return _SessionFactory


def get_session():
    """Obtiene una nueva sesión de base de datos."""
    if _SessionFactory is None:
        init_database()
    return _SessionFactory()
