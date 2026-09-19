"""Comprehensive test suite for DeepGuard API endpoints."""

from __future__ import annotations

import io
import os
import struct
import tempfile
import zlib
from functools import lru_cache
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

# Use a temp file DB so tables persist across requests in the same test run
_test_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_test_db.name}"
os.environ["DEEP_GUARD_ALLOW_ANON"] = "true"

# Force settings cache to pick up the test DB URL BEFORE any module import
from app.config import get_settings  # noqa: E402

get_settings.cache_clear()

from app.db import init_db  # noqa: E402
from main import app  # noqa: E402

# Create tables once at import time
init_db()

client = TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _tiny_png() -> bytes:
    """Return a valid 1x1 white PNG in bytes."""
    raw = b"\x00\xff\xff\xff"
    compressed = zlib.compress(raw)

    def _chunk(ctype: bytes, data: bytes) -> bytes:
        c = ctype + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", ihdr)
        + _chunk(b"IDAT", compressed)
        + _chunk(b"IEND", b"")
    )


def _mock_analyze(path: str) -> dict:
    """Fast mock for signals.analyze_image (avoids heavy AI libs in unit tests)."""
    return {
        "score": 10,
        "verdict": "authentique",
        "verdict_label": "Authentique",
        "heatmap": "data:image/png;base64,abc",
        "image": "data:image/png;base64,xyz",
        "signals": {
            "mela": {"score": 5, "note": "ok"},
            "noise": {"score": 5, "note": "ok"},
            "ela": {"score": 5, "note": "ok"},
            "meta": {"score": 5, "notes": ["ok"]},
        },
        "reasons": [],
    }


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _setup_db():
    from app.models import Client
    from app.security import hash_api_key
    init_db()
    # Ensure demo client exists for anon mode
    from app.db import SessionLocal
    db = SessionLocal()
    try:
        from sqlalchemy import select
        if not db.scalar(select(Client).where(Client.email == "demo@deepguard.local")):
            db.add(Client(
                name="Demo Client", email="demo@deepguard.local",
                api_key=hash_api_key("dg_demo"), plan="pro",
            ))
            db.commit()
    finally:
        db.close()
    yield


@pytest.fixture()
def admin_key() -> str:
    import uuid
    uid = uuid.uuid4().hex[:8]
    payload = {"name": "Test Corp", "email": f"admin-{uid}@testcorp.com", "plan": "pro"}
    resp = client.post("/api/clients", json=payload, headers={"X-API-Key": "dg_demo"})
    assert resp.status_code == 201
    return resp.json()["api_key"]


def _auth(key: str) -> dict:
    """Helper: return headers dict with API key."""
    return {"X-API-Key": key}


# ---------------------------------------------------------------------------
# 1. Health check
# ---------------------------------------------------------------------------

class TestHealth:
    def test_health_ok(self):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# 2. Document analysis (POST /api/analyze)
# ---------------------------------------------------------------------------

