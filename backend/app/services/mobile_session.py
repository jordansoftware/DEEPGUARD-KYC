"""Mobile face verification session — QR code generation + JWT tokens.

Security:
- Tokens are single-use and deleted after completion
- JWT includes aud/iss claims for defense in depth
- Expired sessions are cleaned up periodically
- Thread-safe session mutations via Lock
"""

from __future__ import annotations

import asyncio
import hmac
import io
import logging
import os
import re
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import jwt
import qrcode

from app.config import get_settings

logger = logging.getLogger("deepguard.mobile_session")

settings = get_settings()

# In-memory session store (production: use Redis)
_sessions: dict[str, dict] = {}
_consumed_tokens: set[str] = set()  # tracks used tokens to prevent replay
_session_lock = threading.Lock()

# Valid image magic bytes
IMAGE_SIGNATURES = {
    b"\x89PNG": "image/png",
    b"\xff\xd8\xff": "image/jpeg",
    b"RIFF": "image/webp",  # webp starts with RIFF
    b"II": "image/tiff",
    b"MM": "image/tiff",
}

MAX_SELFIE_SIZE = settings.selfie_max_size_mb * 1024 * 1024


def _cleanup_expired():
    """Remove expired sessions from memory. Called periodically."""
    now = time.time()
    with _session_lock:
        expired = [t for t, s in _sessions.items() if now > s["expires_at"]]
        for t in expired:
            del _sessions[t]
        if expired:
            logger.info("Cleaned up %d expired face sessions", len(expired))


def _start_cleanup_timer():
    """Start background cleanup thread."""
    def _loop():
        while True:
            time.sleep(60)
            _try_cleanup()

    t = threading.Thread(target=_loop, daemon=True, name="session-cleanup")
    t.start()


def _try_cleanup():
    try:
        _cleanup_expired()
    except Exception:
        logger.exception("Session cleanup failed")


# Start cleanup on module load
_start_cleanup_timer()


def _create_token(case_id: int) -> str:
    """Create a short-lived JWT token for face verification."""
    payload = {
        "case_id": case_id,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.face_session_ttl_minutes),
        "iat": datetime.now(timezone.utc),
        "type": "face_verification",
        "iss": "deepguard",
        "aud": "mobile-face-verify",
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def verify_token(token: str) -> dict | None:
    """Verify and decode a face verification token. Returns payload or None."""
    # Check if token was already consumed
    if token in _consumed_tokens:
        logger.warning("Attempt to reuse consumed token")
        return None

    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=["HS256"],
            audience="mobile-face-verify",
            issuer="deepguard",
        )
        if not hmac.compare_digest(payload.get("type", ""), "face_verification"):
            return None
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Face verification token expired")
        return None
    except jwt.InvalidTokenError:
        logger.warning("Invalid face verification token")
        return None


def _validate_image_header(data: bytes) -> bool:
    """Check if file data starts with a valid image magic number."""
    for sig in IMAGE_SIGNATURES:
        if data[:len(sig)] == sig:
            return True
    return False


def create_face_session(case_id: int) -> dict:
    """Create a new face verification session for a KYC case.

    Returns dict with token, qr_code (dataURL), qr_url, expires_at.
    """
    with _session_lock:
        # Invalidate any existing session for this case
        for tok, session in list(_sessions.items()):
            if session["case_id"] == case_id and session["status"] == "pending":
                session["status"] = "expired"

        token = _create_token(case_id)
        now = time.time()
        ttl_seconds = settings.face_session_ttl_minutes * 60

        session = {
            "case_id": case_id,
            "token": token,
            "created_at": now,
            "expires_at": now + ttl_seconds,
            "status": "pending",
            "selfie_path": None,
            "liveness_result": None,
            "face_result": None,
            "capture_device": None,
        }
        _sessions[token] = session

    # Generate QR code (outside lock — CPU-intensive)
    verify_url = f"{settings.qr_code_base_url}/mobile/verify?token={token}"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(verify_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    # Convert to dataURL
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    import base64
    qr_data_url = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

    return {
        "token": token,
        "qr_code": qr_data_url,
        "qr_url": verify_url,
        "expires_at": datetime.fromtimestamp(now + ttl_seconds, tz=timezone.utc).isoformat(),
        "ttl_minutes": settings.face_session_ttl_minutes,
    }


def get_session(token: str) -> dict | None:
    """Get a face verification session by token."""
    if token in _consumed_tokens:
        return None
    with _session_lock:
        session = _sessions.get(token)
        if not session:
            return None
        if time.time() > session["expires_at"]:
            session["status"] = "expired"
        return dict(session)  # return copy


def complete_session(
    token: str,
    selfie_data: bytes,
    liveness_result: dict,
    face_result: dict,
    capture_device: str,
) -> dict | None:
    """Validate selfie, mark session as completed, and consume the token.

    Args:
        token: Face verification JWT token
        selfie_data: Raw selfie image bytes (validated for size + format)
        liveness_result: Liveness detection result dict
        face_result: Face matching result dict
        capture_device: "mobile" | "web" | "unknown"

    Returns:
        Completed session dict or None if invalid
    """
    # Validate selfie data
    if not selfie_data or len(selfie_data) < 100:
        logger.warning("Selfie data too small")
        return None
    if len(selfie_data) > MAX_SELFIE_SIZE:
        logger.warning("Selfie exceeds max size: %d bytes", len(selfie_data))
        return None
    if not _validate_image_header(selfie_data[:16]):
        logger.warning("Selfie is not a valid image")
        return None

    with _session_lock:
        session = _sessions.get(token)
        if not session:
            return None
        if session["status"] != "pending":
            return None
        if time.time() > session["expires_at"]:
            session["status"] = "expired"
            return None

        # Mark as completed
        session["status"] = "completed"
        session["liveness_result"] = liveness_result
        session["face_result"] = face_result
        session["capture_device"] = capture_device

        # Save selfie to temp file
        import tempfile
        import uuid
        suffix = ".jpg"
        tmp = os.path.join(tempfile.gettempdir(), "deepguard", f"selfie_{uuid.uuid4().hex}{suffix}")
        os.makedirs(os.path.dirname(tmp), exist_ok=True)
        with open(tmp, "wb") as f:
            f.write(selfie_data)
        os.chmod(tmp, 0o600)
        session["selfie_path"] = tmp

        # Consume token — prevent replay
        _consumed_tokens.add(token)
        result = dict(session)

    return result


def get_session_status(token: str) -> dict | None:
    """Get the status of a face verification session."""
    if token in _consumed_tokens:
        # Token was consumed — return completed status without leaking data
        return {"status": "completed", "case_id": None}
    with _session_lock:
        session = _sessions.get(token)
        if not session:
            return None
        if time.time() > session["expires_at"]:
            session["status"] = "expired"
        return {
            "status": session["status"],
            "case_id": session["case_id"],
            "expires_at": datetime.fromtimestamp(session["expires_at"], tz=timezone.utc).isoformat(),
            "face_result": session.get("face_result"),
            "liveness_result": session.get("liveness_result"),
        }


def invalidate_token(token: str) -> bool:
    """Explicitly invalidate a token."""
    with _session_lock:
        if token in _sessions:
            _sessions[token]["status"] = "expired"
            _consumed_tokens.add(token)
            return True
    return False
