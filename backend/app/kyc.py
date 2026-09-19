"""KYC cases for the fintech dashboard.

The store is seeded at first startup by running the REAL analysis chain
(signals.analyze_image) on synthetic KYC images — authentic and forged
(double-compressed zone re-inserted). The scores, heatmaps, signals and
reasons displayed in the dashboard are therefore produced by the same
pipeline as the "Image Analysis" tab: consistent behavior under real
conditions.
"""

from __future__ import annotations

import io
import os
import random
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from .signals import analyze_image

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED_DIR = os.path.join("/tmp", "deepguard_kyc")

STATUS_LABELS = {
    "pending": "Pending",
    "review": "Under Review",
    "approved": "Approved",
    "rejected": "Rejected",
}

# --- synthetic KYC image generation ----------------------------------------

def _make_portrait(seed: int, skin=(206, 158, 126), offset: int = 0) -> Image.Image:
    """ID portrait: gradient background + simple face + photo grain."""
    rng = np.random.default_rng(seed + offset)
    w, h = 320, 340
    base = np.full((h, w, 3), 250.0, dtype=np.float64)
    for y in range(h):
        t = y / h
        base[y] *= 1 - 0.14 * t
    cx, cy = w // 2, int(h * 0.44)
    yy, xx = np.mgrid[0:h, 0:w]
    face = ((xx - cx) / (w * 0.30)) ** 2 + ((yy - cy) / (h * 0.42)) ** 2 <= 1
    base[face] = np.array(skin)
    base[face] *= np.clip(1 - 0.4 * np.clip((yy[face] - cy) / (h * 0.42), 0, 1), 0, 1)[:, None]
    hair = ((xx - cx) / (w * 0.36)) ** 2 + ((yy - (cy - h * 0.12)) / (h * 0.22)) ** 2 <= 1
    hair &= yy < cy - h * 0.14
    base[hair] = np.array((52, 44, 38))
    for (ex, ey) in ((cx - w * 0.10, cy - h * 0.03), (cx + w * 0.10, cy - h * 0.03)):
        eye = (xx - ex) ** 2 + (yy - ey) ** 2 <= (w * 0.028) ** 2
        base[eye] = np.array((44, 40, 38))
    mouth = (np.abs(yy - (cy + h * 0.22)) < h * 0.018) & (np.abs(xx - cx) < w * 0.15)
    base[mouth] = np.array((150, 105, 92))
    base += rng.normal(0, 1.5, base.shape)
    return Image.fromarray(np.clip(base, 0, 255).astype("uint8")).convert("RGB")


