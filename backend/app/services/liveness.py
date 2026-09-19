"""Liveness detection — anti-spoofing for selfie uploads.

Heuristic-based approach: analyzes eye shine, skin texture uniformity,
and facial symmetry to detect printed photos, screen replays, and masks.
No pre-trained model required — works with Pillow + numpy only.
"""

from __future__ import annotations

import io
import math

import numpy as np
from PIL import Image, ImageFilter


def _np(img: Image.Image) -> np.ndarray:
    return np.asarray(img, dtype=np.float64)


def _detect_eye_shine(img: Image.Image) -> dict:
    """Detect specular reflections in eye region — real eyes reflect light."""
    arr = _np(img)
    gray = np.mean(arr, axis=2)

    h, w = gray.shape
    mid_h, mid_w = h // 2, w // 2

    eye_region = gray[mid_h - h // 6:mid_h + h // 6, mid_w - w // 3:mid_w + w // 3]
    if eye_region.size == 0:
        return {"score": 0.5, "note": "Eye region too small for analysis."}

    bright_threshold = np.percentile(eye_region, 95)
    bright_pixels = np.mean(eye_region > bright_threshold)
    shine_detected = bright_pixels > 0.005 and bright_pixels < 0.08

    if shine_detected:
        return {"score": 0.9, "note": "Natural eye reflections detected (live person)."}
    elif bright_pixels >= 0.08:
        return {"score": 0.3, "note": "Unusual brightness pattern in eye region (possible screen)."}
    else:
        return {"score": 0.5, "note": "No clear eye reflections found."}


def _detect_skin_texture(img: Image.Image) -> dict:
    """Analyze skin texture uniformity — real skin has natural variation."""
    arr = _np(img).astype(np.float64)
    blurred = np.asarray(img.filter(ImageFilter.GaussianBlur(5))).astype(np.float64)
    residual = arr - blurred
    lum = np.mean(residual, axis=2)

    h, w = lum.shape
    skin_region = lum[h // 4:3 * h // 4, w // 4:3 * w // 4]
    if skin_region.size < 100:
        return {"score": 0.5, "note": "Insufficient skin region for texture analysis."}

    variance = float(np.var(skin_region))
    if variance < 5.0:
        return {"score": 0.2, "note": "Very smooth texture — possible printed photo or mask."}
    elif variance > 500.0:
        return {"score": 0.4, "note": "Highly noisy texture — possible composite image."}
    else:
        score = min(1.0, variance / 200.0)
        return {"score": max(0.5, score), "note": "Natural skin texture variation detected."}


def _detect_facial_symmetry(img: Image.Image) -> dict:
    """Check facial symmetry — extreme asymmetry suggests manipulation."""
    arr = _np(img)
    gray = np.mean(arr, axis=2)

    h, w = gray.shape
    face = gray[h // 4:3 * h // 4, w // 4:3 * w // 4]
    if face.size < 100:
        return {"score": 0.5, "note": "Insufficient face region for symmetry analysis."}

    left = face[:, :face.shape[1] // 2]
    right = face[:, face.shape[1] // 2:]
    min_w = min(left.shape[1], right.shape[1])
    left = left[:, :min_w]
    right = right[:, :min_w]
    right_flipped = right[:, ::-1]

    diff = np.mean(np.abs(left - right_flipped))
    if diff < 5.0:
        return {"score": 0.95, "note": "High facial symmetry (natural face)."}
    elif diff < 15.0:
        return {"score": 0.7, "note": "Moderate facial asymmetry (within normal range)."}
    else:
        return {"score": 0.3, "note": f"High facial asymmetry (diff={diff:.1f}) — possible manipulation."}


def _detect_border_artifacts(img: Image.Image) -> dict:
    """Detect sharp borders that suggest pasted/masked content."""
    arr = _np(img).astype(np.float64)
    gray = np.mean(arr, axis=2)

    sobel_x = np.abs(np.diff(gray, axis=1))
    sobel_y = np.abs(np.diff(gray, axis=0))

    edge_x = float(np.mean(sobel_x > 50))
    edge_y = float(np.mean(sobel_y > 50))
    edge_density = (edge_x + edge_y) / 2

    if edge_density > 0.15:
        return {"score": 0.25, "note": "High edge density — possible cutout or composite."}
    elif edge_density < 0.02:
        return {"score": 0.4, "note": "Very few edges — possible smoothed/manipulated image."}
    else:
        return {"score": 0.8, "note": "Natural edge distribution detected."}


def check_liveness(path: str) -> dict:
    """Full liveness check pipeline. Returns score 0-1 (1 = likely live)."""
    img = Image.open(path).convert("RGB")
    img.thumbnail((1024, 1024), Image.LANCZOS)

    eye = _detect_eye_shine(img)
    texture = _detect_skin_texture(img)
    symmetry = _detect_facial_symmetry(img)
    borders = _detect_border_artifacts(img)

    weights = {"eye": 0.30, "texture": 0.25, "symmetry": 0.25, "borders": 0.20}
    score = (
        weights["eye"] * eye["score"]
        + weights["texture"] * texture["score"]
        + weights["symmetry"] * symmetry["score"]
        + weights["borders"] * borders["score"]
    )
    score = max(0.0, min(1.0, score))

    passed = score >= 0.55
    notes = [eye["note"], texture["note"], symmetry["note"], borders["note"]]

    return {
        "score": round(score, 3),
        "passed": passed,
        "signals": {
            "eye_shine": {"score": round(eye["score"], 3), "note": eye["note"]},
            "skin_texture": {"score": round(texture["score"], 3), "note": texture["note"]},
            "symmetry": {"score": round(symmetry["score"], 3), "note": symmetry["note"]},
            "borders": {"score": round(borders["score"], 3), "note": borders["note"]},
        },
        "reasons": notes if not passed else [],
        "verdict": "live" if passed else "spoof",
    }
