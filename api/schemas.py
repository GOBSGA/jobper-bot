"""
Jobper API — Pydantic schemas for input validation
Every user input goes through these schemas before reaching services.
"""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional, Literal

from pydantic import BaseModel, EmailStr, Field, field_validator

from core.security import sanitize_html, sanitize_search_query


# =============================================================================
# AUTH
# =============================================================================

class LoginSchema(BaseModel):
    email: EmailStr


class VerifySchema(BaseModel):
    token: str = Field(min_length=32, max_length=128)
    referral_code: Optional[str] = Field(None, max_length=20)


class RefreshSchema(BaseModel):
    refresh_token: str = Field(min_length=10)


# =============================================================================
# PROFILE
# =============================================================================

class ProfileUpdateSchema(BaseModel):
    company_name: Optional[str] = Field(None, max_length=200)
    sector: Optional[str] = Field(None, max_length=500)
    keywords: Optional[List[str]] = Field(None, max_length=50)
    notifications_enabled: Optional[bool] = None
    city: Optional[str] = Field(None, max_length=100)
    budget_min: Optional[float] = Field(None, ge=0)
    budget_max: Optional[float] = Field(None, ge=0)
    whatsapp_number: Optional[str] = Field(None, max_length=20)
    whatsapp_enabled: Optional[bool] = None

    @field_validator("company_name", "sector", "city", mode="before")
    @classmethod
    def sanitize_text(cls, v):
        return sanitize_html(v) if v else v

    @field_validator("keywords", mode="before")
    @classmethod
    def sanitize_keywords(cls, v):
        if v:
            return [sanitize_html(kw)[:100] for kw in v[:50]]
        return v


# =============================================================================
# CONTRACTS
# =============================================================================

class SearchSchema(BaseModel):
    query: str = Field("", max_length=500)
    page: int = Field(1, ge=1, le=1000)
    per_page: int = Field(20, ge=1, le=100)

    @field_validator("query", mode="before")
    @classmethod
    def sanitize_query(cls, v):
        return sanitize_search_query(v) if v else ""


class ContractIdSchema(BaseModel):
    contract_id: int = Field(ge=1)


class FavoriteSchema(BaseModel):
    contract_id: int = Field(ge=1)


# =============================================================================
# PIPELINE
# =============================================================================

PIPELINE_STAGES = ("lead", "proposal", "submitted", "won", "lost")


class PipelineAddSchema(BaseModel):
    contract_id: Optional[int] = Field(None, ge=1)
    private_contract_id: Optional[int] = Field(None, ge=1)
    stage: Literal["lead", "proposal", "submitted", "won", "lost"] = "lead"
    value: Optional[float] = Field(None, ge=0)


class PipelineMoveSchema(BaseModel):
    stage: Literal["lead", "proposal", "submitted", "won", "lost"]


class PipelineNoteSchema(BaseModel):
    text: str = Field(min_length=1, max_length=2000)

    @field_validator("text", mode="before")
    @classmethod
    def sanitize_text(cls, v):
        return sanitize_html(v) if v else v


# =============================================================================
# MARKETPLACE
# =============================================================================

class PublishContractSchema(BaseModel):
    title: str = Field(min_length=5, max_length=500)
    description: Optional[str] = Field(None, max_length=5000)
    category: Optional[str] = Field(None, max_length=100)
    budget_min: Optional[float] = Field(None, ge=0)
    budget_max: Optional[float] = Field(None, ge=0)
    city: Optional[str] = Field(None, max_length=100)
    is_remote: bool = False
    deadline: Optional[str] = None  # ISO date
    contact_phone: Optional[str] = Field(None, max_length=20)
    keywords: Optional[List[str]] = Field(None, max_length=20)

    @field_validator("title", "description", "category", "city", mode="before")
    @classmethod
    def sanitize_text(cls, v):
        return sanitize_html(v) if v else v

    @field_validator("keywords", mode="before")
    @classmethod
    def sanitize_keywords(cls, v):
        if v:
            return [sanitize_html(kw)[:100] for kw in v[:20]]
        return v


class MarketplaceListSchema(BaseModel):
    page: int = Field(1, ge=1, le=1000)
    per_page: int = Field(20, ge=1, le=100)
    category: Optional[str] = None
    city: Optional[str] = None


# =============================================================================
# PAYMENTS
# =============================================================================

class CheckoutSchema(BaseModel):
    plan: Literal["alertas", "starter", "business", "enterprise"]


# =============================================================================
# REFERRALS
# =============================================================================

class ReferralTrackSchema(BaseModel):
    code: str = Field(min_length=4, max_length=20)


# =============================================================================
# PUSH
# =============================================================================

class PushSubscriptionSchema(BaseModel):
    endpoint: str = Field(min_length=10, max_length=2000)
    keys: Dict[str, str]  # {p256dh: str, auth: str}


# =============================================================================
# ADMIN
# =============================================================================

class AdminListSchema(BaseModel):
    page: int = Field(1, ge=1)
    per_page: int = Field(50, ge=1, le=200)
    search: Optional[str] = Field(None, max_length=200)


class AdminModerateSchema(BaseModel):
    action: Literal["approve", "reject", "delete"]


class AdminLogsSchema(BaseModel):
    page: int = Field(1, ge=1)
    per_page: int = Field(100, ge=1, le=500)
    action: Optional[str] = None
    user_id: Optional[int] = None


# =============================================================================
# SUPPORT
# =============================================================================

class ChatbotSchema(BaseModel):
    question: str = Field(min_length=2, max_length=1000)

    @field_validator("question", mode="before")
    @classmethod
    def sanitize_text(cls, v):
        return sanitize_html(v) if v else v
