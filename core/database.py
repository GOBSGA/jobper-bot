"""
Jobper Core — Modelos, Unit of Work, Repositorios
14 tablas, ~450 líneas. Reemplaza database/models.py + database/manager.py (1,449 líneas).
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Generic, Optional, Type, TypeVar

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
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Session, relationship, sessionmaker
from sqlalchemy.types import TEXT, TypeDecorator

from config import Config

T = TypeVar("T")


# =============================================================================
# BASE + CUSTOM TYPES
# =============================================================================


class Base(DeclarativeBase):
    pass


class JSONType(TypeDecorator):
    """JSON compatible con PostgreSQL y SQLite."""

    impl = TEXT
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return json.dumps(value) if value is not None else None

    def process_result_value(self, value, dialect):
        return json.loads(value) if value is not None else None


# =============================================================================
# MODELOS (14 tablas)
# =============================================================================


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)  # For password auth (optional, magic link still works)
    company_name = Column(String(200), nullable=True)
    sector = Column(Text, nullable=True)  # texto libre
    keywords = Column(JSONType, default=list)

    # Plan & trial
    plan = Column(String(20), default="trial")  # trial, free, alertas, business, enterprise
    trial_ends_at = Column(DateTime, nullable=True)
    is_admin = Column(Boolean, default=False)
    email_verified = Column(Boolean, default=False)

    # Privacy & Legal
    privacy_policy_accepted_at = Column(DateTime, nullable=True)

    # Notifications
    notifications_enabled = Column(Boolean, default=True)

    # Referrals
    referral_code = Column(String(20), unique=True, nullable=True, index=True)
    referred_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Alert limits (for free tier)
    alerts_sent_this_week = Column(Integer, default=0)
    alerts_week_start = Column(DateTime, nullable=True)

    # Profile fields from onboarding
    city = Column(String(100), nullable=True)
    budget_min = Column(Float, nullable=True)
    budget_max = Column(Float, nullable=True)

    # Embedding (matching semántico)
    profile_embedding = Column(LargeBinary, nullable=True)
    embedding_updated_at = Column(DateTime, nullable=True)

    # Renewal tracking
    last_renewal_prompt = Column(DateTime, nullable=True)

    # Contact / WhatsApp
    phone = Column(String(20), nullable=True)
    whatsapp_number = Column(String(20), nullable=True)  # +57XXXXXXXXXX
    whatsapp_enabled = Column(Boolean, default=False)

    # Onboarding
    onboarding_completed = Column(Boolean, default=False)

    # Trusted Payer System
    trust_score = Column(Float, default=0.0)  # Accumulated trust from verified payments
    verified_payments_count = Column(Integer, default=0)  # Count of 95%+ confidence payments
    trust_level = Column(String(20), default="new")  # new, bronze, silver, gold, platinum
    one_click_renewal_enabled = Column(Boolean, default=False)  # Earned after 2+ verified payments
    last_verified_payment_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    favorites = relationship("Favorite", back_populates="user")
    subscriptions = relationship("Subscription", back_populates="user")
    pipeline_entries = relationship("PipelineEntry", back_populates="user")
    push_subscriptions = relationship("PushSubscription", back_populates="user")

    def is_trial_active(self) -> bool:
        if self.plan != "trial":
            return False
        return self.trial_ends_at and self.trial_ends_at > datetime.utcnow()

    def has_active_plan(self) -> bool:
        return self.plan in ("alertas", "business", "enterprise") or self.is_trial_active()


class Contract(Base):
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True)
    external_id = Column(String(100), unique=True, nullable=False, index=True)

    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    entity = Column(String(300), nullable=True)
    amount = Column(Float, nullable=True)
    currency = Column(String(10), default="COP")

    country = Column(String(50), nullable=False, default="colombia")
    source = Column(String(50), nullable=False)
    source_type = Column(String(20), default="government")
    url = Column(String(500), nullable=True)

    publication_date = Column(DateTime, nullable=True)
    deadline = Column(DateTime, nullable=True)

    embedding = Column(LargeBinary, nullable=True)
    embedding_model = Column(String(50), nullable=True)
    embedding_updated_at = Column(DateTime, nullable=True)

    raw_data = Column(JSONType, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    favorites = relationship("Favorite", back_populates="contract")

    __table_args__ = (
        Index("idx_contract_deadline", "deadline"),
        Index("idx_contract_source", "source"),
        Index("idx_contract_country", "country"),
    )

    @property
    def is_expired(self) -> bool:
        return self.deadline and self.deadline < datetime.utcnow()


class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="favorites")
    contract = relationship("Contract", back_populates="favorites")

    __table_args__ = (UniqueConstraint("user_id", "contract_id", name="uq_favorite"),)


class PrivateContract(Base):
    __tablename__ = "private_contracts"

    id = Column(Integer, primary_key=True)
    publisher_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)

    budget_min = Column(Float, nullable=True)
    budget_max = Column(Float, nullable=True)
    currency = Column(String(10), default="COP")

    city = Column(String(100), nullable=True)
    country = Column(String(50), default="colombia")
    is_remote = Column(Boolean, default=False)

    deadline = Column(DateTime, nullable=True)
    status = Column(String(20), default="active")  # draft, active, completed, cancelled

    # Featured
    is_featured = Column(Boolean, default=False)
    featured_until = Column(DateTime, nullable=True)

    # Contact
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(20), nullable=True)

    keywords = Column(JSONType, default=list)
    embedding = Column(LargeBinary, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    publisher = relationship("User", foreign_keys=[publisher_id])
    applications = relationship("ContractApplication", back_populates="contract")

    __table_args__ = (
        Index("idx_pc_status", "status"),
        Index("idx_pc_category", "category"),
    )


class ContractApplication(Base):
    __tablename__ = "contract_applications"

    id = Column(Integer, primary_key=True)
    contract_id = Column(Integer, ForeignKey("private_contracts.id"), nullable=False)
    applicant_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    proposed_amount = Column(Float, nullable=True)
    message = Column(Text, nullable=True)
    estimated_days = Column(Integer, nullable=True)
    status = Column(String(20), default="pending")
    match_score = Column(Float, default=0.0)

    applied_at = Column(DateTime, default=datetime.utcnow)
    responded_at = Column(DateTime, nullable=True)

    contract = relationship("PrivateContract", back_populates="applications")
    applicant = relationship("User")

    __table_args__ = (UniqueConstraint("contract_id", "applicant_id", name="uq_application"),)


class DataSource(Base):
    __tablename__ = "data_sources"

    id = Column(Integer, primary_key=True)
    source_key = Column(String(50), unique=True, nullable=False)
    display_name = Column(String(100), nullable=False)
    country = Column(String(50), nullable=False)
    source_type = Column(String(20), default="government")
    is_enabled = Column(Boolean, default=True)
    last_successful_fetch = Column(DateTime, nullable=True)
    error_count = Column(Integer, default=0)
    config = Column(JSONType, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)


class IndustryEmbedding(Base):
    __tablename__ = "industry_embeddings"

    id = Column(Integer, primary_key=True)
    industry_key = Column(String(50), unique=True, nullable=False)
    embedding = Column(LargeBinary, nullable=False)
    keywords_hash = Column(String(64), nullable=True)
    model_name = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# --- NEW MODELS ---


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    plan = Column(String(20), nullable=False)  # starter, business, enterprise
    status = Column(String(20), default="active")  # active, cancelled, expired
    wompi_ref = Column(String(100), nullable=True)
    amount = Column(Integer, nullable=False)  # COP, sin decimales
    starts_at = Column(DateTime, default=datetime.utcnow)
    ends_at = Column(DateTime, nullable=False)
    auto_renew = Column(Boolean, default=True)
    renewal_reminded_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="subscriptions")

    __table_args__ = (Index("idx_sub_user_status", "user_id", "status"),)


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Integer, nullable=False)
    currency = Column(String(10), default="COP")
    type = Column(String(20), nullable=False)  # subscription, feature, pack
    wompi_ref = Column(String(100), unique=True, nullable=True)
    status = Column(String(20), default="pending")  # pending, approved, declined, review
    comprobante_url = Column(String(500), nullable=True)
    confirmed_at = Column(DateTime, nullable=True)
    metadata_json = Column(JSONType, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Receipt verification fields
    comprobante_hash = Column(String(64), nullable=True, index=True)  # SHA256 for duplicate detection
    verification_result = Column(JSONType, nullable=True)  # AI verification details
    verification_status = Column(String(20), nullable=True)  # auto_approved, manual_review, rejected

    user = relationship("User")

    __table_args__ = (
        Index("idx_payment_user", "user_id"),
        Index("idx_payment_hash", "comprobante_hash"),
    )


class MagicLink(Base):
    __tablename__ = "magic_links"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), nullable=False, index=True)
    token_hash = Column(String(128), unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class PipelineEntry(Base):
    __tablename__ = "pipeline_entries"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=True)
    private_contract_id = Column(Integer, ForeignKey("private_contracts.id"), nullable=True)

    stage = Column(String(20), default="lead")  # lead, proposal, submitted, won, lost
    notes = Column(JSONType, default=list)  # [{text, created_at}]
    follow_up_date = Column(DateTime, nullable=True)
    value = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="pipeline_entries")

    __table_args__ = (Index("idx_pipe_user_stage", "user_id", "stage"),)


class Referral(Base):
    __tablename__ = "referrals"

    id = Column(Integer, primary_key=True)
    referrer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    referred_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    code = Column(String(20), nullable=False, index=True)
    status = Column(String(20), default="clicked")  # clicked, registered, subscribed
    clicked_at = Column(DateTime, default=datetime.utcnow)
    registered_at = Column(DateTime, nullable=True)
    subscribed_at = Column(DateTime, nullable=True)

    referrer = relationship("User", foreign_keys=[referrer_id])
    referred = relationship("User", foreign_keys=[referred_id])


class PushSubscription(Base):
    __tablename__ = "push_subscriptions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    endpoint = Column(Text, nullable=False)
    p256dh = Column(String(255), nullable=False)
    auth = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="push_subscriptions")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=True)
    action = Column(String(50), nullable=False)
    resource = Column(String(50), nullable=True)
    resource_id = Column(String(50), nullable=True)
    details = Column(JSONType, default=dict)
    ip = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_audit_user", "user_id"),
        Index("idx_audit_action", "action"),
        Index("idx_audit_created", "created_at"),
    )


# =============================================================================
# ENGINE + SESSION FACTORY
# =============================================================================

_engine = None
_SessionFactory = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(
            Config.DATABASE_URL,
            echo=False,
            pool_pre_ping=True,
            pool_recycle=300,
        )
    return _engine


def get_session_factory() -> sessionmaker:
    global _SessionFactory
    if _SessionFactory is None:
        _SessionFactory = sessionmaker(bind=get_engine())
    return _SessionFactory


def init_database():
    """Create all tables (dev only — use Alembic in production)."""
    engine = get_engine()
    Base.metadata.create_all(engine)
    return get_session_factory()


# =============================================================================
# UNIT OF WORK
# =============================================================================


class UnitOfWork:
    """
    Context manager: 1 session per request, 1 commit at the end.
    If exception → rollback. Always closes session.

    Usage:
        with UnitOfWork() as uow:
            user = uow.users.get_by_email("x@y.com")
            uow.payments.create(Payment(...))
            uow.commit()
    """

    def __enter__(self):
        self.session: Session = get_session_factory()()
        self.users = UserRepo(self.session)
        self.contracts = ContractRepo(self.session)
        self.favorites = BaseRepository(Favorite, self.session)
        self.private_contracts = BaseRepository(PrivateContract, self.session)
        self.applications = BaseRepository(ContractApplication, self.session)
        self.data_sources = BaseRepository(DataSource, self.session)
        self.industry_embeddings = BaseRepository(IndustryEmbedding, self.session)
        self.subscriptions = SubscriptionRepo(self.session)
        self.payments = PaymentRepo(self.session)
        self.magic_links = MagicLinkRepo(self.session)
        self.pipeline = PipelineRepo(self.session)
        self.referrals = ReferralRepo(self.session)
        self.push_subs = BaseRepository(PushSubscription, self.session)
        self.audit = BaseRepository(AuditLog, self.session)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.session.rollback()
        self.session.close()

    def commit(self):
        self.session.commit()

    def flush(self):
        self.session.flush()


# =============================================================================
# BASE REPOSITORY (generic CRUD)
# =============================================================================


class BaseRepository(Generic[T]):
    def __init__(self, model: Type[T], session: Session):
        self.model = model
        self.session = session

    def get(self, id: int) -> Optional[T]:
        return self.session.get(self.model, id)

    def get_all(self, limit: int = 100, offset: int = 0):
        return self.session.query(self.model).limit(limit).offset(offset).all()

    def create(self, entity: T) -> T:
        self.session.add(entity)
        self.session.flush()
        return entity

    def delete(self, entity: T):
        self.session.delete(entity)

    def count(self) -> int:
        return self.session.query(self.model).count()


# =============================================================================
# SPECIFIC REPOSITORIES
# =============================================================================


class UserRepo(BaseRepository[User]):
    def __init__(self, session: Session):
        super().__init__(User, session)

    def get_by_email(self, email: str) -> Optional[User]:
        return self.session.query(User).filter(User.email == email).first()

    def get_by_referral_code(self, code: str) -> Optional[User]:
        return self.session.query(User).filter(User.referral_code == code).first()

    def get_active_with_notifications(self):
        return (
            self.session.query(User)
            .filter(
                User.notifications_enabled == True,
                User.email_verified == True,
            )
            .all()
        )

    def get_admins(self):
        return self.session.query(User).filter(User.is_admin == True).all()

    def search(self, query: str, limit: int = 50):
        pattern = f"%{query}%"
        return (
            self.session.query(User)
            .filter((User.email.ilike(pattern)) | (User.company_name.ilike(pattern)))
            .limit(limit)
            .all()
        )

    def can_receive_alert(self, user: User) -> bool:
        """Check if user can receive an alert (respects free tier weekly limit)."""
        # Paid plans have no limit
        if user.plan not in ("free", "trial", "expired"):
            return True

        # For trial users, check if trial is still active
        if user.plan == "trial" and user.is_trial_active():
            return True

        # Free tier: max 3 alerts per week
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)

        # Reset counter if week has passed
        if not user.alerts_week_start or user.alerts_week_start < week_ago:
            user.alerts_week_start = now
            user.alerts_sent_this_week = 0
            return True

        # Check limit (3 alerts per week for free)
        return user.alerts_sent_this_week < 3

    def increment_alert_count(self, user: User):
        """Increment the weekly alert counter."""
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)

        # Reset if new week
        if not user.alerts_week_start or user.alerts_week_start < week_ago:
            user.alerts_week_start = now
            user.alerts_sent_this_week = 1
        else:
            user.alerts_sent_this_week = (user.alerts_sent_this_week or 0) + 1


class ContractRepo(BaseRepository[Contract]):
    def __init__(self, session: Session):
        super().__init__(Contract, session)

    def get_by_external_id(self, external_id: str) -> Optional[Contract]:
        return self.session.query(Contract).filter(Contract.external_id == external_id).first()

    def get_expiring_soon(self, days: int = 3):
        now = datetime.utcnow()
        limit = now + timedelta(days=days)
        return (
            self.session.query(Contract)
            .filter(
                Contract.deadline != None,
                Contract.deadline >= now,
                Contract.deadline <= limit,
            )
            .order_by(Contract.deadline.asc())
            .all()
        )

    def get_without_embedding(self, limit: int = 100):
        return self.session.query(Contract).filter(Contract.embedding == None).limit(limit).all()

    def get_recent(self, limit: int = 50):
        return self.session.query(Contract).order_by(Contract.created_at.desc()).limit(limit).all()


class SubscriptionRepo(BaseRepository[Subscription]):
    def __init__(self, session: Session):
        super().__init__(Subscription, session)

    def get_active_for_user(self, user_id: int) -> Optional[Subscription]:
        return (
            self.session.query(Subscription)
            .filter(
                Subscription.user_id == user_id,
                Subscription.status == "active",
                Subscription.ends_at > datetime.utcnow(),
            )
            .first()
        )


class PaymentRepo(BaseRepository[Payment]):
    def __init__(self, session: Session):
        super().__init__(Payment, session)

    def get_by_wompi_ref(self, ref: str) -> Optional[Payment]:
        return self.session.query(Payment).filter(Payment.wompi_ref == ref).first()

    def get_for_user(self, user_id: int, limit: int = 20):
        return (
            self.session.query(Payment)
            .filter(Payment.user_id == user_id)
            .order_by(Payment.created_at.desc())
            .limit(limit)
            .all()
        )


class MagicLinkRepo(BaseRepository[MagicLink]):
    def __init__(self, session: Session):
        super().__init__(MagicLink, session)

    def get_valid_by_hash(self, token_hash: str) -> Optional[MagicLink]:
        return (
            self.session.query(MagicLink)
            .filter(
                MagicLink.token_hash == token_hash,
                MagicLink.used_at == None,
                MagicLink.expires_at > datetime.utcnow(),
            )
            .first()
        )

    def get_by_hash(self, token_hash: str) -> Optional[MagicLink]:
        """Get link by hash without validity checks (for debugging)."""
        return (
            self.session.query(MagicLink)
            .filter(
                MagicLink.token_hash == token_hash,
            )
            .first()
        )

    def get_failure_reason(self, token_hash: str) -> str:
        """Return specific reason why a token is invalid."""
        link = self.get_by_hash(token_hash)
        if not link:
            return "not_found"  # Token never existed
        if link.used_at is not None:
            return "already_used"  # Token was already used
        if link.expires_at <= datetime.utcnow():
            return "expired"  # Token expired
        return "valid"  # Should not happen


class PipelineRepo(BaseRepository[PipelineEntry]):
    def __init__(self, session: Session):
        super().__init__(PipelineEntry, session)

    def get_for_user(self, user_id: int):
        return (
            self.session.query(PipelineEntry)
            .filter(PipelineEntry.user_id == user_id)
            .order_by(PipelineEntry.updated_at.desc())
            .all()
        )

    def get_by_stage(self, user_id: int, stage: str):
        return (
            self.session.query(PipelineEntry)
            .filter(
                PipelineEntry.user_id == user_id,
                PipelineEntry.stage == stage,
            )
            .all()
        )


class ReferralRepo(BaseRepository[Referral]):
    def __init__(self, session: Session):
        super().__init__(Referral, session)

    def get_by_code(self, code: str) -> Optional[Referral]:
        return self.session.query(Referral).filter(Referral.code == code).first()

    def count_for_referrer(self, referrer_id: int, status: str = "subscribed") -> int:
        return (
            self.session.query(Referral)
            .filter(
                Referral.referrer_id == referrer_id,
                Referral.status == status,
            )
            .count()
        )

    def get_for_referrer(self, referrer_id: int):
        return (
            self.session.query(Referral)
            .filter(Referral.referrer_id == referrer_id)
            .order_by(Referral.clicked_at.desc())
            .all()
        )