class TestAnalyze:
    @patch("app.signals.analyze_image", side_effect=_mock_analyze)
    def test_analyze_valid_png(self, mock_fn):
        resp = client.post(
            "/api/analyze",
            files={"file": ("test.png", _tiny_png(), "image/png")},
            headers={"X-API-Key": "dg_demo"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["score"] == 10
        assert body["verdict"] == "authentique"
        assert body["filename"] == "test.png"
        assert body["size_bytes"] > 0

    def test_analyze_unsupported_format(self):
        resp = client.post(
            "/api/analyze",
            files={"file": ("test.txt", b"hello", "text/plain")},
            headers={"X-API-Key": "dg_demo"},
        )
        assert resp.status_code == 415

    def test_analyze_empty_file(self):
        resp = client.post(
            "/api/analyze",
            files={"file": ("empty.png", b"", "image/png")},
            headers={"X-API-Key": "dg_demo"},
        )
        assert resp.status_code == 400

    def test_analyze_missing_content_type(self):
        resp = client.post(
            "/api/analyze",
            files={"file": ("test.png", _tiny_png(), "")},
            headers={"X-API-Key": "dg_demo"},
        )
        assert resp.status_code == 400

    @patch("app.signals.analyze_image", side_effect=_mock_analyze)
    def test_analyze_no_auth(self, mock_fn):
        # When DEEP_GUARD_ALLOW_ANON=true, anon access is allowed
        # Test that invalid key is rejected
        resp = client.post(
            "/api/analyze",
            files={"file": ("test.png", _tiny_png(), "image/png")},
            headers={"X-API-Key": "dg_invalid_key"},
        )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# 3. KYC cases
# ---------------------------------------------------------------------------

class TestKYCCases:
    @patch("app.kyc.analyze_image", side_effect=_mock_analyze)
    def test_create_and_get_case(self, mock_fn):
        resp = client.post(
            "/api/kyc/cases",
            files={"file": ("doc.png", _tiny_png(), "image/png")},
            data={"applicant": "Alice", "doc_type": "cni", "reference": "TEST-001"},
            headers={"X-API-Key": "dg_demo"},
        )
        assert resp.status_code == 200, f"Create failed: {resp.json()}"
        case_id = resp.json()["id"]

        detail = client.get(f"/api/kyc/cases/{case_id}", headers={"X-API-Key": "dg_demo"})
        assert detail.status_code == 200
        assert detail.json()["applicant"].upper() == "ALICE"

    def test_list_cases(self):
        resp = client.get("/api/kyc/cases", headers={"X-API-Key": "dg_demo"})
        assert resp.status_code == 200
        assert "cases" in resp.json()

    def test_case_detail_not_found(self):
        resp = client.get("/api/kyc/cases/99999", headers={"X-API-Key": "dg_demo"})
        assert resp.status_code == 404

    @patch("app.kyc.analyze_image", side_effect=_mock_analyze)
    def test_case_decision(self, mock_fn):
        resp = client.post(
            "/api/kyc/cases",
            files={"file": ("doc.png", _tiny_png(), "image/png")},
            data={"applicant": "Bob"},
            headers={"X-API-Key": "dg_demo"},
        )
        assert resp.status_code == 200, f"Create failed: {resp.json()}"
        case_id = resp.json()["id"]
        dec = client.post(
            f"/api/kyc/cases/{case_id}/decision",
            json={"action": "approved"},
            headers={"X-API-Key": "dg_demo"},
        )
        assert dec.status_code == 200
        assert dec.json()["status"] == "approved"

    def test_case_decision_invalid_action(self):
        resp = client.post(
            "/api/kyc/cases/1/decision",
            json={"action": "invalid"},
            headers={"X-API-Key": "dg_demo"},
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# 4. Clients
# ---------------------------------------------------------------------------

class TestClients:
    def test_create_client(self):
        resp = client.post(
            "/api/clients",
            json={"name": "Acme", "email": "acme@test.com"},
            headers={"X-API-Key": "dg_demo"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["name"] == "Acme"
        assert body["api_key"].startswith("dg_")

    def test_create_client_duplicate_email(self):
        client.post(
            "/api/clients",
            json={"name": "Dup", "email": "dup@example.com"},
            headers={"X-API-Key": "dg_demo"},
        )
        resp = client.post(
            "/api/clients",
            json={"name": "Dup2", "email": "dup@example.com"},
            headers={"X-API-Key": "dg_demo"},
        )
        assert resp.status_code == 409

    def test_create_client_invalid_plan(self):
        resp = client.post(
            "/api/clients",
            json={"name": "Bad", "email": "bad@example.com", "plan": "ultra"},
            headers={"X-API-Key": "dg_demo"},
        )
        assert resp.status_code == 422

    def test_list_clients(self):
        resp = client.get("/api/clients", headers={"X-API-Key": "dg_demo"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        assert len(resp.json()) >= 1

    def test_get_client(self, admin_key):
        # Get the demo client's ID (id=1 typically)
        list_resp = client.get("/api/clients", headers={"X-API-Key": admin_key})
        # Find a client that belongs to this admin_key's client
        # For simplicity, create a new client and get it with its own key
        import uuid
        uid = uuid.uuid4().hex[:8]
        create_resp = client.post(
            "/api/clients",
            json={"name": "Get Me", "email": f"get-{uid}@test.com"},
            headers={"X-API-Key": admin_key},
        )
        cid = create_resp.json()["id"]
        get_key = create_resp.json()["api_key"]
        resp = client.get(f"/api/clients/{cid}", headers={"X-API-Key": get_key})
        assert resp.status_code == 200
        assert resp.json()["id"] == cid

    def test_get_client_not_found(self, admin_key):
        resp = client.get("/api/clients/99999", headers={"X-API-Key": admin_key})
        assert resp.status_code in (403, 404)

    def test_client_usage(self, admin_key):
        import uuid
        uid = uuid.uuid4().hex[:8]
        create_resp = client.post(
            "/api/clients",
            json={"name": "Usage", "email": f"usage-{uid}@test.com"},
            headers={"X-API-Key": admin_key},
        )
        cid = create_resp.json()["id"]
        get_key = create_resp.json()["api_key"]
        resp = client.get(f"/api/clients/{cid}/usage", headers={"X-API-Key": get_key})
        assert resp.status_code == 200
        body = resp.json()
        assert "quota_monthly" in body
        assert "used_this_month" in body
        assert "remaining" in body
        assert "pct" in body

    def test_client_usage_not_found(self, admin_key):
        resp = client.get("/api/clients/99999/usage", headers={"X-API-Key": admin_key})
        assert resp.status_code in (403, 404)

    def test_rotate_key(self, admin_key):
        import uuid
        uid = uuid.uuid4().hex[:8]
        create_resp = client.post(
            "/api/clients",
            json={"name": "Rotate", "email": f"rotate-{uid}@test.com"},
            headers={"X-API-Key": admin_key},
        )
        cid = create_resp.json()["id"]
        get_key = create_resp.json()["api_key"]
        resp = client.post(f"/api/clients/{cid}/rotate-key", headers={"X-API-Key": get_key})
        assert resp.status_code == 200
        body = resp.json()
        assert body["api_key"].startswith("dg_")
        assert "rotated_at" in body

    def test_rotate_key_not_found(self, admin_key):
        resp = client.post("/api/clients/99999/rotate-key", headers={"X-API-Key": admin_key})
        assert resp.status_code in (403, 404)

    def test_deactivate_client(self, admin_key):
        import uuid
        uid = uuid.uuid4().hex[:8]
        create_resp = client.post(
            "/api/clients",
            json={"name": "Deactivate", "email": f"deact-{uid}@test.com"},
            headers={"X-API-Key": admin_key},
        )
        cid = create_resp.json()["id"]
        get_key = create_resp.json()["api_key"]
        resp = client.delete(f"/api/clients/{cid}", headers={"X-API-Key": get_key})
        assert resp.status_code == 204

        # Verify by listing clients (deactivated client should have active=false)
        list_resp = client.get("/api/clients", headers={"X-API-Key": admin_key})
        found = [c for c in list_resp.json() if c["id"] == cid]
        assert len(found) == 1
        assert found[0]["active"] is False

    def test_deactivate_client_not_found(self, admin_key):
        resp = client.delete("/api/clients/99999", headers={"X-API-Key": admin_key})
        assert resp.status_code in (403, 404)


# ---------------------------------------------------------------------------
# 5. Webhooks
# ---------------------------------------------------------------------------

class TestWebhooks:
    def test_create_webhook(self):
        resp = client.post(
            "/api/webhooks",
            json={
                "url": "https://example.com/hook",
                "events": ["case.completed"],
                "active": True,
            },
            headers={"X-API-Key": "dg_demo"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["url"] == "https://example.com/hook"
        assert body["active"] is True
        assert body["events"] == ["case.completed"]

    def test_create_webhook_invalid_url(self):
        resp = client.post(
            "/api/webhooks",
            json={"url": "not-a-url", "events": []},
            headers={"X-API-Key": "dg_demo"},
        )
        assert resp.status_code == 422

    def test_list_webhooks(self):
        resp = client.get("/api/webhooks", headers={"X-API-Key": "dg_demo"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_create_webhook_ssrf_blocked(self):
        resp = client.post(
            "/api/webhooks",
            json={"url": "http://169.254.169.254/metadata", "events": []},
            headers={"X-API-Key": "dg_demo"},
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# 6. Screening
# ---------------------------------------------------------------------------

class TestScreening:
    def test_screen_clean(self):
        resp = client.post(
            "/api/screening",
            json={"name": "John Smith"},
            headers={"X-API-Key": "dg_demo"},
        )
        assert resp.status_code == 200
        assert resp.json()["matched"] is False

    def test_screen_match(self):
        resp = client.post(
            "/api/screening",
            json={"name": "Vladimir Putin"},
            headers={"X-API-Key": "dg_demo"},
        )
        assert resp.status_code == 200
        assert resp.json()["matched"] is True


# ---------------------------------------------------------------------------
# 7. Rules
# ---------------------------------------------------------------------------

class TestRules:
    def test_get_defaults(self):
        resp = client.get("/api/rules/defaults", headers={"X-API-Key": "dg_demo"})
        assert resp.status_code == 200
        body = resp.json()
        assert "weights" in body
        assert "defect_weights" in body

    def test_get_client_rules(self):
        resp = client.get("/api/rules/client/1", headers={"X-API-Key": "dg_demo"})
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# 8. Analytics
# ---------------------------------------------------------------------------

class TestAnalytics:
    def test_overview(self):
        resp = client.get("/api/analytics/overview", headers={"X-API-Key": "dg_demo"})
        assert resp.status_code == 200
        assert "total_cases" in resp.json()

    def test_trends(self):
        resp = client.get("/api/analytics/trends", headers={"X-API-Key": "dg_demo"})
        assert resp.status_code == 200

    def test_risk_distribution(self):
        resp = client.get("/api/analytics/risk-distribution", headers={"X-API-Key": "dg_demo"})
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# 9. Plugins
# ---------------------------------------------------------------------------

class TestPlugins:
    def test_list_plugins(self):
        resp = client.get("/api/plugins/", headers={"X-API-Key": "dg_demo"})
        assert resp.status_code == 200
        assert "plugins" in resp.json()

    def test_get_plugin(self):
        resp = client.get("/api/plugins/slack", headers={"X-API-Key": "dg_demo"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "slack"

    def test_get_plugin_not_found(self):
        resp = client.get("/api/plugins/nonexistent", headers={"X-API-Key": "dg_demo"})
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# 10. Batch
# ---------------------------------------------------------------------------

class TestBatch:
    def test_list_batches(self):
        resp = client.get("/api/batch/", headers={"X-API-Key": "dg_demo"})
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# 11. Export
# ---------------------------------------------------------------------------

class TestExport:
    def test_export_csv(self):
        resp = client.get("/api/export/cases?format=csv", headers={"X-API-Key": "dg_demo"})
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "text/csv; charset=utf-8"
