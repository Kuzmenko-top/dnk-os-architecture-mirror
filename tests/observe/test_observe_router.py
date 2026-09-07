# --- DNK-MRH-HEADER ---
# mrh_id: "tests/observe/test_observe_router.py"
# purpose: "Integration Tests for Distributed Tracing & Observability REST Router (DNK-OBSERVE-001)"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.api.routers.observe_router import router
from apps.api.services.telemetry_collector_service import (
    TelemetryCollectorService,
    set_default_collector,
)


@pytest.fixture
def client():
    # Setup a fresh collector for test isolation
    fresh_collector = TelemetryCollectorService(
        batch_size=10,
        flush_interval_ms=1000,
        sample_rate=1.0,
        slow_trace_threshold_ms=100.0,
        always_sample_errors=True,
    )
    set_default_collector(fresh_collector)

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


class TestObserveRouter:
    """Integration test suite for Distributed Tracing REST Router."""

    def test_single_span_ingestion(self, client: TestClient):
        payload = {
            "name": "GET /api/v1/products",
            "service_name": "product_catalog",
            "kind": "SERVER",
            "status_code": "OK",
            "duration_ms": 15.4,
            "attributes": {"http.status_code": 200, "user_id": "user-42"},
        }
        res = client.post("/api/v1/observe/spans/ingest", json=payload)
        assert res.status_code == 202
        data = res.json()
        assert data["status"] == "success"
        assert data["format"] == "single_span"
        assert data["ingested_spans_count"] == 1

    def test_batch_span_ingestion(self, client: TestClient):
        payload = {
            "spans": [
                {
                    "name": "authenticate_request",
                    "service_name": "auth_service",
                    "duration_ms": 5.2,
                    "status_code": "OK",
                },
                {
                    "name": "query_database",
                    "service_name": "postgres_db",
                    "duration_ms": 22.1,
                    "status_code": "OK",
                },
            ]
        }
        res = client.post("/api/v1/observe/spans/ingest", json=payload)
        assert res.status_code == 202
        data = res.json()
        assert data["status"] == "success"
        assert data["format"] == "batch_spans"
        assert data["ingested_spans_count"] == 2

    def test_otlp_json_ingestion(self, client: TestClient):
        otlp_payload = {
            "resourceSpans": [
                {
                    "resource": {
                        "attributes": [
                            {"key": "service.name", "value": {"stringValue": "payment_gateway"}},
                            {"key": "service.version", "value": {"stringValue": "2.4.0"}},
                        ]
                    },
                    "scopeSpans": [
                        {
                            "spans": [
                                {
                                    "traceId": "4bf92f3577b34da6a3ce929d0e0e4736",
                                    "spanId": "00f067aa0ba902b7",
                                    "name": "charge_card",
                                    "kind": 1,
                                    "startTimeUnixNano": "1700000000000000000",
                                    "endTimeUnixNano": "1700000000085000000",
                                    "status": {"code": 1},
                                    "attributes": [
                                        {"key": "payment.gateway", "value": {"stringValue": "stripe"}}
                                    ],
                                }
                            ]
                        }
                    ],
                }
            ]
        }
        res = client.post("/api/v1/observe/spans/ingest", json=otlp_payload)
        assert res.status_code == 202
        data = res.json()
        assert data["status"] == "success"
        assert data["format"] == "otlp_json"
        assert data["ingested_spans_count"] == 1

    def test_list_traces_and_filtering(self, client: TestClient):
        # Ingest spans for multiple traces
        client.post(
            "/api/v1/observe/spans/ingest",
            json={
                "name": "checkout_order",
                "service_name": "checkout_svc",
                "trace_id": "11111111111111111111111111111111",
                "span_id": "2222222222222222",
                "duration_ms": 120.0,
                "status_code": "OK",
            },
        )
        client.post(
            "/api/v1/observe/spans/ingest",
            json={
                "name": "send_email",
                "service_name": "notification_svc",
                "trace_id": "33333333333333333333333333333333",
                "span_id": "4444444444444444",
                "duration_ms": 30.0,
                "status_code": "ERROR",
            },
        )

        # Force flush
        flush_res = client.post("/api/v1/observe/flush")
        assert flush_res.status_code == 200

        # Query all traces
        all_res = client.get("/api/v1/observe/traces")
        assert all_res.status_code == 200
        all_data = all_res.json()
        assert all_data["count"] >= 2

        # Filter by service
        svc_res = client.get("/api/v1/observe/traces?service_name=checkout_svc")
        assert svc_res.status_code == 200
        assert svc_res.json()["count"] == 1
        assert svc_res.json()["traces"][0]["root_service"] == "checkout_svc"

        # Filter by status
        err_res = client.get("/api/v1/observe/traces?status_code=ERROR")
        assert err_res.status_code == 200
        assert err_res.json()["count"] == 1
        assert err_res.json()["traces"][0]["has_error"] is True

        # Filter by min_duration_ms
        dur_res = client.get("/api/v1/observe/traces?min_duration_ms=100")
        assert dur_res.status_code == 200
        assert dur_res.json()["count"] == 1
        assert dur_res.json()["traces"][0]["trace_id"] == "11111111111111111111111111111111"

    def test_get_trace_details_and_not_found(self, client: TestClient):
        trace_id = "55555555555555555555555555555555"
        root_span_id = "6666666666666666"
        child_span_id = "7777777777777777"

        client.post(
            "/api/v1/observe/spans/ingest",
            json={
                "spans": [
                    {
                        "name": "root_operation",
                        "service_name": "gateway",
                        "trace_id": trace_id,
                        "span_id": root_span_id,
                        "duration_ms": 80.0,
                        "status_code": "OK",
                    },
                    {
                        "name": "child_operation",
                        "service_name": "worker",
                        "trace_id": trace_id,
                        "span_id": child_span_id,
                        "parent_span_id": root_span_id,
                        "duration_ms": 35.0,
                        "status_code": "OK",
                    },
                ]
            },
        )
        client.post("/api/v1/observe/flush")

        # Get existing trace
        res = client.get(f"/api/v1/observe/traces/{trace_id}")
        assert res.status_code == 200
        data = res.json()
        assert data["trace_id"] == trace_id
        assert data["span_count"] == 2
        assert len(data["spans"]) == 2
        assert "gateway" in data["services"]
        assert "worker" in data["services"]

        # Non-existent trace
        not_found_res = client.get("/api/v1/observe/traces/non_existent_trace_id_999")
        assert not_found_res.status_code == 404

    def test_service_topology_endpoint(self, client: TestClient):
        t_id = "88888888888888888888888888888888"
        p_id = "9999999999999999"
        c_id = "aaaaaaaaaaaaaaaa"

        client.post(
            "/api/v1/observe/spans/ingest",
            json={
                "spans": [
                    {
                        "name": "frontend_request",
                        "service_name": "ui_bff",
                        "trace_id": t_id,
                        "span_id": p_id,
                        "duration_ms": 100.0,
                    },
                    {
                        "name": "backend_call",
                        "service_name": "core_api",
                        "trace_id": t_id,
                        "span_id": c_id,
                        "parent_span_id": p_id,
                        "duration_ms": 40.0,
                    },
                ]
            },
        )
        client.post("/api/v1/observe/flush")

        res = client.get("/api/v1/observe/topology")
        assert res.status_code == 200
        topo = res.json()
        assert "nodes" in topo
        assert "edges" in topo
        node_names = [n["service_name"] if isinstance(n, dict) else n for n in topo["nodes"]]
        assert "ui_bff" in node_names
        assert "core_api" in node_names
        assert len(topo["edges"]) >= 1
        edge = topo["edges"][0]
        assert edge["caller"] == "ui_bff"
        assert edge["callee"] == "core_api"
        assert edge["call_count"] == 1

    def test_services_registry_and_registration(self, client: TestClient):
        # Register a service explicitly
        reg_payload = {
            "service_name": "video_renderer",
            "service_version": "3.1.0",
            "environment": "staging",
            "runtime": "python-ffmpeg",
            "status": "HEALTHY",
            "metadata": {"gpu": "nvidia-t4"},
        }
        reg_res = client.post("/api/v1/observe/services/register", json=reg_payload)
        assert reg_res.status_code == 200
        reg_data = reg_res.json()
        assert reg_data["status"] == "success"
        assert reg_data["service"]["service_name"] == "video_renderer"

        # List services
        list_res = client.get("/api/v1/observe/services")
        assert list_res.status_code == 200
        list_data = list_res.json()
        assert list_data["count"] >= 1
        service_names = [s["service_name"] for s in list_data["services"]]
        assert "video_renderer" in service_names

    def test_metric_aggregations_endpoint(self, client: TestClient):
        # Ingest multiple spans for metric aggregation
        durations = [10.0, 20.0, 30.0, 40.0, 50.0, 100.0]
        spans = [
            {
                "name": "render_component",
                "service_name": "react_ssr",
                "duration_ms": d,
                "status_code": "ERROR" if d == 100.0 else "OK",
            }
            for d in durations
        ]
        client.post("/api/v1/observe/spans/ingest", json={"spans": spans})
        client.post("/api/v1/observe/flush")

        res = client.get("/api/v1/observe/metrics/aggregations?service_name=react_ssr")
        assert res.status_code == 200
        data = res.json()
        assert data["count"] >= 1
        agg = data["aggregations"][0]
        assert agg["service_name"] == "react_ssr"
        assert agg["operation"] == "render_component"
        assert agg["call_count"] == 6
        assert agg["error_count"] == 1
        assert agg["error_rate"] == pytest.approx(1 / 6, rel=1e-2)
        assert agg.get("min_ms", agg.get("min_duration_ms")) == 10.0
        assert agg.get("max_ms", agg.get("max_duration_ms")) == 100.0
