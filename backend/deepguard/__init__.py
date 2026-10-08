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

from deepguard.address import verify_address
from deepguard.core import analyze_image, analyze_image_from_bytes
from deepguard.decision import decide
from deepguard.face import match_faces
from deepguard.liveness import analyze_video_liveness, detect_liveness
from deepguard.ocr import extract_mrz, extract_text

__all__ = [
    "analyze_image",
    "analyze_image_from_bytes",
    "analyze_video_liveness",
    "decide",
    "detect_liveness",
    "extract_mrz",
    "extract_text",
    "match_faces",
    "verify_address",
]
