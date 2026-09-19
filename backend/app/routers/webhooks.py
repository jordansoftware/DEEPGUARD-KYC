"""Signed outgoing webhooks (Fincra-style).

Each delivery is signed HMAC-SHA256 (`X-DeepGuard-Signature`) with the
webhook secret, on the raw JSON payload body. The `/test` endpoint posts
a dummy `case.completed` event and logs the delivery.
"""

from __future__ import annotations

import ipaddress
import json
import logging
import time
import uuid
from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Client, Webhook, WebhookDelivery
from ..schemas import WebhookCreate, WebhookOut, WebhookTestOut
from ..security import current_client, get_webhook_secret, sign_payload

logger = logging.getLogger("deepguard.webhooks")

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _is_safe_url(url: str) -> bool:
    """Block requests to private/internal/loopback addresses (SSRF protection)."""
    parsed = urlparse(url)
    hostname = parsed.hostname
    if not hostname:
        return False
    try:
        ip = ipaddress.ip_address(hostname)
        return not (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved)
    except ValueError:
        # hostname is a domain — block common internal patterns
        blocked = ["localhost", "127.0.0.1", "0.0.0.0", "169.254.169.254", "metadata.google"]
        return not any(b in hostname.lower() for b in blocked)


def _out(w: Webhook) -> WebhookOut:
    return WebhookOut(
        id=w.id,
        client_id=w.client_id,
        url=w.url,
        events=list(w.events or []),
        active=bool(w.active),
        created_at=w.created_at.isoformat() if w.created_at else _now(),
    )


def _delivery_out(d: WebhookDelivery) -> dict:
    return {
        "id": d.id,
        "webhook_id": d.webhook_id,
        "event": d.event,
        "attempts": d.attempts,
        "status_code": d.status_code,
        "last_error": d.last_error or "",
        "created_at": d.created_at.isoformat() if d.created_at else _now(),
    }


@router.get("", response_model=list[WebhookOut])
def list_webhooks(
    db: Session = Depends(get_db),
    client: Client = Depends(current_client),
) -> list[WebhookOut]:
    rows = db.scalars(
        select(Webhook).where(Webhook.client_id == client.id, Webhook.active).order_by(Webhook.created_at.desc())
    ).all()
    return [_out(w) for w in rows]


@router.post("", response_model=WebhookOut, status_code=201)
def create_webhook(
    payload: WebhookCreate,
    db: Session = Depends(get_db),
    client: Client = Depends(current_client),
) -> WebhookOut:
    parsed = urlparse(payload.url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise HTTPException(status_code=422, detail="Invalid webhook URL.")
    if not _is_safe_url(payload.url):
        raise HTTPException(status_code=422, detail="Webhook URL points to a private/internal address.")
    w = Webhook(
        client_id=client.id,
        url=payload.url,
        events=payload.events or ["case.completed"],
        active=bool(payload.active if payload.active is not None else True),
    )
    db.add(w)
    db.commit()
    db.refresh(w)
    return _out(w)


@router.post("/{webhook_id}/test", response_model=WebhookTestOut)
def test_webhook(
    webhook_id: int,
    db: Session = Depends(get_db),
    client: Client = Depends(current_client),
) -> WebhookTestOut:
    w = db.get(Webhook, webhook_id)
    if not w or w.client_id != client.id:
        raise HTTPException(status_code=404, detail="Webhook not found.")
    payload = {
        "event": "case.completed",
        "reference": "DG-DEMO-" + uuid.uuid4().hex[:8].upper(),
        "verdict": "authentique",
        "score": 92,
        "sent_at": _now(),
    }
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    try:
        secret = get_webhook_secret()
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    signature = sign_payload(secret, body)
    started = time.monotonic()
    try:
        r = httpx.post(
            w.url,
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-DeepGuard-Signature": signature,
                "User-Agent": "DeepGuard/1.0 (+webhooks)",
            },
            timeout=8.0,
            verify=True,
            follow_redirects=False,
        )
        elapsed_ms = int((time.monotonic() - started) * 1000)
    except httpx.HTTPError:
        logger.exception("Webhook delivery failed")
        db.add(
            WebhookDelivery(
                webhook_id=w.id, event="case.completed", attempts=1,
                status_code=None, last_error="Delivery failed",
            )
        )
        db.commit()
        raise HTTPException(status_code=502, detail="Webhook delivery failed.")
    db.add(
        WebhookDelivery(
            webhook_id=w.id, event="case.completed", attempts=1,
            status_code=r.status_code, last_error=None,
        )
    )
    db.commit()
    ok = 200 <= r.status_code < 300
    return WebhookTestOut(
        ok=ok,
        status_code=r.status_code,
        elapsed_ms=elapsed_ms,
        message="Delivery successful." if ok else f"HTTP {r.status_code} received.",
    )


@router.get("/{webhook_id}/deliveries", response_model=list[dict])
def list_deliveries(
    webhook_id: int,
    db: Session = Depends(get_db),
    client: Client = Depends(current_client),
) -> list[dict]:
    w = db.get(Webhook, webhook_id)
    if not w or w.client_id != client.id:
        raise HTTPException(status_code=404, detail="Webhook not found.")
    rows = db.scalars(
        select(WebhookDelivery)
        .where(WebhookDelivery.webhook_id == webhook_id)
        .order_by(WebhookDelivery.id.desc())
        .limit(50)
    ).all()
    return [_delivery_out(d) for d in rows]


@router.delete("/{webhook_id}", status_code=204)
def delete_webhook(
    webhook_id: int,
    db: Session = Depends(get_db),
    client: Client = Depends(current_client),
) -> None:
    w = db.get(Webhook, webhook_id)
    if not w or w.client_id != client.id:
        raise HTTPException(status_code=404, detail="Webhook not found.")
    w.active = False
    db.commit()
