"""Client management routes (multi-tenant) + API keys + quotas."""

from __future__ import annotations

import logging
import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Client
from ..schemas import ClientCreate, ClientOut, KeyRotateOut
from ..security import current_client, hash_api_key

logger = logging.getLogger("deepguard.clients")

router = APIRouter(prefix="/api/clients", tags=["clients"])


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _out(c: Client, raw_key: str = "") -> ClientOut:
    return ClientOut(
        id=c.id, name=c.name, email=c.email, api_key=raw_key,
        plan=c.plan, quota_monthly=c.quota_monthly,
        used_this_month=c.used_this_month, active=c.active,
        created_at=c.created_at.isoformat() if c.created_at else _now(),
    )


@router.post("", response_model=ClientOut, status_code=201)
def create_client(
    payload: ClientCreate,
    db: Session = Depends(get_db),
    client: Client = Depends(current_client),
) -> ClientOut:
    if db.scalar(select(Client).where(Client.email == payload.email)):
        raise HTTPException(409, "A client with this email already exists.")
    raw_key = "dg_" + secrets.token_urlsafe(24)
    c = Client(
        name=payload.name, email=payload.email,
        api_key=hash_api_key(raw_key), plan=payload.plan,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return _out(c, raw_key=raw_key)


@router.get("", response_model=list[ClientOut])
def list_clients(
    db: Session = Depends(get_db),
    client: Client = Depends(current_client),
) -> list[ClientOut]:
    rows = db.scalars(select(Client).order_by(Client.id.desc())).all()
    return [_out(c) for c in rows]


@router.get("/{client_id}", response_model=ClientOut)
def get_client(
    client_id: int,
    db: Session = Depends(get_db),
    client: Client = Depends(current_client),
) -> ClientOut:
    if client.id != client_id:
        raise HTTPException(403, "Cannot access another client's data.")
    c = db.get(Client, client_id)
    if not c:
        raise HTTPException(404, "Client not found.")
    return _out(c)


@router.get("/{client_id}/usage")
def client_usage(
    client_id: int,
    db: Session = Depends(get_db),
    client: Client = Depends(current_client),
) -> dict:
    if client.id != client_id:
        raise HTTPException(403, "Cannot access another client's data.")
    c = db.get(Client, client_id)
    if not c:
        raise HTTPException(404, "Client not found.")
    remaining = max(0, c.quota_monthly - c.used_this_month)
    return {
        "client_id": c.id, "name": c.name, "plan": c.plan,
        "quota_monthly": c.quota_monthly, "used_this_month": c.used_this_month,
        "remaining": remaining,
        "pct": round(100 * c.used_this_month / max(1, c.quota_monthly), 1),
    }


@router.delete("/{client_id}", status_code=204)
def deactivate_client(
    client_id: int,
    db: Session = Depends(get_db),
    client: Client = Depends(current_client),
) -> None:
    if client.id != client_id:
        raise HTTPException(403, "Cannot deactivate another client.")
    c = db.get(Client, client_id)
    if not c:
        raise HTTPException(404, "Client not found.")
    c.active = False
    db.commit()


@router.post("/{client_id}/rotate-key", response_model=KeyRotateOut)
def rotate_key(
    client_id: int,
    db: Session = Depends(get_db),
    client: Client = Depends(current_client),
) -> KeyRotateOut:
    if client.id != client_id:
        raise HTTPException(403, "Cannot rotate another client's key.")
    c = db.get(Client, client_id)
    if not c:
        raise HTTPException(404, "Client not found.")
    new_key = "dg_" + secrets.token_urlsafe(24)
    c.api_key = hash_api_key(new_key)
    db.commit()
    db.refresh(c)
    return KeyRotateOut(id=c.id, api_key=new_key, rotated_at=_now())
