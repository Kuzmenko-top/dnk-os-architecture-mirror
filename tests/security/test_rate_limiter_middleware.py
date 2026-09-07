# --- DNK-MRH-HEADER ---
# mrh_id: "tests_security_test_rate_limiter_middleware"
# purpose: "Unit and integration tests for RateLimiterMiddleware and Prometheus metrics instrumentation"
# author: "DNK-e.com Maksym & Gerych Prime"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# --- END DNK-MRH-HEADER ---

import os
import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from apps.api.middleware.rate_limit import RateLimiterMiddleware, InMemorySlidingWindowLimiter


def create_test_app(default_limit=5, sensitive_limit=2):
    app = FastAPI()
    app.add_middleware(
        RateLimiterMiddleware,
        default_limit=default_limit,
        sensitive_limit=sensitive_limit,
        window_seconds=60,
    )

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/api/public")
    def public():
        return {"data": "public"}

    @app.get("/auth/login")
    def auth():
        return {"status": "authenticated"}

    return app


def test_in_memory_sliding_window_limiter():
    limiter = InMemorySlidingWindowLimiter()
    key = "test_ip_1"

    # 3 requests allowed with limit=3
    for _ in range(3):
        allowed, remaining, reset_at = limiter.check_rate_limit(key, max_requests=3, window_seconds=10)
        assert allowed is True

    # 4th request must be rejected
    allowed, remaining, reset_at = limiter.check_rate_limit(key, max_requests=3, window_seconds=10)
    assert allowed is False
    assert remaining == 0
    assert reset_at > 0


def test_rate_limiter_middleware_bypass_in_testing():
    # When TESTING=1 or PYTEST_CURRENT_TEST is set, middleware bypasses
    app = create_test_app(default_limit=2)
    client = TestClient(app)

    # All requests should succeed because test runner sets PYTEST_CURRENT_TEST
    for _ in range(10):
        resp = client.get("/api/public")
        assert resp.status_code == 200


def test_rate_limiter_middleware_enforcement_when_not_testing(monkeypatch):
    monkeypatch.delenv("TESTING", raising=False)
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)

    app = create_test_app(default_limit=3, sensitive_limit=2)
    client = TestClient(app)

    # 3 public requests succeed
    for _ in range(3):
        resp = client.get("/api/public")
        assert resp.status_code == 200
        assert "X-RateLimit-Limit" in resp.headers

    # 4th request should return 429
    resp = client.get("/api/public")
    assert resp.status_code == 429
    assert resp.json()["error_type"] == "RateLimitExceeded"
    assert "Retry-After" in resp.headers


def test_rate_limiter_middleware_sensitive_route_lower_limit(monkeypatch):
    monkeypatch.delenv("TESTING", raising=False)
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)

    app = create_test_app(default_limit=10, sensitive_limit=2)
    client = TestClient(app)

    # Sensitive route allows 2
    r1 = client.get("/auth/login")
    assert r1.status_code == 200

    r2 = client.get("/auth/login")
    assert r2.status_code == 200

    r3 = client.get("/auth/login")
    assert r3.status_code == 429
    assert r3.json()["error_type"] == "RateLimitExceeded"


def test_rate_limiter_middleware_bypasses_health(monkeypatch):
    monkeypatch.delenv("TESTING", raising=False)
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)

    app = create_test_app(default_limit=2)
    client = TestClient(app)

    # Health check is in BYPASS_PATHS and never gets rate limited
    for _ in range(10):
        resp = client.get("/health")
        assert resp.status_code == 200
