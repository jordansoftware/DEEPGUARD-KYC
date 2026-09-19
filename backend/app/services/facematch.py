"""Selfie <-> ID photo matching (DeepFace).

Lazy and fault-tolerant engine: when DeepFace/torch is unavailable (or the
weights cannot be built), each call returns an "unavailable" verdict
without ever crashing the workflow.
"""

from __future__ import annotations

import os
from functools import lru_cache

PREFERRED_MODELS = ("VGG-Face", "Facenet", "OpenFace", "ArcFace", "SFace", "GhostFaceNet")

_THRESHOLDS = {
    "VGG-Face": 0.40,
    "Facenet": 0.40,
    "OpenFace": 0.10,
    "ArcFace": 0.68,
    "SFace": 0.593,
    "GhostFaceNet": 0.42,
}

_engine: str | None = None


def _home() -> str:
    return os.getenv("DEEP_GUARD_HOME") or os.path.expanduser("~")


@lru_cache(maxsize=1)
def is_available() -> bool:
    """Imports DeepFace and attempts to build the first usable model."""
    global _engine
    if _engine:
        return True
    try:
        import torch  # noqa: F401
        from deepface import DeepFace

        for name in PREFERRED_MODELS:
            try:
                DeepFace.build_model(name)
                _engine = name
                return True
            except Exception:  # noqa: BLE001
                continue
    except Exception:  # noqa: BLE001
        pass
    return False


def compare_faces(selfie_path: str, doc_path: str) -> dict:
    """Facial comparison -> `score` 0..1 (1 = same person)."""
    engine = _engine or "VGG-Face"
    threshold = _THRESHOLDS.get(engine, 0.40)
    if not is_available():
        return {
            "engine": engine,
            "available": False,
            "score": None,
            "distance": None,
            "threshold": None,
            "match": None,
            "message": "Face matching engine unavailable — selfie not analyzed.",
        }
    try:
        from deepface import DeepFace

        result = DeepFace.verify(
            img1_path=selfie_path,
            img2_path=doc_path,
            model_name=engine,
            threshold=threshold,
            enforce_detection=False,
            detector_backend="opencv",
            distance_metric="cosine",
            silent=True,
        )
    except Exception as exc:  # noqa: BLE001
        return {
            "engine": engine,
            "available": True,
            "score": None,
            "distance": None,
            "threshold": threshold,
            "match": None,
            "message": f"Facial analysis failed ({exc}).",
        }
    verified = bool(result.get("verified", False))
    distance = float(result.get("distance", 1.0))
    score = float(
        max(0.0, min(1.0, 1.0 - max(0.0, distance - threshold) / (1.0 - threshold)))
    )
    return {
        "engine": engine,
        "available": True,
        "score": round(score, 4),
        "distance": round(distance, 4),
        "threshold": threshold,
        "match": verified,
        "message": "Faces similar (same person)." if verified
        else "Faces different (attention).",
    }
