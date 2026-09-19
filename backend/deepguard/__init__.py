"""DeepGuard - Open-source KYC with forensic image analysis.

Usage as a library:
    from deepguard import analyze_image, match_faces, detect_liveness

    result = analyze_image("id_card.jpg")
    print(result["verdict"], result["score"])

Usage as a microservice:
    uvicorn deepguard.api:app --port 8765

Usage via CLI:
    python -m deepguard analyze image.jpg
"""

__version__ = "0.1.0"

from deepguard.core import analyze_image, analyze_image_from_bytes
from deepguard.face import match_faces
from deepguard.ocr import extract_text, extract_mrz
from deepguard.liveness import detect_liveness, analyze_video_liveness
from deepguard.address import verify_address
from deepguard.decision import decide

__all__ = [
    "analyze_image",
    "analyze_image_from_bytes",
    "match_faces",
    "extract_text",
    "extract_mrz",
    "detect_liveness",
    "analyze_video_liveness",
    "verify_address",
    "decide",
]
