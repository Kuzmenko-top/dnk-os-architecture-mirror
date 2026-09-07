# --- DNK-MRH-HEADER ---
# mrh_id: "tests_security_test_ssrf_guard"
# purpose: "Security test suite for SSRF guard, private IP blocking, DNS rebinding, hex/decimal IP, and upload limits"
# author: "DNK-e.com Maksym & Gerych"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-04"
# --- END DNK-MRH-HEADER ---

import pytest
from apps.api.lib.ssrf_guard import SSRFGuard
from fastapi.testclient import TestClient
from apps.api.routers.video_audit import router as video_audit_router
from fastapi import FastAPI


class TestSSRFGuard:
    @staticmethod
    def test_private_ip_block_127():
        is_allowed, msg = SSRFGuard.is_allowed_url("http://127.0.0.1:8000/test")
        assert not is_allowed
        assert "Private IP" in msg

    @staticmethod
    def test_private_ip_block_192():
        is_allowed, msg = SSRFGuard.is_allowed_url("http://192.168.1.1/test")
        assert not is_allowed
        assert "Private IP" in msg

    @staticmethod
    def test_private_ip_block_10():
        is_allowed, msg = SSRFGuard.is_allowed_url("http://10.0.0.1/internal")
        assert not is_allowed
        assert "Private IP" in msg

    @staticmethod
    def test_private_ip_block_172():
        is_allowed, msg = SSRFGuard.is_allowed_url("http://172.16.0.1/internal")
        assert not is_allowed
        assert "Private IP" in msg

    @staticmethod
    def test_aws_metadata_169_254():
        is_allowed, msg = SSRFGuard.is_allowed_url("http://169.254.169.254/latest/meta-data/")
        assert not is_allowed
        assert "Private IP" in msg

    @staticmethod
    def test_dns_rebinding():
        # Domain that is not in allowlist or resolves to private IP
        is_allowed, msg = SSRFGuard.is_allowed_url("http://evil-redirect.com/test")
        assert not is_allowed

    @staticmethod
    def test_decimal_ip():
        # 127.0.0.1 = 2130706433
        is_allowed, msg = SSRFGuard.is_allowed_url("http://2130706433/test")
        assert not is_allowed
        assert "Private IP" in msg or "Direct IP" in msg

    @staticmethod
    def test_hex_ip():
        # 127.0.0.1 = 0x7f000001
        is_allowed, msg = SSRFGuard.is_allowed_url("http://0x7f000001/test")
        assert not is_allowed
        assert "Private IP" in msg or "Direct IP" in msg

    @staticmethod
    def test_allowed_domain():
        is_allowed, msg = SSRFGuard.is_allowed_url("https://www.tiktok.com/@user/video/123")
        assert is_allowed
        assert msg == "OK"

    @staticmethod
    def test_allowed_domain_youtube():
        is_allowed, msg = SSRFGuard.is_allowed_url("https://youtube.com/watch?v=dQw4w9WgXcQ")
        assert is_allowed
        assert msg == "OK"

    @staticmethod
    def test_allowed_domain_shopify_cdn():
        is_allowed, msg = SSRFGuard.is_allowed_url("https://cdn.shopify.com/s/files/1/0000/products/video.mp4")
        assert is_allowed
        assert msg == "OK"

    @staticmethod
    def test_disallowed_domain():
        is_allowed, msg = SSRFGuard.is_allowed_url("https://evil.com/test")
        assert not is_allowed
        assert "not in allowlist" in msg

    @staticmethod
    def test_upload_limits_valid():
        valid, msg = SSRFGuard.validate_upload_limits(100 * 1024 * 1024, 300)
        assert valid
        assert msg == "OK"

    @staticmethod
    def test_upload_limits_payload_too_large():
        valid, msg = SSRFGuard.validate_upload_limits(200 * 1024 * 1024, 300)
        assert not valid
        assert "Payload too large" in msg

    @staticmethod
    def test_upload_limits_duration_too_long():
        valid, msg = SSRFGuard.validate_upload_limits(50 * 1024 * 1024, 700)
        assert not valid
        assert "Duration too long" in msg


def test_video_audit_endpoint_ssrf_blocked():
    app = FastAPI()
    app.include_router(video_audit_router)
    client = TestClient(app)

    # 1. Attacking localhost should be blocked (403)
    resp = client.post("/api/v1/canvas/video/audit", json={"video_url": "http://127.0.0.1:8000/internal"})
    assert resp.status_code == 403
    assert "SSRF blocked" in resp.json()["detail"]

    # 2. Attacking disallowed domain should be blocked (403)
    resp = client.post("/api/v1/canvas/video/audit", json={"video_url": "https://attacker.org/leak"})
    assert resp.status_code == 403
    assert "SSRF blocked" in resp.json()["detail"]

    # 3. Payload exceeding limits should be rejected (413)
    resp = client.post(
        "/api/v1/canvas/video/audit",
        json={
            "video_url": "https://www.tiktok.com/@user/video/123",
            "content_length": 200 * 1024 * 1024,
        },
    )
    assert resp.status_code == 413
    assert "Upload limits exceeded" in resp.json()["detail"]

    # 4. Valid allowlisted URL should pass (200)
    resp = client.post(
        "/api/v1/canvas/video/audit",
        json={
            "video_url": "https://www.tiktok.com/@user/video/123",
            "content_length": 50 * 1024 * 1024,
            "duration": 60.0,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
    assert resp.json()["ssrf_check"] == "clean"
