"""Analytics dashboard — aggregate statistics and trends."""

from __future__ import annotations

import datetime as dt
from collections import Counter

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Case, Client, Document, DecisionLog, CaseStatus
from app.security import current_client

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/overview")
def get_overview(
    db: Session = Depends(get_db),
    client: Client = Depends(current_client),
):
    """Get high-level analytics overview."""
    base = db.query(Case).filter(Case.client_id == client.id)
    total = base.count()

    status_counts = dict(
        db.query(Case.status, func.count(Case.id))
        .filter(Case.client_id == client.id)
        .group_by(Case.status)
        .all()
    )

    avg_score = db.query(func.avg(Case.score)).filter(Case.client_id == client.id).scalar() or 0

    verdict_counts = dict(
        db.query(Case.verdict, func.count(Case.id))
        .filter(Case.client_id == client.id)
        .group_by(Case.verdict)
        .all()
    )

    return {
        "total_cases": total,
        "by_status": {
            "pending": status_counts.get(CaseStatus.pending, 0),
            "processing": status_counts.get(CaseStatus.processing, 0),
            "review": status_counts.get(CaseStatus.review, 0),
            "approved": status_counts.get(CaseStatus.approved, 0),
            "rejected": status_counts.get(CaseStatus.rejected, 0),
            "expired": status_counts.get(CaseStatus.expired, 0),
        },
        "average_score": round(float(avg_score), 1),
        "verdicts": verdict_counts,
        "approval_rate": round(
            status_counts.get(CaseStatus.approved, 0) / max(total, 1) * 100, 1
        ),
    }


@router.get("/trends")
def get_trends(
    days: int = Query(ge=1, le=365, default=30),
    db: Session = Depends(get_db),
    client: Client = Depends(current_client),
):
    """Get case creation trends over the last N days."""
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)
    cases = (
        db.query(Case)
        .filter(Case.client_id == client.id, Case.created_at >= cutoff)
        .all()
    )

    daily = {}
    for case in cases:
        day = case.created_at.strftime("%Y-%m-%d")
        if day not in daily:
            daily[day] = {"total": 0, "approved": 0, "rejected": 0, "review": 0, "scores": []}
        daily[day]["total"] += 1
        daily[day]["scores"].append(case.score)
        if case.status == CaseStatus.approved:
            daily[day]["approved"] += 1
        elif case.status == CaseStatus.rejected:
            daily[day]["rejected"] += 1
        elif case.status == CaseStatus.review:
            daily[day]["review"] += 1

    trends = []
    for day in sorted(daily.keys()):
        d = daily[day]
        trends.append({
            "date": day,
            "total": d["total"],
            "approved": d["approved"],
            "rejected": d["rejected"],
            "review": d["review"],
            "avg_score": round(sum(d["scores"]) / len(d["scores"]), 1) if d["scores"] else 0,
        })

    return {"trends": trends, "days": days}


@router.get("/risk-distribution")
def get_risk_distribution(
    db: Session = Depends(get_db),
    client: Client = Depends(current_client),
):
    """Get score distribution across all cases."""
    base = db.query(Case).filter(Case.client_id == client.id)
    total = base.count()

    buckets = {"0-20": 0, "21-40": 0, "41-60": 0, "61-80": 0, "81-100": 0}
    for case in base.all():
        s = case.score
        if s <= 20:
            buckets["0-20"] += 1
        elif s <= 40:
            buckets["21-40"] += 1
        elif s <= 60:
            buckets["41-60"] += 1
        elif s <= 80:
            buckets["61-80"] += 1
        else:
            buckets["81-100"] += 1

    return {"distribution": buckets, "total": total}


@router.get("/signal-averages")
def get_signal_averages(
    db: Session = Depends(get_db),
    client: Client = Depends(current_client),
):
    """Get average signal scores across all documents."""
    docs = (
        db.query(Document)
        .join(Case, Document.case_id == Case.id)
        .filter(Case.client_id == client.id)
        .all()
    )

    signal_sums = {}
    signal_counts = {}
    for doc in docs:
        if doc.signals:
            for key, val in doc.signals.items():
                if isinstance(val, dict) and "score" in val:
                    signal_sums[key] = signal_sums.get(key, 0) + val["score"]
                    signal_counts[key] = signal_counts.get(key, 0) + 1

    averages = {
        key: round(signal_sums[key] / max(signal_counts[key], 1), 2)
        for key in signal_sums
    }

    return {"averages": averages, "document_count": len(docs)}


@router.get("/sla-compliance")
def get_sla_compliance(
    db: Session = Depends(get_db),
    client: Client = Depends(current_client),
):
    """Get SLA compliance metrics."""
    now = dt.datetime.now(dt.timezone.utc)
    cases = (
        db.query(Case)
        .filter(Case.client_id == client.id, Case.status == CaseStatus.review)
        .all()
    )

    overdue = 0
    on_track = 0
    for case in cases:
        if case.sla_deadline and case.sla_deadline < now:
            overdue += 1
        else:
            on_track += 1

    return {
        "overdue": overdue,
        "on_track": on_track,
        "total_in_review": len(cases),
        "compliance_rate": round(on_track / max(len(cases), 1) * 100, 1),
    }
