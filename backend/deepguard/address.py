"""Address verification via OCR cross-check."""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.address_verify import verify_address as _verify_address


def verify_address(
    document_path: str,
    declared_address: str,
) -> dict:
    """Verify an address against a document.

    Extracts address fields from the document via OCR and compares
    with the declared address.

    Args:
        document_path: Path to the proof-of-address document.
        declared_address: The address to verify against.

    Returns:
        dict with keys: verified (bool), confidence (float), document_address (str).
    """
    return _verify_address(document_path, declared_address)
