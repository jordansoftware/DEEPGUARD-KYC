"""Business rules and decision engine of the pipeline.

This is where raw signals (forensic, OCR, face, AML) become a compliant
decision: weighted scoring, verdict, status, audit reasons, SLA and
webhook signal. The engine has no web framework dependency — easy to test.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

SLA_HOURS = 12  # processing SLA commitment in hours

VERDICT_ORDER = ("authentique", "suspect", "forge", "inconnu")

# Weight of each signal in the overall confidence score.
WEIGHTS = {
    "forensic": 0.50,  # MELA/ELA/noise/metadata anomalies
    "ocr": 0.18,       # MRZ / document consistency
    "face": 0.22,      # selfie <-> photo
    "aml": 0.10,       # sanctions/PEP screening
}

# Defaults applied per document type.
DEFECT_WEIGHTS = {
    "doc_type_mismatch": 2,    # extracted field contradicts declared type
    "mrz_missing": 2,          # no readable MRZ zone when expected
    "mrz_inconsistent": 3,     # MRZ fields contradict each other (dates/format)
    "face_wrong": 3,           # selfie != ID photo
    "face_unavailable": 1,     # engine unavailable -> slight penalty
    "face_verification_missing": 5,  # face verification not completed
    "aml_hit": 4,              # sanctions/PEP match
    "aml_unresolved": 1,       # inconclusive screening
    "resolution_low": 1,       # image too small for reliable analysis
    "extraction_incomplete": 1,
    "signals_conflicting": 2,  # conflicting signals between engines
    "liveness_failed": 3,      # liveness check failed (spoofing detected)
    "liveness_unavailable": 1, # liveness engine unavailable
    "doc_expired": 5,          # document has expired
    "address_mismatch": 2,     # address on proof does not match declared country
    "address_unreadable": 1,   # address proof could not be read
    "capture_not_mobile": 2,   # selfie captured on web instead of mobile
}


@dataclass(frozen=True)
class Decision:
    """Stable result of the decision engine — serializable as-is."""

    score: int                      # 0..100 (100 = very trustworthy)
    verdict: str                    # authentique / suspect / forge / inconnu
    verdict_label: str
    status: str                     # pending / review / approved / rejected
    reasons: tuple[str, ...] = ()
    meta: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = {
            "score": self.score,
            "verdict": self.verdict,
            "verdict_label": self.verdict_label,
            "status": self.status,
            "reasons": list(self.reasons),
        }
        d.update(self.meta)
        return d


def _score_block(score: float | None, weight: float, is_ok: bool) -> float:
    """Confidence contributed by a signal: `weight` if OK, otherwise a minimal
    fraction so as not to completely shut down the decision."""
    if score is None:
        return weight * 0.30
    contribution = weight * max(0.0, min(1.0, score))
    if not is_ok:
        contribution *= 0.40
    return contribution


def decide(
    *,
    forensic_score: float | None,
    ocr_ok: bool,
    face: dict | None,
    aml: dict | None,
    doc_type: str,
    expected_mrz: bool = False,
    defects: dict[str, int] | None = None,
) -> Decision:
    """Computes verdict & status from analyzed signals."""
    defects = dict(defects or {})

    # reason accumulator (audit)
    reasons: list[str] = []

    face_ok = bool(face and face.get("match") is True)
    face_v = face.get("score") if face else None

    aml_ok = bool(aml and aml.get("hit") is False and not aml.get("unresolved"))
    aml_hit = bool(aml and aml.get("hit") is True)
    aml_v = aml.get("score") if aml else None

    conf = (
        _score_block(forensic_score, WEIGHTS["forensic"], forensic_score is not None)
        + _score_block(face_v, WEIGHTS["face"], face_ok)
        + _score_block(aml_v, WEIGHTS["aml"], aml_ok)
        + (WEIGHTS["ocr"] if ocr_ok else WEIGHTS["ocr"] * 0.30)
    )
    score = int(round(conf * 100))

    # negative defects applied when the signal is bad
    penalty = 0
    for defect, weight in DEFECT_WEIGHTS.items():
        used = defects.get(defect)
        if used:
            penalty += weight * used
            if defect == "face_wrong":
                reasons.append("Selfie does not match the ID photo.")
            elif defect == "aml_hit":
                reasons.append("Sanctions/AML match detected.")
            elif defect == "mrz_inconsistent":
                reasons.append("Inconsistent MRZ zone (unreadable/incompatible reader).")
            elif defect == "mrz_missing":
                reasons.append("No readable MRZ zone found.")
            elif defect == "liveness_failed":
                reasons.append("Liveness check failed — possible spoofing or replay.")
            elif defect == "doc_expired":
                reasons.append("Document has expired and is no longer valid.")
            elif defect == "address_mismatch":
                reasons.append("Address on proof of address does not match declared country.")
            elif defect == "address_unreadable":
                reasons.append("Proof of address could not be read or parsed.")
    score = int(max(0, score - penalty))

    # verdict
    if aml_hit:
        verdict, label = "forge", "Forged"          # immediate AML block
    elif score < 15:
        verdict, label = "inconnu", "Unknown"
    elif score > 88:
        verdict, label = "authentique", "Authentique"
    elif score > 55:
        verdict, label = "suspect", "Suspect"
        if not reasons:
            reasons.append("Average confidence score — manual review recommended.")
    else:
        verdict, label = "forge", "Forged"

    # business status
    if verdict == "authentique":
        status = "approved"
    elif verdict in ("forge",):
        status = "rejected"
    else:
        status = "review"

    return Decision(
        score=score,
        verdict=verdict,
        verdict_label=label,
        status=status,
        reasons=tuple(reasons),
        meta={
            "sla_hours": SLA_HOURS,
            "sla_deadline": (
                dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=SLA_HOURS)
            ).isoformat(),
            "weights": WEIGHTS,
        },
    )
