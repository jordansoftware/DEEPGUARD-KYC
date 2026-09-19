"""OCR and MRZ extraction from identity documents."""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.ocr import extract_text as _extract_text, parse_mrz


def extract_text(path: str) -> dict:
    """Extract text from an identity document image.

    Args:
        path: Path to the document image.

    Returns:
        dict with keys: raw_text (str), fields (dict), mrz (dict|None).
    """
    return _extract_text(path)


def extract_mrz(path: str) -> dict | None:
    """Extract and parse MRZ (Machine Readable Zone) from a document.

    Args:
        path: Path to the document image.

    Returns:
        dict with MRZ fields (document_number, nationality, birth_date, etc.) or None.
    """
    result = _extract_text(path)
    return result.get("mrz")
