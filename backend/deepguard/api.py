"""DeepGuard as a FastAPI microservice.

Usage:
    uvicorn deepguard.api:app --port 8765
"""

from __future__ import annotations

import logging
import os
import sys
import tempfile

# Ensure backend app is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger("deepguard.api")

app = FastAPI(
    title="DeepGuard API",
    description="Open-source KYC with forensic image analysis",
    version="0.1.0",
)

ALLOWED_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

MAX_SIZE = 30 * 1024 * 1024
ALLOWED = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "0.1.0"}


@app.post("/api/analyze")
async def analyze(file: UploadFile = File(...)):
    """Forensic analysis of a document image."""
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED:
        raise HTTPException(400, f"Unsupported format: {ext}")

    data = await file.read()
    if len(data) > MAX_SIZE:
        raise HTTPException(413, f"File too large: {len(data)} bytes (max {MAX_SIZE})")
    if len(data) == 0:
        raise HTTPException(400, "Empty file.")

    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
        f.write(data)
        tmp = f.name

    try:
        from deepguard.core import analyze_image
        return analyze_image(tmp)
    except Exception:
        logger.exception("Image analysis failed")
        raise HTTPException(422, "Unable to analyze image.")
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass


@app.post("/api/match-faces")
async def match_faces(
    selfie: UploadFile = File(...),
    id_photo: UploadFile = File(...),
    model: str | None = None,
):
    """Compare selfie against ID photo."""
    selfie_data = await selfie.read()
    id_data = await id_photo.read()

    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        f.write(selfie_data)
        selfie_tmp = f.name
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        f.write(id_data)
        id_tmp = f.name

    try:
        from deepguard.face import match_faces
        return match_faces(selfie_tmp, id_tmp, model=model)
    except Exception:
        logger.exception("Face matching failed")
        raise HTTPException(422, "Unable to match faces.")
    finally:
        try:
            os.unlink(selfie_tmp)
            os.unlink(id_tmp)
        except OSError:
            pass


@app.post("/api/detect-liveness")
async def liveness(file: UploadFile = File(...)):
    """Liveness detection on a face image."""
    data = await file.read()
    ext = os.path.splitext(file.filename or "")[1].lower() or ".jpg"

    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
        f.write(data)
        tmp = f.name

    try:
        from deepguard.liveness import detect_liveness
        return detect_liveness(tmp)
    except Exception:
        logger.exception("Liveness detection failed")
        raise HTTPException(422, "Unable to detect liveness.")
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass


@app.post("/api/extract-text")
async def ocr(file: UploadFile = File(...)):
    """OCR text extraction from a document."""
    data = await file.read()
    ext = os.path.splitext(file.filename or "")[1].lower() or ".jpg"

    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
        f.write(data)
        tmp = f.name

    try:
        from deepguard.ocr import extract_text
        return extract_text(tmp)
    except Exception:
        logger.exception("OCR extraction failed")
        raise HTTPException(422, "Unable to extract text.")
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass
