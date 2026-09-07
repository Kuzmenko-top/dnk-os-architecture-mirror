# --- DNK-MRH-HEADER ---
# mrh_id: "tests/deployment/test_canvas_deployment.py"
# purpose: "Verification tests for docker-compose.canvas.yml and .github/workflows/canvas-ci.yml"
# author: "DNK-e.com Maksym"
# license: "MIT"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# --- END DNK-MRH-HEADER ---

import os
import yaml
import pytest

CANVAS_COMPOSE = "docker-compose.canvas.yml"
CANVAS_CI_WORKFLOW = ".github/workflows/canvas-ci.yml"

def test_canvas_compose_exists_and_valid():
    assert os.path.exists(CANVAS_COMPOSE), f"{CANVAS_COMPOSE} must exist"
    with open(CANVAS_COMPOSE, "r", encoding="utf-8") as f:
        content = f.read()
    assert "# --- DNK-MRH-HEADER ---" in content
    assert 'mrh_id: "docker-compose.canvas.yml"' in content
    assert "# --- END DNK-MRH-HEADER ---" in content

    data = yaml.safe_load(content)
    assert "services" in data
    services = data["services"]
    required_services = ["canvas-api", "canvas-worker", "canvas-web", "canvas-redis"]
    for svc in required_services:
        assert svc in services, f"Service '{svc}' must be configured in {CANVAS_COMPOSE}"

    # Verify resource limits on production services
    for svc in ["canvas-api", "canvas-worker", "canvas-web"]:
        assert "deploy" in services[svc], f"{svc} must have deploy configuration"
        assert "resources" in services[svc]["deploy"], f"{svc} must have resources configuration"
        assert "limits" in services[svc]["deploy"]["resources"], f"{svc} must have limits configuration"

    # Verify healthchecks
    for svc in ["canvas-api", "canvas-web", "canvas-redis"]:
        assert "healthcheck" in services[svc], f"{svc} must define a healthcheck"

def test_canvas_ci_workflow_exists_and_valid():
    assert os.path.exists(CANVAS_CI_WORKFLOW), f"{CANVAS_CI_WORKFLOW} must exist"
    with open(CANVAS_CI_WORKFLOW, "r", encoding="utf-8") as f:
        content = f.read()
    assert "# --- DNK-MRH-HEADER ---" in content
    assert 'mrh_id: ".github/workflows/canvas-ci.yml"' in content
    assert "# --- END DNK-MRH-HEADER ---" in content

    workflow = yaml.safe_load(content)
    assert "jobs" in workflow
    assert "test-canvas-backend" in workflow["jobs"]
    assert "test-canvas-frontend" in workflow["jobs"]
    assert "docker-build-and-verify" in workflow["jobs"]
