"""Email notification service for DeepGuard KYC events."""

from __future__ import annotations

import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from html import escape
import logging

from app.config import get_settings

logger = logging.getLogger(__name__)

EVENT_TEMPLATES = {
    "case.completed": {
        "subject": "KYC Case #{case_id} — Verification Complete",
        "body": """
        <h2>KYC Verification Complete</h2>
        <p>Case <strong>#{case_id}</strong> for <strong>{applicant}</strong> has been processed.</p>
        <table style="border-collapse:collapse;width:100%;max-width:600px">
            <tr><td style="padding:8px;border:1px solid #ddd"><strong>Score</strong></td><td style="padding:8px;border:1px solid #ddd">{score}/100</td></tr>
            <tr><td style="padding:8px;border:1px solid #ddd"><strong>Verdict</strong></td><td style="padding:8px;border:1px solid #ddd">{verdict}</td></tr>
            <tr><td style="padding:8px;border:1px solid #ddd"><strong>Status</strong></td><td style="padding:8px;border:1px solid #ddd">{status}</td></tr>
        </table>
        <p style="margin-top:16px"><a href="{dashboard_url}" style="background:#2563eb;color:white;padding:10px 20px;text-decoration:none;border-radius:6px">View in Dashboard</a></p>
        """,
    },
    "case.review_required": {
        "subject": "KYC Case #{case_id} — Manual Review Required",
        "body": """
        <h2>Manual Review Required</h2>
        <p>Case <strong>#{case_id}</strong> for <strong>{applicant}</strong> requires manual review.</p>
        <p>Score: {score}/100 | Verdict: {verdict}</p>
        <p><a href="{dashboard_url}">Review in Dashboard</a></p>
        """,
    },
    "sla.approaching": {
        "subject": "KYC Case #{case_id} — SLA Deadline Approaching",
        "body": """
        <h2>SLA Deadline Approaching</h2>
        <p>Case <strong>#{case_id}</strong> for <strong>{applicant}</strong> has an SLA deadline in {hours_remaining} hours.</p>
        <p>Current status: {status} | Score: {score}/100</p>
        """,
    },
    "batch.completed": {
        "subject": "Batch Job #{batch_id} — Processing Complete",
        "body": """
        <h2>Batch Processing Complete</h2>
        <p>Batch <strong>#{batch_id}</strong> has finished processing.</p>
        <table style="border-collapse:collapse;width:100%;max-width:600px">
            <tr><td style="padding:8px;border:1px solid #ddd"><strong>Total Files</strong></td><td style="padding:8px;border:1px solid #ddd">{total}</td></tr>
            <tr><td style="padding:8px;border:1px solid #ddd"><strong>Processed</strong></td><td style="padding:8px;border:1px solid #ddd">{processed}</td></tr>
            <tr><td style="padding:8px;border:1px solid #ddd"><strong>Failed</strong></td><td style="padding:8px;border:1px solid #ddd">{failed}</td></tr>
        </table>
        """,
    },
}

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")


def _sanitize_context(context: dict) -> dict:
    """HTML-escape all user-supplied values to prevent XSS."""
    return {k: escape(str(v)) if isinstance(v, str) else v for k, v in context.items()}


def send_email(recipient: str, event: str, context: dict) -> dict:
    """Send an email notification. Returns status dict."""
    settings = get_settings()

    if not settings.email_enabled:
        return {"status": "skipped", "error": "Email not configured"}

    template = EVENT_TEMPLATES.get(event)
    if not template:
        return {"status": "skipped", "error": f"Unknown event: {event}"}

    # Validate recipient email
    if not EMAIL_REGEX.match(recipient):
        return {"status": "failed", "error": "Invalid recipient email address"}

    # Sanitize context to prevent XSS
    safe_context = _sanitize_context(context)

    subject = template["subject"].format(**safe_context)
    body_html = template["body"].format(**safe_context)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from
    msg["To"] = recipient
    msg.attach(MIMEText(body_html, "html"))

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            if settings.smtp_user:
                server.login(settings.smtp_user, settings.smtp_pass)
            server.sendmail(settings.smtp_from, recipient, msg.as_string())
        return {"status": "sent", "error": ""}
    except Exception:
        logger.exception("Failed to send email")
        return {"status": "failed", "error": "Email delivery failed."}
