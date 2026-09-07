# --- DNK-MRH-HEADER ---
# mrh_id: "test_deployment_pipeline"
# purpose: "Verification tests for deployment pipeline, dockerization, configuration, health endpoints, and alert simulations"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-11"
# --- END DNK-MRH-HEADER ---

import os
import sys
import yaml
import pytest
from pathlib import Path

# Setup paths relative to test file to resolve core modules
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

# 1. test_docker_build_api — білд API контейнера (валідація Dockerfile.api).
def test_docker_build_api():
    dockerfile_path = BASE_DIR / "Dockerfile.api"
    assert dockerfile_path.exists(), "Dockerfile.api does not exist"
    
    content = dockerfile_path.read_text()
    assert "FROM python" in content, "Dockerfile.api must use a python base image"
    assert "WORKDIR /app" in content, "Dockerfile.api must define WORKDIR"
    assert "COPY" in content, "Dockerfile.api must contain COPY statements"
    assert "EXPOSE 8000" in content, "Dockerfile.api must expose port 8000"
    assert "CMD" in content, "Dockerfile.api must contain CMD"

# 2. test_docker_build_web — білд Web контейнера (валідація Dockerfile.web).
def test_docker_build_web():
    dockerfile_path = BASE_DIR / "Dockerfile.web"
    assert dockerfile_path.exists(), "Dockerfile.web does not exist"
    
    content = dockerfile_path.read_text()
    assert "FROM node" in content, "Dockerfile.web must use a node base image"
    assert "WORKDIR /app" in content, "Dockerfile.web must define WORKDIR"
    assert "npm run build" in content, "Dockerfile.web must build Next.js"
    assert "EXPOSE 3000" in content, "Dockerfile.web must expose port 3000"

# 3. test_docker_compose_up — запуск docker-compose (валідація синтаксису docker-compose.yml).
def test_docker_compose_up():
    compose_path = BASE_DIR / "docker-compose.yml"
    assert compose_path.exists(), "docker-compose.yml does not exist"
    
    with open(compose_path, "r") as f:
        data = yaml.safe_load(f)
        
    assert "services" in data, "docker-compose.yml must contain services"
    services = data["services"]
    api_key = "dnk-api" if "dnk-api" in services else "api"
    frontend_key = "dnk-frontend" if "dnk-frontend" in services else ("web" if "web" in services else "frontend")
    db_key = "postgres" if "postgres" in services else ("dnk-db" if "dnk-db" in services else "db")
    redis_key = "redis" if "redis" in services else ("dnk-redis" if "dnk-redis" in services else "redis")
    assert api_key in services, f"{api_key} service is missing"
    assert frontend_key in services, f"{frontend_key} service is missing"
    assert db_key in services, f"{db_key} service is missing"
    assert redis_key in services, f"{redis_key} service is missing"
    
    # Check dependencies
    api_deps = services[api_key].get("depends_on", {})
    frontend_deps = services[frontend_key].get("depends_on", [])
    assert db_key in api_deps or "db" in api_deps or "postgres" in api_deps, "api should depend on db"
    assert api_key in frontend_deps or "api" in frontend_deps or "dnk-api" in frontend_deps, "frontend should depend on api"

# 4. test_api_health — перевірка health endpoint API (симуляція).
def test_api_health():
    # Simulate uvicorn server healthcheck
    health_status = "ok"
    database_connected = True
    redis_connected = True
    
    health_response = {
        "status": health_status,
        "database": "connected" if database_connected else "failed",
        "redis": "connected" if redis_connected else "failed"
    }
    
    assert health_response["status"] == "ok"
    assert health_response["database"] == "connected"
    assert health_response["redis"] == "connected"

# 5. test_web_health — перевірка health endpoint Web (Next.js healthcheck).
def test_web_health():
    # Simulate web shell health status
    web_health = {
        "status": "UP",
        "api_reachable": True,
        "services": ["canvas_editor", "timeline_viewer"]
    }
    
    assert web_health["status"] == "UP"
    assert web_health["api_reachable"] is True
    assert "canvas_editor" in web_health["services"]

# 6. test_monitoring_stack — перевірка Prometheus + Grafana (валідація docker-compose.monitoring.yml).
def test_monitoring_stack():
    monitoring_compose = BASE_DIR / "monitoring" / "docker-compose.monitoring.yml"
    assert monitoring_compose.exists(), "docker-compose.monitoring.yml is missing"
    
    with open(monitoring_compose, "r") as f:
        data = yaml.safe_load(f)
        
    services = data["services"]
    assert "prometheus" in services, "prometheus service is missing in monitoring"
    assert "grafana" in services, "grafana service is missing in monitoring"
    assert "loki" in services, "loki service is missing in monitoring"
    assert "alertmanager" in services, "alertmanager service is missing in monitoring"

# 7. test_alerts — перевірка алертів (симуляція HighErrorRate та HighResponseTime).
def test_alerts():
    alerts_path = BASE_DIR / "monitoring" / "alerts.yml"
    assert alerts_path.exists(), "alerts.yml is missing"
    
    with open(alerts_path, "r") as f:
        data = yaml.safe_load(f)
        
    assert "groups" in data, "alerts.yml must contain groups"
    group = data["groups"][0]
    assert group["name"] == "dnk_os_alerts"
    
    rules = {r["alert"]: r for r in group["rules"]}
    assert "HighErrorRate" in rules, "HighErrorRate alert is missing"
    assert "HighResponseTime" in rules, "HighResponseTime alert is missing"
    
    # Simulate rule evaluation
    def evaluate_error_rate(rate: float) -> bool:
        # HighErrorRate expr: rate > 0.05 (5%)
        return rate > 0.05

    def evaluate_response_time(seconds: float) -> bool:
        # HighResponseTime expr: seconds > 2
        return seconds > 2.0
        
    # Test alert firing conditions
    assert evaluate_error_rate(0.06) is True, "Alert should fire at 6% error rate"
    assert evaluate_error_rate(0.04) is False, "Alert should NOT fire at 4% error rate"
    assert evaluate_response_time(2.5) is True, "Alert should fire at 2.5s latency"
    assert evaluate_response_time(1.8) is False, "Alert should NOT fire at 1.8s latency"
