# --- DNK-MRH-HEADER ---
# mrh_id: "tests/deployment/test_helm_chart.py"
# purpose: "Verification tests for Helm Chart templates, values files, and chart metadata"
# author: "DNK-e.com Maksym"
# license: "MIT"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import os
import yaml
import pytest

HELM_DIR = "deployments/helm/dnk-os"

def test_chart_yaml_validity():
    chart_path = os.path.join(HELM_DIR, "Chart.yaml")
    assert os.path.exists(chart_path)
    with open(chart_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert data.get("name") == "dnk-os"
    assert data.get("apiVersion") == "v2"
    assert "version" in data
    assert "appVersion" in data

def test_values_files_exist():
    for f_name in ["values.yaml", "values-staging.yaml", "values-prod.yaml"]:
        path = os.path.join(HELM_DIR, f_name)
        assert os.path.exists(path), f"Values file {f_name} must exist"
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            assert isinstance(data, dict), f"{f_name} must be a valid dictionary"

def test_templates_exist():
    templates_dir = os.path.join(HELM_DIR, "templates")
    assert os.path.exists(templates_dir)
    files = os.listdir(templates_dir)
    required = ["deployment-api.yaml", "deployment-web.yaml", "deployment-worker.yaml", "service-api.yaml", "service-web.yaml"]
    for req in required:
        assert req in files, f"Template {req} must exist in {templates_dir}"
