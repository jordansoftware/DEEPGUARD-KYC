"""Liveness detection for anti-spoofing."""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.liveness import detect_liveness as _detect_liveness
from app.services.video_liveness import analyze_video_liveness as _analyze_video


def detect_liveness(path: str) -> dict:
    """Analyze an image for liveness (anti-spoofing).

    Checks eye shine, skin texture, facial symmetry, and border artifacts.

    Args:
        path: Path to the face image.

    Returns:
        dict with keys: is_live (bool), score (float), checks (dict).
    """
    return _detect_liveness(path)


def analyze_video_liveness(video_path: str) -> dict:
    """Analyze a short video for liveness.

    Detects micro-movements, blink patterns, and temporal consistency.

    Args:
        video_path: Path to the video file.

    Returns:
        dict with keys: is_live (bool), score (float), details (dict).
    """
    return _analyze_video(video_path)
