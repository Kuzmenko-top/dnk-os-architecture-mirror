# --- DNK-MRH-HEADER ---
# mrh_id: "tests/deployment/test_docker_compose_prod.py"
# purpose: "Verification tests for docker-compose.prod.yml configuration, networks, and services"
# author: "DNK-e.com Maksym"
# license: "MIT"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import os
import yaml
import pytest

COMPOSE_FILE = "docker-compose.prod.yml"

@pytest.fixture
def compose_data():
    assert os.path.exists(COMPOSE_FILE), f"{COMPOSE_FILE} must exist"
    with open(COMPOSE_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def test_compose_has_mrh_header():
    with open(COMPOSE_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    assert "# --- DNK-MRH-HEADER ---" in content
    assert 'mrh_id: "docker-compose.prod.yml"' in content
    assert "# --- END DNK-MRH-HEADER ---" in content

def test_compose_required_services(compose_data):
    services = compose_data.get("services", {})
    required = ["api", "web", "worker", "db", "redis", "gateway", "prometheus", "grafana"]
    for svc in required:
        assert svc in services, f"Service '{svc}' must be defined in {COMPOSE_FILE}"

def test_compose_network_isolation(compose_data):
    networks = compose_data.get("networks", {})
    assert "dnk_frontend_net" in networks
    assert "dnk_backend_net" in networks
    assert "dnk_data_net" in networks

    # Check that database is on data net
    db_nets = compose_data["services"]["db"].get("networks", [])
    assert "dnk_data_net" in db_nets
    assert "dnk_frontend_net" not in db_nets, "Database must not be directly exposed to frontend network"

def test_compose_healthchecks(compose_data):
    services = compose_data.get("services", {})
    critical_services = ["api", "web", "db", "redis"]
    for svc in critical_services:
        assert "healthcheck" in services[svc], f"Service '{svc}' must have a healthcheck declared"

def test_compose_resource_limits(compose_data):
    services = compose_data.get("services", {})
    for svc in ["api", "web", "worker"]:
        deploy = services[svc].get("deploy", {})
        resources = deploy.get("resources", {})
        assert "limits" in resources, f"Service '{svc}' must have resource limits declared"
        assert "reservations" in resources, f"Service '{svc}' must have resource reservations declared"
