"""DeepGuard - image manipulation signal analysis.

Implemented signals (lightweight, no pre-trained model):
- MELA: Multi-patch Error Level Analysis (grid) - local recompression artifacts
- Noise: residual noise variance (PRNU approx.)
- ELA: Error Level Analysis pixel
- EXIF: metadata / inconsistencies
"""

from __future__ import annotations

import io
import math

import numpy as np
from PIL import Image, ImageFilter, ImageChops

MAX_DIM = 1024
GRID = 8

JPEG_QUALITY = 85


def _open_image(path: str) -> Image.Image:
    img = Image.open(path).convert("RGB")
    img.thumbnail((MAX_DIM, MAX_DIM), Image.LANCZOS)
    return img


def _np(img: Image.Image) -> np.ndarray:
    return np.asarray(img, dtype=np.uint8)


def _jpeg_mse(img: Image.Image, quality: int = JPEG_QUALITY) -> float:
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality, optimize=True)
    buf.seek(0)
    reencoded = Image.open(buf).convert("RGB")
    a = _np(img).astype(np.float64)
    b = _np(reencoded).astype(np.float64)
    return float(np.mean((a - b) ** 2))


def _jpeg_mse(img: Image.Image, quality: int = JPEG_QUALITY) -> float:
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality, optimize=True)
    buf.seek(0)
    reencoded = Image.open(buf).convert("RGB")
    a = _np(img).astype(np.float64)
    b = _np(reencoded).astype(np.float64)
    return float(np.mean((a - b) ** 2))


def _local_degrid_img(img: Image.Image) -> np.ndarray:
    """MELA core: grid of local recompression 'benefit'.

    For each cell we measure the additional error induced by aggressive
    recompression (Q70) compared to mild recompression (Q92):
        benefit = error(Q70) - error(Q92)
    A zone already heavily quantized (re-inserted / double-compressed) loses
    almost no more information -> abnormally low benefit.
    """
    w, h = img.size
    cw, ch = w // GRID, h // GRID
    grid = np.zeros((GRID, GRID), dtype=np.float64)
    for i in range(GRID):
        for j in range(GRID):
            box = (
                j * cw,
                i * ch,
                min(w, (j + 1) * cw),
                min(h, (i + 1) * ch),
            )
            patch = img.crop(box)
            err_hi = _jpeg_mse(patch, 92)
            err_lo = _jpeg_mse(patch, 70)
            grid[i, j] = err_lo - err_hi
    return grid


def mela_analysis(img: Image.Image) -> dict:
    """MELA grid: zones that are 'already compressed' (insertion) stand out with
    an abnormally low recompression benefit."""
    grid = _local_degrid_img(img)
    med = float(np.median(grid))
    mad = float(np.median(np.abs(grid - med)))
    if mad < 1e-3 or med < 1e-3:
        return {"score": 0.0, "map": np.zeros_like(grid), "note": "Grid too homogeneous."}

    z = (med - grid) / (mad * 1.4826 + 1e-9)  # robust, >0 => abnormally low
    z = np.clip(z, 0, None)
    hot_full = z > 1.5
    anomaly = np.clip(z / 3.0, 0, 1)
    hot = float(np.mean(hot_full))
    concentration = float(np.max(anomaly))
    score = float(np.clip(0.6 * hot + 0.4 * concentration, 0, 1))

    note = (
        f"{int(round(hot * 100))}% of the surface shows abnormal "
        "compression benefit (content likely re-inserted)."
        if hot_full.any()
        else "Homogeneous compression benefits."
    )
    return {"score": score, "map": anomaly, "note": note}


def noise_analysis(img: Image.Image) -> dict:
    """Residual noise variance: retouched zones (smoothed/denoised) show
    abnormally low noise; noisy zones (cropped) show abnormally high noise."""
    arr = _np(img).astype(np.float64)
    blurred = np.asarray(img.filter(ImageFilter.GaussianBlur(3))).astype(np.float64)
    residual = arr - blurred  # high-frequency noise
    lum = np.mean(residual, axis=2)

    h, w = lum.shape
    cw, ch = w // GRID, h // GRID
    variance_map = np.zeros((GRID, GRID))
    for i in range(GRID):
        for j in range(GRID):
            cell = lum[i * ch:(i + 1) * ch, j * cw:(j + 1) * cw]
            if cell.size < 16:
                variance_map[i, j] = 0.0
            else:
                variance_map[i, j] = float(np.var(cell))

    med = float(np.median(variance_map))
    if med < 1e-3:
        # very smooth image: cannot discriminate -> neutral signal
        return {
            "score": 0.0,
            "map": np.zeros((GRID, GRID)),
            "note": "Smooth image, residual noise non-discriminative.",
        }

    # abnormally smoothed (denoise/inpaint) OR abnormally noisy (splice)
    low_z = np.clip((med - variance_map) / (0.45 * med) , 0, None)
    high_z = np.clip((variance_map - med * 2.5) / (0.5 * med), 0, None)
    anomaly = np.clip(np.maximum(low_z * 0.8, high_z), 0, 1)

    hot = float(np.mean(anomaly > 0.5))
    score = float(np.clip(hot, 0, 1))

    note = (
        f"Noise heterogeneity across {int(round(hot * 100))}% of the surface "
        "(retouching/smoothing or inserted element)."
        if hot > 0.08
        else "Homogeneous residual noise."
    )
    return {"score": score, "map": anomaly, "note": note}


