"""Video liveness detection — analyze short video clips for anti-spoofing."""

from __future__ import annotations

import io
import math

import numpy as np
from PIL import Image


def _extract_frames(video_path: str, max_frames: int = 10) -> list[Image.Image]:
    """Extract frames from video using OpenCV or fallback to image list."""
    try:
        import cv2
        cap = cv2.VideoCapture(video_path)
        frames = []
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        step = max(1, total // max_frames)
        for i in range(0, total, step):
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()
            if ret:
                img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                img.thumbnail((512, 512), Image.LANCZOS)
                frames.append(img)
            if len(frames) >= max_frames:
                break
        cap.release()
        return frames
    except ImportError:
        return []


def _analyze_micro_movements(frames: list[Image.Image]) -> dict:
    """Detect natural micro-movements between frames."""
    if len(frames) < 3:
        return {"score": 0.5, "note": "Insufficient frames for movement analysis."}

    diffs = []
    for i in range(1, len(frames)):
        arr1 = np.asarray(frames[i - 1], dtype=np.float64)
        arr2 = np.asarray(frames[i], dtype=np.float64)
        if arr1.shape != arr2.shape:
            arr2 = np.array(Image.fromarray(arr2.astype(np.uint8)).resize(
                (arr1.shape[1], arr1.shape[0])
            ), dtype=np.float64)
        diff = float(np.mean(np.abs(arr1 - arr2)))
        diffs.append(diff)

    avg_diff = np.mean(diffs)
    std_diff = np.std(diffs)

    if avg_diff < 0.5:
        return {"score": 0.2, "note": "No movement detected — possible static image replay."}
    elif avg_diff > 30.0:
        return {"score": 0.3, "note": "Excessive movement — unstable capture."}
    elif std_diff < 1.0:
        return {"score": 0.4, "note": "Uniform movement pattern — possible looped video."}
    else:
        score = min(1.0, avg_diff / 15.0)
        return {"score": max(0.6, score), "note": f"Natural micro-movements detected (avg={avg_diff:.1f}, std={std_diff:.1f})."}


def _analyze_blink_pattern(frames: list[Image.Image]) -> dict:
    """Detect natural blink patterns over time."""
    if len(frames) < 5:
        return {"score": 0.5, "note": "Insufficient frames for blink analysis."}

    eye_brightness = []
    for frame in frames:
        arr = np.asarray(frame, dtype=np.float64)
        gray = np.mean(arr, axis=2)
        h, w = gray.shape
        eye_region = gray[h // 3:h // 2, w // 4:3 * w // 4]
        if eye_region.size > 0:
            eye_brightness.append(float(np.mean(eye_region)))

    if len(eye_brightness) < 3:
        return {"score": 0.5, "note": "Could not track eye region."}

    brightness_std = float(np.std(eye_brightness))
    brightness_range = float(np.max(eye_brightness) - np.min(eye_brightness))

    if brightness_std < 0.5:
        return {"score": 0.3, "note": "No blink pattern detected — possible static image."}
    elif brightness_range > 20.0:
        return {"score": 0.8, "note": "Natural blink pattern detected."}
    else:
        return {"score": 0.6, "note": f"Mild eye movement detected (range={brightness_range:.1f})."}


def _analyze_temporal_consistency(frames: list[Image.Image]) -> dict:
    """Check that frames form a consistent temporal sequence."""
    if len(frames) < 3:
        return {"score": 0.5, "note": "Insufficient frames."}

    color_means = []
    for frame in frames:
        arr = np.asarray(frame, dtype=np.float64)
        color_means.append(np.mean(arr, axis=(0, 1)))

    diffs = [np.mean(np.abs(color_means[i] - color_means[i - 1])) for i in range(1, len(color_means))]
    avg_diff = np.mean(diffs)

    if avg_diff < 0.3:
        return {"score": 0.3, "note": "Very low temporal variation — possible single frame repeated."}
    elif avg_diff > 50.0:
        return {"score": 0.3, "note": "High temporal inconsistency — possible spliced frames."}
    else:
        return {"score": 0.8, "note": "Temporally consistent video sequence."}


def check_video_liveness(video_path: str) -> dict:
    """Full video liveness pipeline. Returns score 0-1 (1 = likely live video)."""
    frames = _extract_frames(video_path)

    if not frames:
        return {
            "score": 0.5,
            "passed": False,
            "signals": {},
            "reasons": ["Could not extract frames from video."],
            "verdict": "unavailable",
        }

    movements = _analyze_micro_movements(frames)
    blinks = _analyze_blink_pattern(frames)
    temporal = _analyze_temporal_consistency(frames)

    weights = {"movements": 0.40, "blinks": 0.30, "temporal": 0.30}
    score = (
        weights["movements"] * movements["score"]
        + weights["blinks"] * blinks["score"]
        + weights["temporal"] * temporal["score"]
    )
    score = max(0.0, min(1.0, score))
    passed = score >= 0.55

    reasons = []
    if not passed:
        reasons = [movements["note"], blinks["note"], temporal["note"]]

    return {
        "score": round(score, 3),
        "passed": passed,
        "frame_count": len(frames),
        "signals": {
            "movements": {"score": round(movements["score"], 3), "note": movements["note"]},
            "blinks": {"score": round(blinks["score"], 3), "note": blinks["note"]},
            "temporal": {"score": round(temporal["score"], 3), "note": temporal["note"]},
        },
        "reasons": reasons,
        "verdict": "live" if passed else "spoof",
    }
