"""Face matching between selfie and ID photo."""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.facematch import match_faces as _match_faces


def match_faces(
    selfie_path: str,
    id_photo_path: str,
    model: str | None = None,
    threshold: float | None = None,
) -> dict:
    """Compare a selfie against an ID photo.

    Args:
        selfie_path: Path to the selfie image.
        id_photo_path: Path to the ID document photo.
        model: Face recognition model (VGG-Face, Facenet, OpenFace, ArcFace, SFace, GhostFaceNet).
        threshold: Match threshold (model-specific default if None).

    Returns:
        dict with keys: match (bool), distance (float), model (str), threshold (float).
    """
    return _match_faces(selfie_path, id_photo_path, model=model, threshold=threshold)
