"""Batch upload processing for multiple KYC documents."""

from __future__ import annotations

import logging
import os
import stat
import tempfile
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.models import BatchJob, Client
from app import kyc
from app.security import current_client

logger = logging.getLogger("deepguard.batch")

router = APIRouter(prefix="/api/batch", tags=["batch"])
settings = get_settings()

ALLOWED = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}
MAX_SIZE = 30 * 1024 * 1024


@router.post("/upload")
async def batch_upload(
    files: list[UploadFile] = File(...),
    applicant: str = Form(""),
    doc_type: str = Form("autre"),
    reference: str = Form(""),
    db: Session = Depends(get_db),
    client: Client = Depends(current_client),
):
    """Upload multiple documents for batch processing."""
    if len(files) > settings.batch_max_files:
        raise HTTPException(status_code=400, detail=f"Too many files. Max: {settings.batch_max_files}")

    batch = BatchJob(
        status="processing",
        total_files=len(files),
        client_id=client.id,
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)

    case_ids = []
    processed = 0
    failed = 0

    for file in files:
        suffix = Path(file.filename or "image.png").suffix.lower()
        if suffix not in ALLOWED:
            failed += 1
            continue

        data = await file.read()
        if len(data) > MAX_SIZE or len(data) == 0:
            failed += 1
            continue

        tmp = Path(tempfile.gettempdir()) / "deepguard" / f"{uuid.uuid4().hex}{suffix}"
        tmp.parent.mkdir(parents=True, exist_ok=True)
        try:
            tmp.write_bytes(data)
            os.chmod(tmp, stat.S_IRUSR | stat.S_IWUSR)
            case = kyc.create_case(
                str(tmp),
                applicant=applicant,
                doc_type=doc_type.strip().lower() or "autre",
                reference=reference.strip() or f"BATCH-{batch.id}-{len(case_ids)+1}",
                filename=file.filename,
            )
            case_ids.append(case.id)
            processed += 1
        except Exception:
            logger.exception("Batch file processing failed")
            failed += 1
        finally:
            try:
                tmp.unlink()
            except OSError:
                pass

    batch.status = "completed"
    batch.processed = processed
    batch.failed = failed
    batch.case_ids = case_ids
    db.commit()

    return batch.to_dict()


@router.get("/{batch_id}")
def get_batch(
    batch_id: int,
    db: Session = Depends(get_db),
    client: Client = Depends(current_client),
):
    """Get batch job status."""
    batch = db.query(BatchJob).filter(BatchJob.id == batch_id, BatchJob.client_id == client.id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch job not found.")
    return batch.to_dict()


@router.get("/")
def list_batches(
    page: int = Query(ge=1, default=1),
    page_size: int = Query(ge=1, le=100, default=20),
    db: Session = Depends(get_db),
    client: Client = Depends(current_client),
):
    """List all batch jobs."""
    query = db.query(BatchJob).filter(BatchJob.client_id == client.id).order_by(BatchJob.id.desc())
    total = query.count()
    batches = query.offset((page - 1) * page_size).limit(page_size).all()
    return {
        "batches": [b.to_dict() for b in batches],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
