"""Address verification — OCR extraction and cross-check for proof of address."""

from __future__ import annotations

import re

from PIL import Image


def _extract_address_fields(ocr_text: str) -> dict:
    """Extract address components from OCR text using keyword patterns."""
    text_upper = ocr_text.upper()
    result = {
        "name": "",
        "address": "",
        "city": "",
        "postal_code": "",
        "country": "",
        "date": "",
    }

    patterns = [
        (r"(?:NOM|NAME|TITULARIRE|ADDRESS|ADRESSE)\s*:?\s*(.+?)(?:\n|$)", "name"),
        (r"(?:ADRESSE|ADDRESS|RUE|STREET|AVENUE|BOULEVARD|ROUTE)\s*:?\s*(.+?)(?:\n|$)", "address"),
        (r"(?:VILLE|CITY|COMMUNE)\s*:?\s*(.+?)(?:\n|$)", "city"),
        (r"(?:CODE\s*(?:POSTAL|POST)?|ZIP)\s*:?\s*(\d{4,6})", "postal_code"),
        (r"(?:PAYS|COUNTRY)\s*:?\s*(.+?)(?:\n|$)", "country"),
        (r"(?:DATE|DU|DATED?)\s*:?\s*(\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4})", "date"),
    ]

    for pattern, field in patterns:
        m = re.search(pattern, text_upper)
        if m:
            result[field] = m.group(1).strip()

    return result


def _check_date_validity(date_str: str) -> bool:
    """Check if the document date is within the last 3 months."""
    if not date_str:
        return True

    from datetime import datetime, timedelta

    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%d/%m/%y", "%d-%m-%y"):
        try:
            parsed = datetime.strptime(date_str, fmt)
            three_months_ago = datetime.now() - timedelta(days=90)
            return parsed >= three_months_ago
        except ValueError:
            continue
    return True


def verify_address(ocr_text: str, declared_country: str = "") -> dict:
    """Verify proof of address document.

    Returns score 0-1 (1 = verified), extracted fields, and issues found.
    """
    fields = _extract_address_fields(ocr_text)
    issues = []
    score = 1.0

    if not fields["address"] and not fields["city"]:
        issues.append("Could not extract address from document.")
        score -= 0.4

    if not fields["name"]:
        issues.append("Could not extract name from document.")
        score -= 0.2

    if not fields["postal_code"]:
        issues.append("No postal code found.")
        score -= 0.1

    if declared_country and fields["country"]:
        if fields["country"].upper() != declared_country.upper():
            issues.append(f"Country on document ({fields['country']}) does not match declared country ({declared_country}).")
            score -= 0.3

    if not _check_date_validity(fields["date"]):
        issues.append("Document date is older than 3 months.")
        score -= 0.2

    score = max(0.0, min(1.0, score))

    return {
        "score": round(score, 3),
        "verified": score >= 0.6,
        "extracted": fields,
        "issues": issues,
    }
