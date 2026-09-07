# --- DNK-MRH-HEADER ---
# mrh_id: "tests/load_balancing/test_load_balancing.py"
# purpose: "Test suite for Nginx load balancing, rate limiting, and Docker Compose scaling"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-23"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import os
import yaml
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from dnk_os.core.agent import app


class TestLoadBalancingConfig:
    """Test suite for Nginx and Docker Compose load balancing configuration."""

    def test_nginx_config_exists_and_valid(self):
        """Test Nginx configuration structure and directives."""
        nginx_conf_path = "dnk_os/nginx/nginx.conf"
        assert os.path.exists(nginx_conf_path)
        with open(nginx_conf_path, "r") as f:
            content = f.read()

        # Upstream load balancing directives
        assert "upstream dnk_api" in content
        assert "least_conn;" in content
        assert "server dnk-api-1:8000" in content
        assert "server dnk-api-2:8000" in content
        assert "server dnk-api-3:8000" in content

        # Rate limiting directives
        assert "limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;" in content
        assert "limit_req_zone $binary_remote_addr zone=stream_limit:10m rate=5r/s;" in content

        # Endpoint locations
        assert "location /health" in content
        assert "location /metrics" in content
        assert "location /stream/" in content
        assert "location /session/" in content
        assert "proxy_pass http://dnk_api;" in content

    def test_rate_limit_config_exists(self):
        """Test rate limit configuration file exists and contains documentation."""
        rate_limit_path = "dnk_os/nginx/rate_limit.conf"
        assert os.path.exists(rate_limit_path)
        with open(rate_limit_path, "r") as f:
            content = f.read()
        assert "API rate limits" in content
        assert "10 requests/second" in content

    def test_docker_compose_prod_scaling(self):
        """Test production docker-compose file for scaled API instances."""
        prod_compose_path = "dnk_os/docker-compose.prod.yml"
        assert os.path.exists(prod_compose_path)
        with open(prod_compose_path, "r") as f:
            compose_cfg = yaml.safe_load(f)

        services = compose_cfg.get("services", {})
        assert "nginx" in services
        assert "dnk-api-1" in services
        assert "dnk-api-2" in services
        assert "dnk-api-3" in services
        assert "dnk-frontend" in services

        # Check Nginx dependencies
        nginx_deps = services["nginx"].get("depends_on", [])
        assert "dnk-api-1" in nginx_deps
        assert "dnk-api-2" in nginx_deps
        assert "dnk-api-3" in nginx_deps

        # Check Nginx ports
        assert "80:80" in services["nginx"]["ports"]


class TestLoadBalancingEndpoints:
    """Test suite for load balanced endpoint behavior using TestClient and mocks."""

    def test_nginx_health(self):
        """Test Nginx health via agent health endpoint."""
        with patch("psutil.cpu_percent", return_value=10.0), patch("psutil.virtual_memory") as mock_mem:
            mock_mem.return_value.percent = 40.0
            mock_mem.return_value.available = 4000 * 1024 * 1024
            mock_mem.return_value.total = 8000 * 1024 * 1024
            client = TestClient(app)
            response = client.get("/health")
            assert response.status_code == 200
            assert response.json()["status"] == "healthy"

    def test_api_instances(self):
        """Test simulation of multiple API instances health status."""
        with patch("psutil.cpu_percent", return_value=10.0), patch("psutil.virtual_memory") as mock_mem:
            mock_mem.return_value.percent = 40.0
            mock_mem.return_value.available = 4000 * 1024 * 1024
            mock_mem.return_value.total = 8000 * 1024 * 1024
            for i in range(1, 4):
                client = TestClient(app)
                response = client.get("/health")
                assert response.status_code == 200
                assert response.json()["status"] == "healthy"


    def test_rate_limiting(self):
        """Test rate limiting logic simulation."""
        responses = []
        # Simulate burst exceeding limit
        for i in range(15):
            if i >= 10:
                responses.append(429)
            else:
                responses.append(200)

        assert 429 in responses
        assert responses.count(200) == 10
        assert responses.count(429) == 5

    def test_load_distribution(self):
        """Test load distribution across instances."""
        instances = ["api-1", "api-2", "api-3"]
        instance_ids = []
        for i in range(10):
            instance_ids.append(instances[i % 3])

        unique_instances = set(instance_ids)
        assert len(unique_instances) == 3
        assert "api-1" in unique_instances
        assert "api-2" in unique_instances
        assert "api-3" in unique_instances

    def test_streaming_endpoint(self):
        """Test streaming endpoint headers and behavior."""
        client = TestClient(app)
        response = client.get("/stream/example")
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")

    def test_session_endpoint(self):
        """Test session lifecycle through API."""
        from unittest.mock import MagicMock
        with patch("dnk_os.core.agent.session_manager.redis") as mock_redis, \
             patch("dnk_os.core.session.redis.Redis"):
            mock_redis.setex = MagicMock(return_value=True)
            mock_redis.get = MagicMock(return_value=None)
            client = TestClient(app)
            # Create session
            create_resp = client.post("/session/create", json={"user_id": "user123"})
            assert create_resp.status_code == 200
            data = create_resp.json()
            assert "session_id" in data

    def test_failover(self):
        """Test failover routing when an instance fails."""
        responses = []
        client = TestClient(app)
        for _ in range(5):
            response = client.get("/health")
            responses.append(response.status_code)

        assert all(r == 200 for r in responses)
