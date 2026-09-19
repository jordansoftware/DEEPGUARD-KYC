"""Validation schemas (Pydantic) for the public DeepGuard API."""

from __future__ import annotations

import re

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Clients / API keys
# ---------------------------------------------------------------------------

class ClientCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=5, max_length=200)
    plan: str = Field(default="free", pattern="^(free|starter|pro|enterprise)$")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$", v):
            raise ValueError("Invalid email address")
        return v.lower()


class ClientOut(BaseModel):
    id: int
    name: str
    email: str
    api_key: str = ""
    plan: str
    quota_monthly: int
    used_this_month: int
    active: bool
    created_at: str


class KeyRotateOut(BaseModel):
    id: int
    api_key: str  # new key, shown once only
    rotated_at: str


# ---------------------------------------------------------------------------
# KYC / analysis
# ---------------------------------------------------------------------------

class SignalsOut(BaseModel):
    forensic: dict
    ocr: dict
    face: dict
    aml: dict


class CaseCreate(BaseModel):
    applicant: str = Field(default="", max_length=200)
    doc_type: str = Field(default="autre", max_length=40)
    reference: str = Field(default="", max_length=120)
    country: str = Field(default="FR", max_length=3)


class CaseOut(BaseModel):
    id: int
    reference: str
    applicant: str
    country: str
    doc_type: str
    status: str
    score: int
    verdict: str
    verdict_label: str
    submitted_at: str


class CaseDetail(CaseOut):
    signals: dict
    reasons: list[str]
    documents: list[dict]
    history: list[dict]


class DecisionIn(BaseModel):
    action: str = Field(pattern="^(approved|rejected|review)$")


# ---------------------------------------------------------------------------
# AML Screening
# ---------------------------------------------------------------------------

class ScreeningIn(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    birth_date: str = Field(default="", max_length=20)
    country: str = Field(default="", max_length=3)


class ScreeningOut(BaseModel):
    query_name: str
    kind: str
    matched: bool
    match_score: float
    matches: list[dict]
    source: str


# ---------------------------------------------------------------------------
# Webhooks
# ---------------------------------------------------------------------------

class WebhookCreate(BaseModel):
    url: str = Field(min_length=8, max_length=500)
    events: list[str] = Field(default_factory=list)
    active: bool = True


class WebhookOut(BaseModel):
    id: int
    client_id: int
    url: str
    events: list[str]
    active: bool
    created_at: str


class WebhookTestOut(BaseModel):
    ok: bool
    status_code: int
    elapsed_ms: int
    message: str


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

class ReportOut(BaseModel):
    case_id: int
    filename: str
    engine: str
    generated_at: str


# ---------------------------------------------------------------------------
# Rules Engine
# ---------------------------------------------------------------------------

class ThresholdsUpdate(BaseModel):
    auto_approve_score: int = Field(ge=0, le=100, default=15)
    auto_reject_score: int = Field(ge=0, le=100, default=70)
    sla_hours: int = Field(ge=1, le=720, default=48)


class RulesUpdate(BaseModel):
    weights: dict[str, float] | None = None
    defect_weights: dict[str, int] | None = None
    thresholds: ThresholdsUpdate | None = None
