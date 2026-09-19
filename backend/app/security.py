"""API key authentication + webhook signatures (stdlib only).

No dependency on `cryptography`: hashing and signatures via `hashlib`/`hmac`.
"""

from __future__ import annotations

import hashlib
import hmac
import os

from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import get_db
from .models import Client


def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


def sign_payload(secret: str, body: bytes) -> str:
    """HMAC-SHA256 signature of a webhook payload (header X-DeepGuard-Signature)."""
    return hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


def verify_signature(secret: str, body: bytes, signature: str) -> bool:
    return hmac.compare_digest(sign_payload(secret, body), signature)


async def current_client(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    db: Session = Depends(get_db),
) -> Client:
    """FastAPI dependency: resolves the client from the API key.

    In demo mode (DEEP_GUARD_ALLOW_ANON=true), a missing key returns a demo
    client — convenient for testing without onboarding.
    """
    allow_anon = _allow_anon()
    if not x_api_key:
        if allow_anon:
            demo = db.scalar(select(Client).where(Client.email == "demo@deepguard.local"))
            if demo:
                return demo
        raise HTTPException(status_code=401, detail="Missing API key (header X-API-Key).")

    hashed = hash_api_key(x_api_key)
    client = db.scalar(select(Client).where(Client.api_key == hashed))
    if not client or not client.active:
        raise HTTPException(status_code=401, detail="Invalid or inactive API key.")
    return client


def _allow_anon() -> bool:
    return os.getenv("DEEP_GUARD_ALLOW_ANON", "false").lower() == "true"


def enforce_quota(client: Client) -> None:
    if client.used_this_month >= client.quota_monthly:
        raise HTTPException(status_code=429, detail="Monthly quota reached for this client.")


def get_webhook_secret() -> str:
    """Get webhook signing secret from env. Raises if not configured."""
    secret = os.getenv("DG_WEBHOOK_SECRET", "")
    if not secret:
        raise RuntimeError(
            "DG_WEBHOOK_SECRET must be set. "
            "Generate one with: python -c 'import secrets; print(secrets.token_hex(32))'"
        )
    return secret