def ela_analysis(img: Image.Image) -> dict:
    """Chroma ELA: modified zones diverge on recompression."""
    quality = 95
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality, optimize=True)
    buf.seek(0)
    diff = ImageChops.difference(img, Image.open(buf).convert("RGB"))
    diff = diff.convert("L")
    arr = np.asarray(diff, dtype=np.float64)
    thresh = float(np.percentile(arr, 92))
    hot = float(np.mean(arr > thresh))
    score = float(np.clip(hot * 2.0, 0, 1))
    note = (
        f"Localized compression divergences across {int(round(hot * 100))}% of the surface."
        if hot > 0.05
        else "No significant ELA divergence."
    )
    return {"score": score, "note": note}


def meta_analysis(path: str) -> dict:
    """EXIF metadata analysis - weak but useful indicator."""
    from PIL import ExifTags

    notes: list[str] = []
    score = 0.0
    try:
        img = Image.open(path)
        exif = img.getexif()
        if not exif:
                notes.append("No EXIF metadata (possible metadata removal).")
                score += 0.2
        else:
            software_tag = None
            model_tag = None
            for k, v in exif.items():
                name = ExifTags.TAGS.get(k, "")
                if name == "Software":
                    software_tag = v
                if name == "Model" or name == "Make":
                    model_tag = v
            if software_tag:
                s = str(software_tag)
                if any(x in s.lower() for x in ("photoshop", "gimp", "stablediffusion", "dalle", "midjourney", "firefly")):
                    notes.append(f"Editing (or generator) software detected: {s}.")
                    score += 0.6
                else:
                    notes.append(f"Capture software: {s}.")
                    score += 0.1
            elif model_tag:
                notes.append(f"Capture device: {model_tag}.")
                score += 0.15
            return {"score": min(score, 1.0), "notes": notes}
    except Exception:
        notes.append("Unreadable metadata.")
        score += 0.2
    return {"score": min(score, 1.0), "notes": notes}


def build_heatmap(img: Image.Image, mela_map: np.ndarray, noise_map: np.ndarray) -> str:
    """Merges the maps into a colormap heatmap, returns a PNG dataURL."""
    combined = np.clip(0.65 * mela_map + 0.35 * noise_map, 0, 1)
    w, h = img.size
    heat = Image.fromarray(np.uint8(combined * 255), "L").resize((w, h), Image.BICUBIC)
    heat = np.asarray(heat, dtype=np.float64) / 255.0

    def colormap(t):
        t = np.clip(t, 0, 1)
        # blue -> cyan -> green -> yellow -> red
        r = np.clip(1.5 * t - 0.5, 0, 1)
        g = np.clip(1.0 - np.abs(2.0 * t - 1.0), 0, 1)
        b = np.clip(1.5 * (1 - t) - 0.0, 0, 1)
        b = np.clip(1.0 - 1.5 * t, 0, 1)
        return np.stack([r, g, b], axis=-1)

    rgb = colormap(heat)
    base = np.asarray(img, dtype=np.float64) / 255.0
    alpha = np.clip(heat * 1.4, 0, 1)
    alpha = np.expand_dims(alpha, axis=-1)
    blended = base * (1 - alpha * 0.7) + rgb * (alpha * 0.9)
    out = Image.fromarray(np.uint8(np.clip(blended, 0, 1) * 255))

    buf = io.BytesIO()
    out.save(buf, format="PNG")
    import base64
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def analyze_image(path: str) -> dict:
    """Full pipeline -> result dictionary."""
    img = _open_image(path)

    m = mela_analysis(img)
    n = noise_analysis(img)
    e = ela_analysis(img)
    meta = meta_analysis(path)

    weights = {"mela": 0.45, "noise": 0.3, "ela": 0.15, "meta": 0.10}
    score = (
        weights["mela"] * m["score"]
        + weights["noise"] * n["score"]
        + weights["ela"] * e["score"]
        + weights["meta"] * meta["score"]
    )
    score = float(np.clip(score, 0, 1))
    score100 = int(round(score * 100))

    if score < 0.25:
        verdict = "authentique"
    elif score < 0.5:
        verdict = "suspect"
    else:
        verdict = "forge"

    verdict_label = {
        "authentique": "Authentique",
        "suspect": "Suspect",
        "forge": "Forged",
    }[verdict]

    reasons = []
    if m["score"] > 0.25:
        reasons.append(m["note"])
    if n["score"] > 0.25:
        reasons.append(n["note"])
    if e["score"] > 0.25:
        reasons.append(e["note"])
    reasons.extend(meta["notes"])

    heatmap = build_heatmap(img, m["map"], n["map"])

    thumb = img.copy()
    thumb.thumbnail((400, 400))
    buf = io.BytesIO()
    thumb.save(buf, format="PNG")
    import base64
    thumb_url = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

    return {
        "score": score100,
        "verdict": verdict,
        "verdict_label": verdict_label,
        "heatmap": heatmap,
        "image": thumb_url,
        "signals": {
            "mela": {"score": int(round(m["score"] * 100)), "note": m["note"]},
            "noise": {"score": int(round(n["score"] * 100)), "note": n["note"]},
            "ela": {"score": int(round(e["score"] * 100)), "note": e["note"]},
            "meta": {"score": int(round(meta["score"] * 100)), "notes": meta["notes"]},
        },
        "reasons": reasons,
    }