def make_id(seed: int, country: str = "fr") -> Image.Image:
    """National ID card: institutional banner, photo, fields."""
    w, h = 1000, 640
    img = Image.new("RGB", (w, h), (228, 232, 240))
    d = ImageDraw.Draw(img)
    for i in range(170):
        v = int(40 + 130 * (i / 170))
        d.line([(0, i), (w, i)], fill=(v, 60 + i // 5, 210 - i // 5))
    for i in range(170, 190):
        d.line([(0, i), (w, i)], fill=(24, 48, 120))
    d.rectangle([0, 190, w, h], fill=(240, 246, 253))
    if country == "de":
        d.text((48, 52), "DEUTSCHES REICH", fill=(255, 255, 255))
        d.text((48, 100), "PERSOENLICHEN AUSWEISKARTE", fill=(215, 228, 255))
    else:
        d.text((48, 52), "REPUBLIQUE FRANCAISE", fill=(255, 255, 255))
        d.text((48, 100), "CARTE NATIONALE D'IDENTITE", fill=(215, 228, 255))
    photo = _make_portrait(seed, offset=5)
    img.paste(photo, (60, 215))
    d.rectangle([58, 212, 420, 604], outline=(120, 135, 165), width=2)
    if country == "de":
        rows = [
            ("NAME", "MUELLER"),
            ("VORNAMEN", "HANNAH"),
            ("GEBURTSDATUM", "12.03.1996"),
            ("GESCHLECHT", "W"),
            ("PERSONALE KZ", "2N1847288"),
        ]
    else:
        rows = [
            ("NOM", "DIALLO"),
            ("PRENOMS", "AMINATA"),
            ("NEE LE", "12/03/1996"),
            ("SEXE", "F"),
            ("N", "2N1847288"),
        ]
    y = 250
    for lab, val in rows:
        d.text((470, y), lab, fill=(120, 135, 165))
        d.text((470, y + 28), val, fill=(30, 42, 70))
        y += 78
    d.text((70, 560), "<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<", fill=(110, 125, 155))
    return img


def make_passport(seed: int, country: str = "fr") -> Image.Image:
    """Passport: blue cover + data page."""
    w, h = 900, 640
    img = Image.new("RGB", (w, h), (18, 55, 105))
    d = ImageDraw.Draw(img)
    if country == "de":
        d.text((60, 55), "DEUTSCHER PASS", fill=(220, 235, 255))
        d.text((60, 105), "REISEPASS", fill=(255, 255, 255))
        d.text((700, 165), "Type : P", fill=(190, 214, 244))
        d.text((700, 210), "Code : DEU", fill=(190, 214, 244))
    else:
        d.text((60, 55), "REPUBLIQUE FRANCAISE", fill=(220, 235, 255))
        d.text((60, 105), "PASSEPORT", fill=(255, 255, 255))
        d.text((700, 165), "Type : PA", fill=(190, 214, 244))
        d.text((700, 210), "Code : FRA", fill=(190, 214, 244))
    photo = _make_portrait(seed, offset=8)
    img.paste(photo, (60, 220))
    d.text((500, 240), "N : 70FA18472", fill=(225, 238, 254))
    d.text((500, 300), "NOM : DIALLO", fill=(225, 238, 254))
    d.text((500, 360), "PRENOMS : AMINATA", fill=(225, 238, 254))
    d.text((500, 420), "NEE LE : 12.03.1996", fill=(225, 238, 254))
    d.text((60, 578), "<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<", fill=(190, 214, 244))
    return img


def make_selfie(seed: int) -> Image.Image:
    """Webcam selfie: neutral background, centered face."""
    s = 640
    img = Image.new("RGB", (s, s), (246, 248, 252))
    d = ImageDraw.Draw(img)
    for y in range(s):
        t = y / s
        d.line([(0, y), (s, y)], fill=(int(246 - 8 * t), int(247 - 12 * t), int(250 - 4 * t)))
    photo = _make_portrait(seed, offset=12).resize((s - 220, s - 220))
    img.paste(photo, (110, 105))
    return img


def forge(img: Image.Image, box) -> Image.Image:
    """Local double-compression: zone re-encoded at low quality then smoothed,
    re-inserted into the original image — "retouching" artifact type."""
    patch = img.crop(box)
    buf = io.BytesIO()
    patch.save(buf, format="JPEG", quality=35)
    buf.seek(0)
    patch = Image.open(buf).convert("RGB").filter(ImageFilter.GaussianBlur(1.1))
    out = img.copy()
    out.paste(patch, box)
    return out


def _save_jpeg(img: Image.Image, path: str, quality: int = 92) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.convert("RGB").save(path, format="JPEG", quality=quality)


def ensure_seed_images() -> list[tuple[str, str]]:
    """(Re)generates KYC images in /tmp/deepguard_kyc.
    Returns [(path, label)] with label among real/forged."""
    os.makedirs(SEED_DIR, exist_ok=True)
    items = [
        ("id_real.jpg", make_id(1), (60, 215, 424, 606), True),
        ("id_forge.jpg", make_id(11), (60, 215, 424, 606), False),
        ("id_de_real.jpg", make_id(2, country="de"), (60, 215, 424, 606), True),
        ("id_de_forge.jpg", make_id(12, country="de"), (60, 215, 424, 606), False),
        ("passport_real.jpg", make_passport(3), (60, 220, 444, 470), True),
        ("passport_forge.jpg", make_passport(13), (60, 220, 444, 470), False),
        ("passport_de_real.jpg", make_passport(4, country="de"), (60, 220, 444, 470), True),
        ("passport_de_forge.jpg", make_passport(14, country="de"), (60, 220, 444, 470), False),
        ("selfie_real.jpg", make_selfie(5), (110, 105, 530, 535), True),
        ("selfie_forge.jpg", make_selfie(15), (110, 105, 530, 535), False),
    ]
    out = []
    for name, img, box, real in items:
        path = os.path.join(SEED_DIR, name)
        # build the image -> forged version if applicable
        final = img if real else forge(img, box)
        _save_jpeg(final, path)
        out.append((path, "real" if real else "forged"))
    return out


# --- in-memory store ---------------------------------------------------------

@dataclass
class KycCase:
    id: int
    applicant: str
    reference: str
    doc_type: str
    country: str
    filename: str
    submitted_at: str
    status: str = "pending"
    score: int = 0
    verdict: str = "authentique"
    verdict_label: str = "Authentique"
    signals: dict = field(default_factory=dict)
    reasons: list = field(default_factory=list)
    image: str = ""
    heatmap: str = ""
    history: list = field(default_factory=list)

    def to_list(self) -> dict:
        return {
            "id": self.id,
            "applicant": self.applicant,
            "reference": self.reference,
            "doc_type": self.doc_type,
            "country": self.country,
            "filename": self.filename,
            "submitted_at": self.submitted_at,
            "status": self.status,
            "score": self.score,
            "verdict": self.verdict,
            "verdict_label": self.verdict_label,
        }

    def to_detail(self) -> dict:
        d = self.to_list()
        d["signals"] = self.signals
        d["reasons"] = self.reasons
        d["image"] = self.image
        d["heatmap"] = self.heatmap
        d["history"] = self.history
        return d


_APPLICANTS = [
    ("AMINATA DIALLO", "ID-CNI-FR-2024-01142", "cni", "FR"),
    ("SEBASTIEN MARTIN", "ID-PASS-FR-2024-00871", "passeport", "FR"),
    ("FATOU N'DIAYE", "ID-CNI-FR-2024-00923", "cni", "FR"),
    ("HANNAH MUELLER", "ID-CNI-DE-2023-04412", "cni", "DE"),
    ("AICHA BOUBAKAR", "ID-SELFIE-FR-2024-01277", "selfie", "FR"),
    ("YACINE BELHADJ", "ID-PASS-DE-2024-00765", "passeport", "DE"),
    ("CHLOE DUMONT", "ID-CNI-FR-2024-01305", "cni", "FR"),
    ("MARC LE GUEN", "ID-CNI-DE-2023-03011", "cni", "DE"),
]

_COUNTRIES = {"FR": "France", "NG": "Nigeria", "SN": "Senegal", "CI": "Cote d'Ivoire", "MA": "Morocco", "DE": "Germany"}

_store: dict[int, KycCase] = {}
_next_id = 1
_lock = threading.Lock()
_ready = threading.Event()


def _seed() -> None:
    """Builds the store: half the cases are "forged" (double-compressed zone),
    the other half are authentic. Mixed starting statuses."""
    global _next_id
    images = ensure_seed_images()
    rng = random.Random(42)

    # The doc_type of each case must match a seed image: we reuse
    # images in order (cni -> id, passeport -> passport, selfie -> selfie).
    # Add _de suffix to pick the German variants.
    doc_map: dict[str, dict[str, str]] = {
        "cni": {}, "cni_de": {}, "passeport": {}, "passeport_de": {}, "selfie": {},
    }
    for path, kind in images:
        base = os.path.basename(path)
        key = base.split("_")[0]
        real_key = "cni" if key == "id" else ("passeport" if key == "passport" else "selfie")
        if "de" in base and not base.endswith("real.jpg") and not base.endswith("forge.jpg"):
            real_key = f"{real_key}_de"
        elif base.startswith("id_de"):
            real_key = "cni_de"
        elif base.startswith("passport_de"):
            real_key = "passeport_de"
        doc_map.setdefault(real_key, {}).setdefault(kind, path)

    for i, (applicant, reference, doc_type, cc) in enumerate(_APPLICANTS):
        # alternate real/forged; forged score always > 25 to stand out
        is_german = cc == "DE"
        if doc_type == "cni" and is_german:
            key = doc_map.get("cni_de", doc_map["cni"])
        elif doc_type == "passeport" and is_german:
            key = doc_map.get("passeport_de", doc_map["passeport"])
        else:
            key = doc_map.get(doc_type, doc_map["cni"])
        path = key["forged" if i % 2 == 1 else "real"]

        res = analyze_image(path)
        verdict = res["verdict_label"]

        # Mixed and realistic initial statuses: half the forged cases go to
        # "review"/"rejected", half the authentic ones to "pending"/"approved".
        # We rely on parity + a majority verdict for a stable seed.
        if verdict != "authentique":
            initial = "review" if i % 3 else "rejected"
        else:
            initial = "approved" if i % 4 in (1, 2) else "pending"

        case = KycCase(
            id=_next_id,
            applicant=applicant,
            reference=reference,
            doc_type=doc_type,
            country=_COUNTRIES.get(cc, cc),
            filename=os.path.basename(path),
            submitted_at=f"2024-06-{10 + (i % 18):02d}T09:3{i % 6}0:00Z",
            status=initial,
            score=res["score"],
            verdict=verdict,
            verdict_label=res["verdict_label"],
            signals=res["signals"],
            reasons=res["reasons"],
            image=res["image"],
            heatmap=res["heatmap"],
        )
        _store[case.id] = case
        _next_id += 1

    _ready.set()


def _stats() -> dict:
    st = {"total": 0, "pending": 0, "review": 0, "approved": 0, "rejected": 0}
    for c in _store.values():
        st["total"] += 1
        st[c.status] = st.get(c.status, 0) + 1
    return st


def get_cases(status: str | None, q: str | None, page: int, page_size: int) -> dict:
    _ready.wait(timeout=10)
    with _lock:
        items = list(_store.values())
    if status and status in STATUS_LABELS:
        items = [c for c in items if c.status == status]
    if q:
        ql = q.lower()
        items = [
            c for c in items
            if ql in c.applicant.lower() or ql in c.reference.lower()
        ]
    items.sort(key=lambda c: c.submitted_at, reverse=True)
    total = len(items)
    start = (page - 1) * page_size
    page_items = items[start:start + page_size]
    return {
        "cases": [c.to_list() for c in page_items],
        "total": total,
        "pages": max(1, -(-total // page_size)),
        "stats": _stats(),
    }


def get_case(case_id: int) -> KycCase | None:
    _ready.wait(timeout=10)
    with _lock:
        return _store.get(case_id)


def decide(case_id: int, action: str) -> KycCase | None:
    """action: approved | rejected | review -> updates the status."""
    mapping = {"approved": "approved", "rejected": "rejected", "review": "review"}
    new_status = mapping.get(action)
    if not new_status:
        return None
    with _lock:
        case = _store.get(case_id)
        if not case:
            return None
        old = case.status
        case.status = new_status
        case.history.append({
            "action": action,
            "from": old,
            "to": new_status,
        })
        return case


def create_case(image_path: str, *, applicant: str = "",
                doc_type: str = "autre", filename: str = "",
                reference: str = "") -> KycCase:
    """Submit a new ID document from an API (external client).

    Analyzes the image with the real forensic chain, creates a KYC case and
    returns it. The initial status follows the verdict: authentic -> "pending",
    suspect -> "review", forged -> "rejected".
    """
    global _next_id
    _ready.wait(timeout=10)
    res = analyze_image(image_path)
    verdict = res["verdict_label"]
    if verdict == "forge":
        initial = "rejected"
    elif verdict == "suspect":
        initial = "review"
    else:
        initial = "pending"

    applicant = (applicant or "").strip() or "External case"
    with _lock:
        cid = _next_id
        _next_id += 1
    case = KycCase(
        id=cid,
        applicant=applicant.upper(),
        reference=reference or f"KS-{cid:05d}",
        doc_type=doc_type,
        country="Unknown",
        filename=filename or os.path.basename(image_path),
        submitted_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        status=initial,
        score=res["score"],
        verdict=verdict,
        verdict_label=res["verdict_label"],
        signals=res["signals"],
        reasons=res["reasons"],
        image=res["image"],
        heatmap=res["heatmap"],
    )
    with _lock:
        _store[case.id] = case
    return case


def update_face_verification(
    case_id: int,
    face_match: bool,
    face_score: float,
    liveness_result: dict,
    capture_device: str,
) -> KycCase | None:
    """Update a KYC case with face verification results from mobile.

    Recalculates the verdict using the decision engine with face + liveness data.
    """
    case = _store.get(case_id)
    if not case:
        return None

    # Store face verification data in signals
    case.signals["face_match"] = face_match
    case.signals["face_score"] = face_score
    case.signals["liveness"] = liveness_result
    case.signals["capture_device"] = capture_device

    # Build defects list based on results
    defects = []
    if not face_match:
        defects.append("face_wrong")
    if not liveness_result.get("is_live", False):
        defects.append("liveness_failed")
    if capture_device == "web":
        defects.append("capture_not_mobile")

    # Re-run decision engine with face data
    from app.workflow import decide
    result = decide(
        forensic_score=case.score,
        face_score=face_score * 100 if face_match else 0,
        ocr_score=80,  # default — OCR not yet integrated
        aml_score=0,
        defects=defects,
    )

    # Update case
    case.score = result["score"]
    case.verdict = result["verdict"]
    case.verdict_label = result["verdict_label"]
    case.reasons = result.get("reasons", case.reasons)

    # Update status based on new verdict
    if result["verdict"] == "authentique" and result["score"] >= 88:
        case.status = "approved"
    elif result["verdict"] == "forge" or result["score"] < 55:
        case.status = "rejected"
    else:
        case.status = "review"

    return case


# The store is seeded in a background thread on first import (the AI analyses
# are fast, but we don't block server startup on them).
threading.Thread(target=_seed, name="kyc-seed", daemon=True).start()
