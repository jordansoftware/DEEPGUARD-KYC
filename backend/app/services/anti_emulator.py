"""Anti-emulator and device authenticity detection.

IMPORTANT: All checks are based on client-provided data and can be spoofed.
This module is an ADVISORY signal, not a blocking gate. Use it as one input
into a weighted scoring model. For high-security KYC, supplement with:
- TLS fingerprinting (JA3/JA4)
- IP geolocation consistency
- Device attestation (Apple App Attest / Google Play Integrity)
- Native app signed challenge-response
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

logger = logging.getLogger("deepguard.anti_emulator")

# Known emulator User-Agent patterns
EMULATOR_PATTERNS = [
    r"bluestacks",
    r"genymotion",
    r"ldplayer",
    r"nox",
    r"memu",
    r"andy",
    r"windroy",
    r"youwave",
    r"virtualbox",
    r"vmware",
    r"qemu",
    r"chromium.*headless",
    r"phantomjs",
    r"selenium",
    r"puppeteer",
    r"headlesschrome",
]

# Known bot/crawler User-Agent keywords
BOT_PATTERNS = [
    r"googlebot",
    r"bingbot",
    r"slurp",
    r"duckduckbot",
    r"baiduspider",
    r"yandex",
    r"facebookexternalhit",
    r"twitterbot",
    r"linkedinbot",
    r"whatsapp",
    r"telegrambot",
    r"discordbot",
]

# Valid mobile OS patterns
MOBILE_OS_PATTERNS = [
    r"android",
    r"iphone",
    r"ipad",
    r"windows phone",
    r"blackberry",
    r"mobile",
]


@dataclass
class DeviceCheck:
    is_emulator: bool
    is_bot: bool
    is_mobile: bool
    confidence: float  # 0-1, higher = more likely real mobile device
    reasons: list[str]


def check_device(
    user_agent: str | None,
    screen_width: int | None = None,
    screen_height: int | None = None,
    has_camera: bool | None = None,
    has_gyroscope: bool | None = None,
    webdriver: bool | None = None,
) -> DeviceCheck:
    """Analyze device properties to detect emulators and bots.

    WARNING: All inputs are client-provided and can be spoofed.
    This function provides advisory signals, not definitive verdicts.

    Args:
        user_agent: Browser User-Agent string
        screen_width: Screen width in pixels
        screen_height: Screen height in pixels
        has_camera: Whether device has a camera (client-reported)
        has_gyroscope: Whether device has a gyroscope (client-reported)
        webdriver: navigator.webdriver value (True = automation detected)

    Returns:
        DeviceCheck with is_emulator, is_bot, is_mobile, confidence, reasons
    """
    reasons = []
    is_emulator = False
    is_bot = False
    is_mobile = False
    confidence = 0.5  # start neutral

    ua = (user_agent or "").lower()

    # Check for emulators
    for pattern in EMULATOR_PATTERNS:
        if re.search(pattern, ua, re.IGNORECASE):
            is_emulator = True
            reasons.append(f"Emulator pattern detected: {pattern}")
            confidence -= 0.4
            break

    # Check for bots
    for pattern in BOT_PATTERNS:
        if re.search(pattern, ua, re.IGNORECASE):
            is_bot = True
            reasons.append(f"Bot pattern detected: {pattern}")
            confidence -= 0.5
            break

    # Check for mobile OS
    for pattern in MOBILE_OS_PATTERNS:
        if re.search(pattern, ua, re.IGNORECASE):
            is_mobile = True
            confidence += 0.15
            break

    # Check webdriver flag (indicates automation)
    if webdriver is True:
        is_emulator = True
        reasons.append("navigator.webdriver is true (automation detected)")
        confidence -= 0.3

    # Check screen dimensions (mobile typically portrait 9:16 to 9:19)
    if screen_width and screen_height:
        ratio = screen_width / screen_height
        if 0.4 < ratio < 0.7:  # portrait mobile
            confidence += 0.1
            reasons.append(f"Mobile screen ratio: {ratio:.2f}")
        elif ratio > 1.5:  # landscape desktop
            confidence -= 0.1
            reasons.append(f"Landscape/desktop screen ratio: {ratio:.2f}")

    # Client-reported features (low trust — easily spoofed)
    if has_camera is True:
        confidence += 0.05  # small boost — client-reported
        reasons.append("Camera accessible (client-reported)")
    elif has_camera is False:
        confidence -= 0.15
        reasons.append("Camera not accessible")

    if has_gyroscope is True:
        confidence += 0.05  # small boost — client-reported
        reasons.append("Gyroscope available (client-reported)")
    elif has_gyroscope is False:
        confidence -= 0.05
        reasons.append("No gyroscope")

    # Clamp confidence
    confidence = max(0.0, min(1.0, confidence))

    # If no User-Agent at all, suspicious
    if not user_agent:
        reasons.append("No User-Agent provided")
        confidence -= 0.2

    return DeviceCheck(
        is_emulator=is_emulator,
        is_bot=is_bot,
        is_mobile=is_mobile,
        confidence=round(confidence, 3),
        reasons=reasons,
    )


def get_device_summary(check: DeviceCheck) -> dict:
    """Convert DeviceCheck to a JSON-serializable dict.

    Verdict logic:
    - "blocked": emulator or bot detected (hard block)
    - "suspicious": low confidence (requires additional verification)
    - "advisory": client-side signals only, not definitive

    Note: Never assign "trusted" based solely on client-reported properties.
    Server-side signals (TLS fingerprint, attestation) are needed for trust.
    """
    if check.is_emulator or check.is_bot:
        verdict = "blocked"
    elif check.confidence < 0.5:
        verdict = "suspicious"
    else:
        verdict = "advisory"  # never "trusted" from client signals alone

    return {
        "is_emulator": check.is_emulator,
        "is_bot": check.is_bot,
        "is_mobile": check.is_mobile,
        "confidence": check.confidence,
        "reasons": check.reasons,
        "verdict": verdict,
        "warning": "Client-side signals only. Supplement with server-side verification for high-security decisions.",
    }
