"""DeepGuard data models — full KYC.

Organization:
- Client        : company (multi-tenant) calling the API (API key, quota).
- Case          : KYC case for an individual, composed of multiple documents.
- Document      : attachment (ID card, passport, selfie, proof of address...) +
                  analysis result (score, signals, heatmap, OCR, face match).
- Screening     : AML / sanctions screening result for a case.
- DecisionLog   : audit log (compliance traceability).
- Webhook / WebhookDelivery : outgoing notifications to the client.
"""

from __future__ import annotations

import datetime as dt
import enum
import secrets

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .config import get_settings
from .db import Base

settings = get_settings()


def _now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


class CaseStatus(str, enum.Enum):
    pending = "pending"          # awaiting documents
    processing = "processing"    # automatic analysis in progress
    review = "review"            # human review required
    approved = "approved"        # validated
    rejected = "rejected"        # rejected
    expired = "expired"          # SLA exceeded


class DocType(str, enum.Enum):
    cni = "cni"
    passeport = "passeport"
    selfie = "selfie"
    justificatif = "justificatif"
    permis = "permis"
    titre_sejour = "titre_sejour"
    autre = "autre"


class ScreeningKind(str, enum.Enum):
    sanctions = "sanctions"
    pep = "pep"
    adverse_media = "adverse_media"


class RiskLevel(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    email: Mapped[str] = mapped_column(String(160), unique=True)
    api_key: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    plan: Mapped[str] = mapped_column(String(40), default="free")
    quota_monthly: Mapped[int] = mapped_column(Integer, default=100)
    used_this_month: Mapped[int] = mapped_column(Integer, default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=_now)

    cases: Mapped[list["Case"]] = relationship(back_populates="client")

    @staticmethod
    def new_api_key() -> str:
        return settings.api_key_prefix + secrets.token_urlsafe(32)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "api_key": self.api_key,
            "plan": self.plan,
            "quota_monthly": self.quota_monthly,
            "used_this_month": self.used_this_month,
            "active": self.active,
            "created_at": self.created_at.isoformat(),
        }


class Case(Base):
    __tablename__ = "cases"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int | None] = mapped_column(ForeignKey("clients.id"), nullable=True)
    external_ref: Mapped[str] = mapped_column(String(120), default="", index=True)
    applicant_name: Mapped[str] = mapped_column(String(200), default="")
    applicant_email: Mapped[str] = mapped_column(String(200), default="")
    country: Mapped[str] = mapped_column(String(80), default="")
    status: Mapped[CaseStatus] = mapped_column(Enum(CaseStatus), default=CaseStatus.pending)
    risk_level: Mapped[RiskLevel] = mapped_column(Enum(RiskLevel), default=RiskLevel.low)
    score: Mapped[int] = mapped_column(Integer, default=0)
    verdict: Mapped[str] = mapped_column(String(40), default="inconnu")
    reasons: Mapped[list] = mapped_column(JSON, default=list)
    assigned_to: Mapped[str] = mapped_column(String(120), default="")
    sla_deadline: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    client: Mapped["Client | None"] = relationship(back_populates="cases")
    documents: Mapped[list["Document"]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )
    screenings: Mapped[list["Screening"]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )
    logs: Mapped[list["DecisionLog"]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )

    def doc_summary(self) -> list[dict]:
        return [d.to_dict(include_image=False) for d in self.documents]

    def to_list(self) -> dict:
        return {
            "id": self.id,
            "applicant": self.applicant_name,
            "reference": self.external_ref or f"KYC-{self.id:05d}",
            "doc_type": self.documents[0].doc_type.value if self.documents else "autre",
            "country": self.country or "---",
            "filename": self.documents[0].filename if self.documents else "",
            "submitted_at": self.created_at.isoformat(),
            "status": self.status.value,
            "status_label": STATUS_LABELS.get(self.status.value, self.status.value),
            "score": self.score,
            "verdict": self.verdict,
            "verdict_label": VERDICT_LABELS.get(self.verdict, self.verdict),
            "risk_level": self.risk_level.value,
            "documents_count": len(self.documents),
        }

    def to_detail(self) -> dict:
        d = self.to_list()
        d.update({
            "applicant_email": self.applicant_email,
            "assigned_to": self.assigned_to,
            "sla_deadline": self.sla_deadline.isoformat() if self.sla_deadline else None,
            "reasons": self.reasons or [],
            "documents": [doc.to_dict() for doc in self.documents],
            "screenings": [s.to_dict() for s in self.screenings],
            "history": [log.to_dict() for log in sorted(self.logs, key=lambda x: x.id)],
        })
        return d


STATUS_LABELS = {
    "pending": "Pending",
    "processing": "Processing",
    "review": "Under Review",
    "approved": "Approved",
    "rejected": "Rejected",
    "expired": "Expired",
}

