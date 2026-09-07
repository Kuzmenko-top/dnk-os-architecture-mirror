# --- DNK-MRH-HEADER ---
# mrh_id: "tests/deployment/test_github_workflows.py"
# purpose: "Verification tests for GitHub Actions CI/CD workflows (.github/workflows/ci.yml and deploy.yml)"
# author: "DNK-e.com Maksym"
# license: "MIT"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import os
import yaml
import pytest

WORKFLOWS_DIR = ".github/workflows"

def test_ci_workflow():
    path = os.path.join(WORKFLOWS_DIR, "ci.yml")
    assert os.path.exists(path)
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert data.get("name") in ("Continuous Integration & Quality Gate", "CI Pipeline")
    jobs = data.get("jobs", {})
    assert any(k in jobs for k in ("quality-gate", "test"))

def test_deploy_workflow():
    path = os.path.join(WORKFLOWS_DIR, "deploy.yml")
    assert os.path.exists(path)
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert data.get("name") == "Production Deployment Pipeline"
    jobs = data.get("jobs", {})
    assert "test-and-verify" in jobs
    assert "build-and-push" in jobs
    assert "security-scan" in jobs
    assert "deploy-kubernetes" in jobs


def test_cd_workflow():
    path = os.path.join(WORKFLOWS_DIR, "cd.yml")
    assert os.path.exists(path)
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert "CD" in data.get("name", "")
    jobs = data.get("jobs", {})
    assert "build" in jobs
    assert "deploy" in jobs
    assert "healthcheck" in jobs


def test_security_scan_workflow():
    path = os.path.join(WORKFLOWS_DIR, "security_scan.yml")
    assert os.path.exists(path)
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert "Security" in data.get("name", "")
    jobs = data.get("jobs", {})
    assert "secrets" in jobs
    assert "dependencies" in jobs
    assert "codeql" in jobs
