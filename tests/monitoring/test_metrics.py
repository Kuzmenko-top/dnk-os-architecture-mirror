# --- DNK-MRH-HEADER ---
# mrh_id: "tests/monitoring/test_metrics.py"
# purpose: "Test suite for MetricsCollector and /metrics endpoint"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-23"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import pytest
from fastapi.testclient import TestClient
from dnk_os.core.metrics import MetricsCollector
from dnk_os.core.agent import app


class TestMetricsCollector:
    """Test suite for MetricsCollector."""
    
    def test_init(self):
        """Test initialization."""
        metrics = MetricsCollector()
        assert metrics is not None
        assert metrics.request_count == 0
        assert metrics.error_count == 0
        assert len(metrics.request_latencies) == 0
    
    def test_record_request(self):
        """Test request recording."""
        metrics = MetricsCollector()
        metrics.record_request(latency_ms=50.0)
        assert metrics.request_count == 1
        assert metrics.request_latencies == [50.0]
    
    def test_record_error(self):
        """Test error recording."""
        metrics = MetricsCollector()
        metrics.record_error()
        assert metrics.error_count == 1
    
    def test_record_task_execution(self):
        """Test task execution metrics recording."""
        metrics = MetricsCollector()
        metrics.record_task_execution(execution_time_ms=120.5)
        assert len(metrics.task_execution_times) == 1
        assert metrics.task_execution_times[0] == 120.5

    def test_record_agent_utilization(self):
        """Test agent utilization recording."""
        metrics = MetricsCollector()
        metrics.record_agent_utilization(agent_name="Герич", utilization=85.0)
        assert metrics.agent_utilization["Герич"] == 85.0

    def test_get_metrics(self):
        """Test metrics retrieval."""
        metrics = MetricsCollector()
        metrics.record_request(latency_ms=50.0)
        metrics.record_request(latency_ms=150.0)
        metrics.record_error()
        metrics.record_task_execution(execution_time_ms=200.0)
        metrics.record_agent_utilization(agent_name="Antigravity", utilization=60.0)
        
        result = metrics.get_metrics()
        assert result["request_count"] == 2
        assert result["error_count"] == 1
        assert result["error_rate"] == 0.5
        assert result["avg_latency_ms"] == 100.0
        assert result["avg_task_execution_time_ms"] == 200.0
        assert result["agent_utilization"]["Antigravity"] == 60.0
        assert "uptime_seconds" in result
        assert "timestamp" in result
    
    def test_reset_metrics(self):
        """Test metrics reset."""
        metrics = MetricsCollector()
        metrics.record_request(latency_ms=50.0)
        metrics.record_error()
        metrics.record_task_execution(execution_time_ms=100.0)
        metrics.record_agent_utilization(agent_name="Герич", utilization=90.0)
        
        metrics.reset_metrics()
        assert metrics.request_count == 0
        assert metrics.error_count == 0
        assert len(metrics.request_latencies) == 0
        assert len(metrics.task_execution_times) == 0
        assert len(metrics.agent_utilization) == 0

    def test_api_metrics_endpoint_fastapi(self):
        """Test FastAPI /metrics endpoint and request logging middleware."""
        client = TestClient(app)
        response = client.get("/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "request_count" in data
        assert "uptime_seconds" in data
        assert "timestamp" in data
