"""Custom rules engine — per-client configurable weights and thresholds."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.models import Client, ClientRules
from app.schemas import RulesUpdate
from app.security import current_client
from app.workflow import WEIGHTS, DEFECT_WEIGHTS

router = APIRouter(prefix="/api/rules", tags=["rules"])
settings = get_settings()


@router.get("/defaults")
def get_defaults(client: Client = Depends(current_client)):
    """Get default rules configuration."""
    return {
        "weights": WEIGHTS,
        "defect_weights": DEFECT_WEIGHTS,
        "thresholds": {
            "auto_approve_score": settings.auto_approve_score,
            "auto_reject_score": settings.auto_reject_score,
            "sla_hours": settings.default_sla_hours,
            "face_match_threshold": settings.face_match_threshold,
            "doc_expiry_penalty": settings.doc_expiry_penalty,
        },
    }


@router.get("/client/{client_id}")
def get_client_rules(
    client_id: int,
    db: Session = Depends(get_db),
    client: Client = Depends(current_client),
):
    """Get rules for a specific client."""
    if client.id != client_id:
        raise HTTPException(status_code=403, detail="Cannot access another client's rules.")
    rules = db.query(ClientRules).filter(ClientRules.client_id == client_id).first()
    if not rules:
        return {
            "client_id": client_id,
            "weights": WEIGHTS,
            "defect_weights": DEFECT_WEIGHTS,
            "thresholds": {
                "auto_approve_score": settings.auto_approve_score,
                "auto_reject_score": settings.auto_reject_score,
                "sla_hours": settings.default_sla_hours,
            },
            "custom": False,
        }
    return {
        "client_id": client_id,
        "weights": {**WEIGHTS, **(rules.weights or {})},
        "defect_weights": {**DEFECT_WEIGHTS, **(rules.defect_weights or {})},
        "thresholds": {
            "auto_approve_score": settings.auto_approve_score,
            "auto_reject_score": settings.auto_reject_score,
            "sla_hours": settings.default_sla_hours,
            **(rules.thresholds or {}),
        },
        "custom": True,
    }


@router.put("/client/{client_id}")
def update_client_rules(
    client_id: int,
    payload: RulesUpdate,
    db: Session = Depends(get_db),
    client: Client = Depends(current_client),
):
    """Update rules for a specific client."""
    if client.id != client_id:
        raise HTTPException(status_code=403, detail="Cannot modify another client's rules.")
    rules = db.query(ClientRules).filter(ClientRules.client_id == client_id).first()

    if not rules:
        rules = ClientRules(client_id=client_id)
        db.add(rules)

    if payload.weights is not None:
        rules.weights = payload.weights
    if payload.defect_weights is not None:
        rules.defect_weights = payload.defect_weights
    if payload.thresholds is not None:
        rules.thresholds = payload.thresholds.model_dump()

    db.commit()
    db.refresh(rules)
    return rules.to_dict()


@router.delete("/client/{client_id}")
def reset_client_rules(
    client_id: int,
    db: Session = Depends(get_db),
    client: Client = Depends(current_client),
):
    """Reset client rules to defaults."""
    if client.id != client_id:
        raise HTTPException(status_code=403, detail="Cannot modify another client's rules.")
    rules = db.query(ClientRules).filter(ClientRules.client_id == client_id).first()
    if rules:
        db.delete(rules)
        db.commit()
    return {"status": "reset"}


@router.get("/all")
def list_all_rules(
    db: Session = Depends(get_db),
    client: Client = Depends(current_client),
):
    """List all client rule configurations."""
    rules = db.query(ClientRules).all()
    return {"rules": [r.to_dict() for r in rules]}
