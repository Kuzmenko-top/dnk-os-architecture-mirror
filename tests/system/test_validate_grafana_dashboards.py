# --- DNK-MRH-HEADER ---
# mrh_id: "tests_system_test_validate_grafana_dashboards"
# purpose: "Unit tests for Grafana dashboard JSON schema integrity validator"
# author: "DNK-e.com Maksym & Gerych Prime"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# --- END DNK-MRH-HEADER ---

import json
from pathlib import Path
import pytest

from scripts.system.validate_grafana_dashboards import validate_dashboard_file, main


def test_validate_valid_dashboard(tmp_path: Path):
    dash_file = tmp_path / "valid_dashboard.json"
    data = {
        "title": "Test Dashboard",
        "panels": [
            {
                "id": 1,
                "title": "Panel 1",
                "type": "stat",
                "targets": [{"expr": "up"}],
            }
        ],
    }
    dash_file.write_text(json.dumps(data), encoding="utf-8")

    valid, errors = validate_dashboard_file(dash_file)
    assert valid is True
    assert errors == []


def test_validate_invalid_dashboard(tmp_path: Path):
    dash_file = tmp_path / "invalid_dashboard.json"
    # Missing title and panels
    data = {"uid": "123"}
    dash_file.write_text(json.dumps(data), encoding="utf-8")

    valid, errors = validate_dashboard_file(dash_file)
    assert valid is False
    assert any("title" in e for e in errors)
    assert any("panels" in e for e in errors)


def test_validate_existing_repo_dashboards():
    repo_file = Path("monitoring/grafana_dashboards/dnk_os_dashboard.json")
    if repo_file.exists():
        valid, errors = validate_dashboard_file(repo_file)
        assert valid is True, f"Dashboard validation failed: {errors}"
