"""DeepGuard configuration — 100% open source.

All values are overridable via environment variables (see .env.example).
No dependency on any proprietary service.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("DEEP_GUARD_DATA_DIR", BASE_DIR / "data"))
UPLOAD_DIR = Path(os.getenv("DEEP_GUARD_UPLOAD_DIR", BASE_DIR / "uploads"))


class Settings:
    """Application settings."""

    app_name: str = "DeepGuard KYC"
    version: str = "1.0.0"

    # Database: SQLite by default, overridable (Postgres possible).
    database_url: str = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR / 'deepguard.db'}")

    # Security — DEEP_GUARD_SECRET_KEY must be set in production
    secret_key: str = os.getenv("DEEP_GUARD_SECRET_KEY", "")
    api_key_prefix: str = "dg_"

    # CORS
    cors_origins: list[str] = [
        o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",") if o.strip()
    ]

    def __post_init__(self) -> None:
        if not self.secret_key:
            import secrets as _secrets
            self.secret_key = _secrets.token_hex(32)

    # AI Engines
    enable_ocr: bool = os.getenv("ENABLE_OCR", "true").lower() == "true"
    enable_facematch: bool = os.getenv("ENABLE_FACEMATCH", "true").lower() == "true"
    enable_liveness: bool = os.getenv("ENABLE_LIVENESS", "true").lower() == "true"
    enable_video_liveness: bool = os.getenv("ENABLE_VIDEO_LIVENESS", "true").lower() == "true"
    enable_address_verify: bool = os.getenv("ENABLE_ADDRESS_VERIFY", "true").lower() == "true"
    face_match_threshold: float = float(os.getenv("FACE_MATCH_THRESHOLD", "0.40"))
    face_match_model: str = os.getenv("FACE_MATCH_MODEL", "VGG-Face")

    # Workflow
    default_sla_hours: int = int(os.getenv("DEFAULT_SLA_HOURS", "48"))
    auto_reject_score: int = int(os.getenv("AUTO_REJECT_SCORE", "70"))
    auto_approve_score: int = int(os.getenv("AUTO_APPROVE_SCORE", "15"))
    doc_expiry_penalty: int = int(os.getenv("DOC_EXPIRY_PENALTY", "5"))

    # Sanctions
    sanctions_file: Path = DATA_DIR / "sanctions.csv"

    # Email notifications
    smtp_host: str = os.getenv("SMTP_HOST", "")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_user: str = os.getenv("SMTP_USER", "")
    smtp_pass: str = os.getenv("SMTP_PASS", "")
    smtp_from: str = os.getenv("SMTP_FROM", "noreply@deepguard.io")
    email_enabled: bool = os.getenv("EMAIL_ENABLED", "false").lower() == "true"

    # WebSocket
    ws_enabled: bool = os.getenv("WS_ENABLED", "true").lower() == "true"

    # Plugins
    plugins_enabled: bool = os.getenv("PLUGINS_ENABLED", "true").lower() == "true"
    plugins_dir: Path = DATA_DIR / "plugins"

    # Batch processing
    batch_max_files: int = int(os.getenv("BATCH_MAX_FILES", "20"))
    batch_max_size_mb: int = int(os.getenv("BATCH_MAX_SIZE_MB", "100"))

    # Face verification (mobile-only)
    face_verification_required: bool = os.getenv("FACE_VERIFICATION_REQUIRED", "true").lower() == "true"
    face_session_ttl_minutes: int = int(os.getenv("FACE_SESSION_TTL_MINUTES", "15"))
    qr_code_base_url: str = os.getenv("QR_CODE_BASE_URL", "http://localhost:3000")
    selfie_max_size_mb: int = int(os.getenv("SELFIE_MAX_SIZE_MB", "10"))


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    s.__post_init__()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    return s
