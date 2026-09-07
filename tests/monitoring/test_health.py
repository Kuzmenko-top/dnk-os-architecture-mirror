# --- DNK-MRH-HEADER ---
# mrh_id: "tests/monitoring/test_health.py"
# purpose: "Test suite for HealthChecker and /health endpoint"
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
from dnk_os.core.health import HealthChecker
from dnk_os.core.agent import app


class TestHealthChecker:
    """Test suite for HealthChecker."""
    
    def test_init(self):
        """Test initialization."""
        checker = HealthChecker()
        assert checker is not None
        assert checker.memory_threshold == 0.95
        assert checker.cpu_threshold == 0.95
        assert checker.disk_threshold == 0.95
    
    def test_check_api_health(self):
        """Test API health check."""
        checker = HealthChecker()
        health = checker.check_api_health()
        assert health["status"] == "healthy"
        assert "timestamp" in health
        assert health["service"] == "dnk-api"
    
    def test_check_database_health(self):
        """Test database health check."""
        checker = HealthChecker()
        health = checker.check_database_health()
        assert health["status"] == "healthy"
        assert health["connection"] == "active"
        assert "latency_ms" in health
    
    def test_check_redis_health(self):
        """Test Redis health check."""
        checker = HealthChecker()
        health = checker.check_redis_health()
        assert health["status"] == "healthy"
        assert health["connection"] == "active"
        assert "latency_ms" in health
    
    def test_check_memory_health(self):
        """Test memory health check."""
        checker = HealthChecker()
        health = checker.check_memory_health()
        assert health["status"] in ["healthy", "unhealthy"]
        assert "usage_percent" in health
        assert "available_mb" in health
        assert "total_mb" in health
    
    def test_check_cpu_health(self):
        """Test CPU health check."""
        checker = HealthChecker()
        health = checker.check_cpu_health()
        assert health["status"] in ["healthy", "unhealthy"]
        assert "usage_percent" in health
        assert "cores" in health
    
    def test_check_disk_health(self):
        """Test disk health check."""
        checker = HealthChecker()
        health = checker.check_disk_health()
        assert health["status"] in ["healthy", "unhealthy"]
        assert "usage_percent" in health
        assert "free_gb" in health
        assert "total_gb" in health
    
    def test_get_full_health(self):
        """Test full health report."""
        checker = HealthChecker()
        health = checker.get_full_health()
        assert health["status"] in ["healthy", "unhealthy"]
        assert "services" in health
        assert "api" in health["services"]
        assert "database" in health["services"]
        assert "redis" in health["services"]
        assert "memory" in health["services"]
        assert "cpu" in health["services"]
        assert "disk" in health["services"]

    def test_unhealthy_threshold_trigger(self):
        """Test threshold trigger for unhealthy status."""
        # Force memory threshold to 0 to trigger unhealthy status
        checker = HealthChecker(memory_threshold=0.0)
        health = checker.check_memory_health()
        assert health["status"] == "unhealthy"
        full = checker.get_full_health()
        assert full["status"] == "unhealthy"

    def test_api_health_endpoint_fastapi(self):
        """Test FastAPI /health route."""
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "services" in data
        assert "timestamp" in data
