# --- DNK-MRH-HEADER ---
# mrh_id: "tests/observe/test_telemetry_collector_service.py"
# purpose: "Unit tests for Telemetry Collector and Exporter Service (DNK-OBSERVE-001)"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

import pytest
from apps.api.services.telemetry_collector_service import TelemetryCollectorService


class TestTelemetryCollectorService:
    """Test suite for Phase 2 Telemetry Collector & Exporter."""

    def test_service_registration_and_list(self):
        collector = TelemetryCollectorService()
        srv = collector.register_service(
            name="dnk_event_stream_bus",
            environment="production",
            version="1.0.0",
            health_status="HEALTHY",
            metadata_info={"cluster": "alpha"},
        )
        assert srv["name"] == "dnk_event_stream_bus"
        assert srv["health_status"] == "HEALTHY"

        fetched = collector.get_service("dnk_event_stream_bus")
        assert fetched is not None
        assert fetched["version"] == "1.0.0"

        all_services = collector.list_services()
        assert len(all_services) == 1
        assert all_services[0]["name"] == "dnk_event_stream_bus"

    def test_single_span_ingestion_and_auto_service_registration(self):
        collector = TelemetryCollectorService(batch_size=10)
        res = collector.ingest_span({
            "service_name": "dnk_a2a_mesh",
            "name": "RouteMessageEnvelope",
            "kind": "SERVER",
            "duration_ms": 14.5,
            "attributes": {"a2a.agent_id": "agent_builder"},
        })
        assert res["status"] == "buffered"
        assert "span_id" in res
        assert "trace_id" in res

        # Check auto-registered service
        srv = collector.get_service("dnk_a2a_mesh")
        assert srv is not None
        assert srv["name"] == "dnk_a2a_mesh"

    def test_batch_ingestion_and_auto_flush(self):
        collector = TelemetryCollectorService(batch_size=5)
        spans = [
            {
                "service_name": "dnk_api_gateway",
                "name": f"HTTP_GET_/item_{i}",
                "duration_ms": 5.0 + i,
            }
            for i in range(6)
        ]
        res = collector.ingest_spans(spans)
        assert res["total_submitted"] == 6
        assert res["ingested_count"] == 6
        # Batch size is 5, so after 5 it flushed, leaving 1 in buffer
        assert res["buffer_size"] == 1

        # Force flush and verify total stored
        collector.flush()
        traces = collector.list_traces()
        assert len(traces) == 6

    def test_otlp_json_payload_ingestion(self):
        collector = TelemetryCollectorService()
        otlp_payload = {
            "resourceSpans": [
                {
                    "resource": {
                        "attributes": [
                            {"key": "service.name", "value": {"stringValue": "dnk_shopify_bridge"}}
                        ]
                    },
                    "scopeSpans": [
                        {
                            "spans": [
                                {
                                    "traceId": "4bf92f3577b34da6a3ce929d0e0e4736",
                                    "spanId": "00f067aa0ba902b7",
                                    "name": "SyncShopifyWebhooks",
                                    "kind": "CONSUMER",
                                    "startTimeUnixNano": 1724900000000000000,
                                    "endTimeUnixNano": 1724900000025000000,  # 25 ms
                                    "status": {"code": "STATUS_CODE_ERROR", "message": "Rate limit exceeded"},
                                    "attributes": [
                                        {"key": "shopify.shop", "value": {"stringValue": "mystore.myshopify.com"}},
                                        {"key": "http.status_code", "value": {"intValue": 429}},
                                    ],
                                }
                            ]
                        }
                    ],
                }
            ]
        }

        res = collector.ingest_otlp_json(otlp_payload)
        assert res["ingested_count"] == 1

        trace_spans = collector.get_trace("4bf92f3577b34da6a3ce929d0e0e4736")
        assert len(trace_spans) == 1
        sp = trace_spans[0]
        assert sp["service_name"] == "dnk_shopify_bridge"
        assert sp["name"] == "SyncShopifyWebhooks"
        assert sp["status_code"] == "ERROR"
        assert sp["status_message"] == "Rate limit exceeded"
        assert sp["duration_ms"] == 25.0
        assert sp["attributes"]["shopify.shop"] == "mystore.myshopify.com"

    def test_tail_sampling_error_and_latency_retention(self):
        # sample_rate = 0.0 (drops ordinary spans), but preserves errors and slow traces (> 100ms)
        collector = TelemetryCollectorService(
            sample_rate=0.0,
            always_sample_errors=True,
            slow_trace_threshold_ms=100.0,
        )

        # 1. Normal fast span -> dropped
        r1 = collector.ingest_span({
            "service_name": "svc1",
            "name": "fast_op",
            "duration_ms": 10.0,
            "status_code": "OK",
        })
        assert r1["status"] == "dropped_by_sampling"

        # 2. Error span -> retained
        r2 = collector.ingest_span({
            "service_name": "svc1",
            "name": "failing_op",
            "duration_ms": 15.0,
            "status_code": "ERROR",
        })
        assert r2["status"] == "buffered"

        # 3. Slow span -> retained
        r3 = collector.ingest_span({
            "service_name": "svc1",
            "name": "slow_database_query",
            "duration_ms": 250.0,
            "status_code": "OK",
        })
        assert r3["status"] == "buffered"

    def test_exporter_callbacks(self):
        collector = TelemetryCollectorService(batch_size=2)
        exported_data = []

        def mock_clickhouse_exporter(batch):
            exported_data.append(batch)

        collector.register_exporter("clickhouse", mock_clickhouse_exporter)

        collector.ingest_span({"service_name": "svc_test", "name": "op1", "duration_ms": 10})
        assert len(exported_data) == 0

        collector.ingest_span({"service_name": "svc_test", "name": "op2", "duration_ms": 20})
        # Auto-flushed at batch_size=2
        assert len(exported_data) == 1
        assert len(exported_data[0]) == 2

    def test_trace_retrieval_and_filtering(self):
        collector = TelemetryCollectorService()
        trace_id = "trace_abc_123"

        # Root span
        collector.ingest_span({
            "trace_id": trace_id,
            "span_id": "span_root",
            "parent_span_id": None,
            "service_name": "gateway",
            "name": "POST /orders",
            "duration_ms": 80.0,
            "status_code": "OK",
        })

        # Child span 1
        collector.ingest_span({
            "trace_id": trace_id,
            "span_id": "span_child_1",
            "parent_span_id": "span_root",
            "service_name": "payment_service",
            "name": "ProcessPayment",
            "duration_ms": 40.0,
            "status_code": "OK",
        })

        # Child span 2 (Error)
        collector.ingest_span({
            "trace_id": trace_id,
            "span_id": "span_child_2",
            "parent_span_id": "span_root",
            "service_name": "notification_service",
            "name": "SendReceipt",
            "duration_ms": 15.0,
            "status_code": "ERROR",
        })

        trace = collector.get_trace(trace_id)
        assert len(trace) == 3

        # Filter by service_name
        list_gateway = collector.list_traces(service_name="gateway")
        assert len(list_gateway) == 1
        assert list_gateway[0]["trace_id"] == trace_id
        assert list_gateway[0]["has_error"] is True
        assert set(list_gateway[0]["services"]) == {"gateway", "payment_service", "notification_service"}

        # Filter by status_code
        list_err = collector.list_traces(status_code="ERROR")
        assert len(list_err) == 1

    def test_service_topology_dependency_graph(self):
        collector = TelemetryCollectorService()
        trace_id = "trace_topo_999"

        collector.ingest_span({
            "trace_id": trace_id,
            "span_id": "root_span",
            "service_name": "api_gateway",
            "name": "HandleRequest",
            "duration_ms": 100.0,
        })
        collector.ingest_span({
            "trace_id": trace_id,
            "span_id": "child_span_1",
            "parent_span_id": "root_span",
            "service_name": "stream_bus",
            "name": "PublishEvent",
            "duration_ms": 30.0,
        })
        collector.ingest_span({
            "trace_id": trace_id,
            "span_id": "child_span_2",
            "parent_span_id": "child_span_1",
            "service_name": "clickhouse_sink",
            "name": "InsertBuffer",
            "duration_ms": 15.0,
            "status_code": "ERROR",
        })

        topo = collector.get_service_topology()
        assert topo["total_services"] >= 3
        assert topo["total_dependencies"] == 2

        edges = {(e["source"], e["target"]): e for e in topo["edges"]}
        assert ("api_gateway", "stream_bus") in edges
        assert edges[("api_gateway", "stream_bus")]["call_count"] == 1
        assert ("stream_bus", "clickhouse_sink") in edges
        assert edges[("stream_bus", "clickhouse_sink")]["error_rate"] == 1.0

    def test_compute_aggregations(self):
        collector = TelemetryCollectorService()
        durations = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0]
        for idx, d in enumerate(durations):
            collector.ingest_span({
                "service_name": "dnk_health_service",
                "name": "CheckSystemProbes",
                "duration_ms": d,
                "status_code": "ERROR" if idx == 0 else "OK",
            })

        aggs = collector.compute_aggregations(service_name="dnk_health_service")
        assert len(aggs) == 1
        agg = aggs[0]
        assert agg["service_name"] == "dnk_health_service"
        assert agg["operation"] == "CheckSystemProbes"
        assert agg["call_count"] == 10
        assert agg["error_count"] == 1
        assert agg["error_rate"] == 0.10
        assert agg["min_ms"] == 10.0
        assert agg["max_ms"] == 100.0
        assert agg["p50_ms"] == 60.0
