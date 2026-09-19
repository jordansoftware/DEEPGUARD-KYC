"""OCR & identity data extraction (DocTR).

DocTR is loaded lazily: if the library is not installed, the module
falls back to a degraded mode (heuristic MRZ extraction + no OCR) so that
the platform remains usable in demo.
"""

from __future__ import annotations

import re
from functools import lru_cache

_ocr_model = None
_doctr_ok: bool | None = None


def _load_doctr():
    """Load the DocTR predictor once."""
    global _ocr_model, _doctr_ok
    if _doctr_ok is not None:
        return _ocr_model
    try:
        from doctr.io import DocumentFile
        from doctr.models import ocr_predictor

        _ocr_model = ocr_predictor(pretrained=True)
        _doctr_ok = True
    except Exception:  # noqa: BLE001
        _ocr_model = None
        _doctr_ok = False
    return _ocr_model


def doctr_available() -> bool:
    _load_doctr()
    return bool(_doctr_ok)


def run_ocr(image_path: str) -> dict:
    """Returns {"text": str, "lines": [str], "engine": str}."""
    model = _load_doctr()
    if model is None:
        return {"text": "", "lines": [], "engine": "unavailable"}
    try:
        from doctr.io import DocumentFile

        doc = DocumentFile.from_images(image_path)
        result = model(doc)
        lines: list[str] = []
        for page in result.pages:
            for block in page.blocks:
                for line in block.lines:
                    words = [w.value for w in line.words]
                    if words:
                        lines.append(" ".join(words))
        return {"text": "\n".join(lines), "lines": lines, "engine": "doctr"}
    except Exception as exc:  # noqa: BLE001
        return {"text": "", "lines": [], "engine": f"error: {exc}"}


# --- MRZ (Machine Readable Zone) -------------------------------------------
# TD1 (ID cards, 3x30) or TD3 (passport, 2x44).

_MRZ_CHARS = re.compile(r"[A-Z0-9<]{28,}")


def _clean_mrz(raw: str) -> str:
    return raw.replace(" ", "").upper()


def parse_mrz(text: str) -> dict:
    """Detects and parses an MRZ zone. Returns extracted fields (best effort)."""
    candidates = [
        _clean_mrz(line)
        for line in text.splitlines()
        if len(_MRZ_CHARS.findall(_clean_mrz(line))) and _clean_mrz(line).count("<") >= 2
    ]
    fields: dict = {}
    if not candidates:
        return fields

    # Passport (TD3): 2 lines of 44
    td3 = [c for c in candidates if len(c) >= 40]
    if len(td3) >= 2:
        l1, l2 = td3[-2], td3[-1]
        fields["mrz_type"] = "TD3"
        try:
            names = l1[5:44].split("<<", 1)
            fields["last_name"] = names[0].replace("<", " ").strip().title()
            if len(names) > 1:
                fields["first_name"] = names[1].replace("<", " ").strip().title()
        except Exception:  # noqa: BLE001
            pass
        fields["document_number"] = l2[0:9].replace("<", "").strip()
        fields["nationality"] = l2[10:13].replace("<", "").strip()
        fields["birth_date"] = _mrz_date(l2[13:19])
        fields["sex"] = l2[20:21].replace("<", "").strip()
        fields["expiry_date"] = _mrz_date(l2[21:27])
        return {k: v for k, v in fields.items() if v}

    # ID card (TD1): 3 lines of 30
    td1 = [c for c in candidates if 25 <= len(c) < 40]
    if len(td1) >= 3:
        a, b, c = td1[-3], td1[-2], td1[-1]
        fields["mrz_type"] = "TD1"
        fields["document_number"] = a[5:14].replace("<", "").strip()
        fields["birth_date"] = _mrz_date(b[0:6])
        fields["sex"] = b[7:8].replace("<", "").strip()
        fields["expiry_date"] = b[8:14] and _mrz_date(b[8:14])
        fields["nationality"] = c[15:18].replace("<", "").strip()
        try:
            names = c[0:30].split("<<", 1)
            fields["last_name"] = names[0].replace("<", " ").strip().title()
            if len(names) > 1:
                fields["first_name"] = names[1].replace("<", " ").strip().title()
        except Exception:  # noqa: BLE001
            pass
        return {k: v for k, v in fields.items() if v}

    return fields


def _mrz_date(raw: str) -> str:
    """YYMMDD -> ISO (approximate: 2 digits -> 19xx/20xx based on likelihood)."""
    digits = re.sub(r"[^0-9]", "", raw)
    if len(digits) != 6:
        return ""
    yy, mm, dd = digits[0:2], digits[2:4], digits[4:6]
    year = int(yy)
    full = 2000 + year if year <= 40 else 1900 + year
    return f"{full:04d}-{mm}-{dd}"


def extract_fields(image_path: str) -> dict:
    """Full pipeline: OCR + MRZ parsing -> structured fields."""
    ocr = run_ocr(image_path)
    extracted = parse_mrz(ocr["text"]) if ocr["text"] else {}

    # complement: keyword detection without MRZ
    if not extracted and ocr["text"]:
        extracted = _guess_fields(ocr["text"])

    return {
        "engine": ocr["engine"],
        "text": ocr["text"],
        "fields": extracted,
        "mrz_found": bool(extracted.get("mrz_type")),
    }


def _guess_fields(text: str) -> dict:
    fields: dict = {}
    upper = text.upper()
    m = re.search(r"(?:NOM|SURNAME|NAME)\s*:?\s*([A-ZÀ-Ÿ' -]{2,40})", upper)
    if m:
        fields["last_name"] = m.group(1).strip().title()
    m = re.search(r"(?:PR[ÉE]NOM|GIVEN)[S]?\s*:?\s*([A-ZÀ-Ÿ' -]{2,40})", upper)
    if m:
        fields["first_name"] = m.group(1).strip().title()
    m = re.search(r"\b(\d{2}[./-]\d{2}[./-]\d{4})\b", text)
    if m:
        fields["birth_date"] = m.group(1).replace("/", "-").replace(".", "-")
    m = re.search(r"(?:N[°O]|NO\.?|NUMBER)\s*:?\s*([A-Z0-9]{5,15})", upper)
    if m:
        fields["document_number"] = m.group(1)
    return fields
