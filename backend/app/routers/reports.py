from __future__ import annotations
import logging
import os
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from .. import kyc
from ..models import Client
from ..schemas import ReportOut
from ..security import current_client

logger = logging.getLogger("deepguard.reports")

router = APIRouter(prefix="/api/reports", tags=["reports"])
PDF_DIR = "/tmp/deepguard_kyc"


def _generate_kyc_pdf(case: kyc.KycCase) -> str:
    path = os.path.join(PDF_DIR, f"{case.id}_report.pdf")
    os.makedirs(PDF_DIR, exist_ok=True)
    c = canvas.Canvas(path, pagesize=A4)
    w, h = A4
    y = h - 40 * mm
    c.setFont("Helvetica-Bold", 16)
    c.drawString(20 * mm, y, "DeepGuard - KYC Verification Report")
    y -= 15 * mm
    c.setFont("Helvetica", 10)
    fields = [
        ("Reference", case.reference), ("Applicant", case.applicant),
        ("Country", case.country), ("Document type", case.doc_type),
        ("Status", kyc.STATUS_LABELS.get(case.status, case.status)),
        ("Verdict", case.verdict_label), ("Score", str(case.score)),
    ]
    for label, value in fields:
        c.setFont("Helvetica-Bold", 10)
        c.drawString(20 * mm, y, f"{label}:")
        c.setFont("Helvetica", 10)
        c.drawString(80 * mm, y, str(value))
        y -= 6 * mm
    y -= 6 * mm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(20 * mm, y, "Signals")
    y -= 8 * mm
    c.setFont("Helvetica", 9)
    for key in ("forensic", "ocr", "face"):
        data = case.signals.get(key, {})
        label_text = f"{key}: " + ", ".join(f"{k}={v}" for k, v in data.items()) if data else f"{key}: --"
        c.drawString(20 * mm, y, label_text)
        y -= 5 * mm
    y -= 4 * mm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(20 * mm, y, "Reasons")
    y -= 8 * mm
    c.setFont("Helvetica", 9)
    for reason in case.reasons:
        c.drawString(24 * mm, y, f"* {reason}")
        y -= 5 * mm
    y -= 8 * mm
    c.setFont("Helvetica", 9)
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    c.drawString(20 * mm, y, f"Generated on {generated}")
    c.save()
    return path


@router.get("/{case_id}")
def download_report(
    case_id: int,
    client: Client = Depends(current_client),
) -> FileResponse:
    case = kyc.get_case(case_id)
    if not case:
        raise HTTPException(404, "Case not found.")
    pdf_path = _generate_kyc_pdf(case)
    return FileResponse(pdf_path, media_type="application/pdf",
                        filename=f"report_kyc_{case_id}.pdf")


@router.get("", response_model=list[ReportOut])
def list_reports(
    client: Client = Depends(current_client),
) -> list[ReportOut]:
    reports = []
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for case in sorted(kyc._store.values(), key=lambda c: c.id):
        pdf_path = os.path.join(PDF_DIR, f"{case.id}_report.pdf")
        generated = now
        if os.path.exists(pdf_path):
            generated = datetime.fromtimestamp(
                os.path.getmtime(pdf_path), tz=timezone.utc
            ).strftime("%Y-%m-%dT%H:%M:%SZ")
        reports.append(ReportOut(
            case_id=case.id, filename=f"{case.id}_report.pdf",
            engine="reportlab", generated_at=generated,
        ))
    return reports