VERDICT_LABELS = {
    "authentique": "Authentique",
    "suspect": "Suspect",
    "forge": "Forged",
    "inconnu": "Unknown",
}


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"))
    doc_type: Mapped[DocType] = mapped_column(Enum(DocType), default=DocType.autre)
    filename: Mapped[str] = mapped_column(String(255), default="")
    stored_path: Mapped[str] = mapped_column(String(500), default="")
    content_type: Mapped[str] = mapped_column(String(120), default="")
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)

    # Forensic result (signals engine)
    score: Mapped[int] = mapped_column(Integer, default=0)
    verdict: Mapped[str] = mapped_column(String(40), default="inconnu")
    signals: Mapped[dict] = mapped_column(JSON, default=dict)
    reasons: Mapped[list] = mapped_column(JSON, default=list)
    image: Mapped[str] = mapped_column(Text, default="")     # dataURL
    heatmap: Mapped[str] = mapped_column(Text, default="")   # dataURL

    # OCR / extraction
    ocr_text: Mapped[str] = mapped_column(Text, default="")
    extracted: Mapped[dict] = mapped_column(JSON, default=dict)

    # Face matching (selfie vs document photo)
    face_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    face_match: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    # Liveness detection
    liveness_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    liveness_result: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Capture device tracking
    capture_device: Mapped[str | None] = mapped_column(String(20), nullable=True)  # mobile/web/unknown

    # Face verification session
    face_session_token: Mapped[str | None] = mapped_column(String(500), nullable=True)
    face_verified_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=_now)

    case: Mapped["Case"] = relationship(back_populates="documents")

    def to_dict(self, include_image: bool = True) -> dict:
        d = {
            "id": self.id,
            "doc_type": self.doc_type.value,
            "filename": self.filename,
            "size_bytes": self.size_bytes,
            "score": self.score,
            "verdict": self.verdict,
            "verdict_label": VERDICT_LABELS.get(self.verdict, self.verdict),
            "signals": self.signals or {},
            "reasons": self.reasons or [],
            "ocr_text": self.ocr_text,
            "extracted": self.extracted or {},
            "face_score": self.face_score,
            "face_match": self.face_match,
            "liveness_score": self.liveness_score,
            "liveness_result": self.liveness_result,
            "capture_device": self.capture_device,
            "face_verified": self.face_verified_at is not None,
        }
        if include_image:
            d["image"] = self.image
            d["heatmap"] = self.heatmap
        return d


class Screening(Base):
    __tablename__ = "screenings"

    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"))
    kind: Mapped[ScreeningKind] = mapped_column(Enum(ScreeningKind), default=ScreeningKind.sanctions)
    query_name: Mapped[str] = mapped_column(String(200), default="")
    matched: Mapped[bool] = mapped_column(Boolean, default=False)
    match_score: Mapped[float] = mapped_column(Float, default=0.0)
    matches: Mapped[list] = mapped_column(JSON, default=list)
    source: Mapped[str] = mapped_column(String(120), default="")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=_now)

    case: Mapped["Case"] = relationship(back_populates="screenings")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "kind": self.kind.value,
            "query_name": self.query_name,
            "matched": self.matched,
            "match_score": self.match_score,
            "matches": self.matches or [],
            "source": self.source,
            "created_at": self.created_at.isoformat(),
        }


class DecisionLog(Base):
    __tablename__ = "decision_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"))
    actor: Mapped[str] = mapped_column(String(120), default="system")
    action: Mapped[str] = mapped_column(String(80), default="")
    from_status: Mapped[str] = mapped_column(String(40), default="")
    to_status: Mapped[str] = mapped_column(String(40), default="")
    note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=_now)

    case: Mapped["Case"] = relationship(back_populates="logs")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "actor": self.actor,
            "action": self.action,
            "from": self.from_status,
            "to": self.to_status,
            "note": self.note,
            "at": self.created_at.isoformat(),
        }


class Webhook(Base):
    __tablename__ = "webhooks"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    url: Mapped[str] = mapped_column(String(500))
    secret: Mapped[str] = mapped_column(String(120), default=lambda: secrets.token_hex(24))
    events: Mapped[list] = mapped_column(JSON, default=list)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=_now)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "client_id": self.client_id,
            "url": self.url,
            "events": self.events or [],
            "active": self.active,
            "created_at": self.created_at.isoformat(),
        }


class WebhookDelivery(Base):
    __tablename__ = "webhook_deliveries"

    id: Mapped[int] = mapped_column(primary_key=True)
    webhook_id: Mapped[int] = mapped_column(ForeignKey("webhooks.id"))
    case_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    event: Mapped[str] = mapped_column(String(80), default="")
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=_now)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "webhook_id": self.webhook_id,
            "case_id": self.case_id,
            "event": self.event,
            "status_code": self.status_code,
            "attempts": self.attempts,
            "last_error": self.last_error,
            "created_at": self.created_at.isoformat(),
        }


class BatchJob(Base):
    __tablename__ = "batch_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int | None] = mapped_column(ForeignKey("clients.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="pending")
    total_files: Mapped[int] = mapped_column(Integer, default=0)
    processed: Mapped[int] = mapped_column(Integer, default=0)
    failed: Mapped[int] = mapped_column(Integer, default=0)
    case_ids: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "client_id": self.client_id,
            "status": self.status,
            "total_files": self.total_files,
            "processed": self.processed,
            "failed": self.failed,
            "case_ids": self.case_ids or [],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class ClientRules(Base):
    __tablename__ = "client_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), unique=True)
    weights: Mapped[dict] = mapped_column(JSON, default=dict)
    defect_weights: Mapped[dict] = mapped_column(JSON, default=dict)
    thresholds: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "client_id": self.client_id,
            "weights": self.weights or {},
            "defect_weights": self.defect_weights or {},
            "thresholds": self.thresholds or {},
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class PluginConfig(Base):
    __tablename__ = "plugin_configs"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "enabled": self.enabled,
            "config": self.config or {},
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class EmailLog(Base):
    __tablename__ = "email_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    recipient: Mapped[str] = mapped_column(String(200))
    subject: Mapped[str] = mapped_column(String(500))
    event: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(40), default="pending")
    error: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=_now)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "case_id": self.case_id,
            "recipient": self.recipient,
            "subject": self.subject,
            "event": self.event,
            "status": self.status,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
        }
