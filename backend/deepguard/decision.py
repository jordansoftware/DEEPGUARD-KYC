"""Decision engine — weighted scoring and verdict."""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.workflow import decide as _decide


def decide(
    forensic_score: float = 0,
    face_score: float = 0,
    ocr_score: float = 0,
    aml_score: float = 0,
    defects: list[str] | None = None,
) -> dict:
    """Compute a KYC verdict from signal scores.

    Args:
        forensic_score: Forensic analysis score (0-100).
        face_score: Face match score (0-100).
        ocr_score: OCR confidence score (0-100).
        aml_score: AML risk score (0-100, higher = more risk).
        defects: List of defect codes (doc_expired, face_wrong, aml_hit, etc.).

    Returns:
        dict with keys: score (int), verdict (str), verdict_label (str), reasons (list).
    """
    return _decide(
        forensic_score=forensic_score,
        face_score=face_score,
        ocr_score=ocr_score,
        aml_score=aml_score,
        defects=defects or [],
    )
