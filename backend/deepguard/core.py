"""Core forensic image analysis."""

from __future__ import annotations

import io
import sys
import os

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.signals import analyze_image as _analyze_image, build_heatmap, _open_image
import numpy as np
from PIL import Image


def analyze_image(path: str) -> dict:
    """Analyze an image for manipulation signals.

    Args:
        path: Path to the image file (jpg, png, webp, bmp, tif).

    Returns:
        dict with keys: score, verdict, verdict_label, heatmap, image, signals, reasons.
    """
    return _analyze_image(path)


def analyze_image_from_bytes(data: bytes, filename: str = "image.jpg") -> dict:
    """Analyze image data from bytes (e.g., from an upload).

    Args:
        data: Raw image bytes.
        filename: Original filename (used for extension detection).

    Returns:
        dict with keys: score, verdict, verdict_label, heatmap, image, signals, reasons.
    """
    img = Image.open(io.BytesIO(data)).convert("RGB")
    img.thumbnail((1024, 1024), Image.LANCZOS)

    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        img.save(f, format="JPEG", quality=95)
        tmp_path = f.name

    try:
        return _analyze_image(tmp_path)
    finally:
        os.unlink(tmp_path)
