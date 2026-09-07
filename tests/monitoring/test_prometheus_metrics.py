# --- DNK-MRH-HEADER ---
# mrh_id: "tests_monitoring_test_prometheus_metrics"
# purpose: "Integration tests for FastAPI Prometheus metrics endpoint and request instrumentation"
# author: "DNK-e.com Maksym & Gerych Prime"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# --- END DNK-MRH-HEADER ---

import os
import pytest
from fastapi.testclient import TestClient

from apps.api.main import app


def test_prometheus_metrics_endpoint():
    client = TestClient(app)

    # Invoke an endpoint to generate request telemetry
    client.get("/health")
    client.get("/api/health")

    # Scrape metrics
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers.get("content-type", "")

    content = response.text
    assert "http_requests_total" in content
    assert "http_request_duration_seconds" in content
