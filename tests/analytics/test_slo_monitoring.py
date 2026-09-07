# --- DNK-MRH-HEADER ---
# mrh_id: "tests_analytics_test_slo_monitoring"
# purpose: "Unit and integration tests for SLA/SLO Monitoring, Uptime, Error Budget, Burn Rate, and 24h Snapshots"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import pytest
from starlette.testclient import TestClient

from apps.api.main import app
from apps.api.services.auth_service import auth_service
from apps.api.services.slo_calculator import SLOCalculator, slo_calculator

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_slo_state():
    slo_calculator.clear()
    yield
    slo_calculator.clear()


def test_slo_uptime_calculation():
    calc = SLOCalculator(default_uptime_target_percent=99.90)

    # 10,000 total requests, 5 failed -> 99.95% uptime
    uptime = calc.calculate_uptime(total_requests=10000, failed_requests=5)
    assert uptime == 99.95

    # 10,000 total requests, 20 failed -> 99.80% uptime
    uptime_degraded = calc.calculate_uptime(total_requests=10000, failed_requests=20)
    assert uptime_degraded == 99.80


def test_error_budget_burn_rate():
    calc = SLOCalculator(default_uptime_target_percent=99.90)

    # Allowed error = 0.10%. If actual uptime is 99.95%, error is 0.05%
    budget_rem = calc.calculate_error_budget(uptime_percentage=99.95, uptime_target_percent=99.90)
    assert budget_rem == 0.50  # 50% remaining

    # Burn rate = 0.05 / 0.10 = 0.50
    burn_rate = calc.calculate_burn_rate(actual_error_pct=0.05, uptime_target_percent=99.90)
    assert burn_rate == 0.50

    # If actual uptime is 99.70% (error 0.30%), burn rate = 3.0
    burn_rate_high = calc.calculate_burn_rate(actual_error_pct=0.30, uptime_target_percent=99.90)
    assert burn_rate_high == 3.0


def test_slo_status_determination():
    calc = SLOCalculator(default_uptime_target_percent=99.90, default_latency_target_ms=200)

    # Meeting SLO
    status_ok = calc.determine_slo_status(
        uptime_percentage=99.98,
        uptime_target_percent=99.90,
        latency_p95_ms=120,
        latency_slo_target_ms=200,
        burn_rate=0.20,
        error_budget_remaining=0.80,
    )
    assert status_ok == "meeting"

    # Breached SLO (latency p95 > 200)
    status_breach = calc.determine_slo_status(
        uptime_percentage=99.95,
        uptime_target_percent=99.90,
        latency_p95_ms=250,
        latency_slo_target_ms=200,
        burn_rate=0.50,
        error_budget_remaining=0.50,
    )
    assert status_breach == "breached"


@pytest.mark.asyncio
async def test_slo_snapshot_generation_and_history():
    # Generate snapshot
    snapshot = await slo_calculator.generate_snapshot(
        workspace_id="ws_slo_snap",
        total_requests=20000,
        failed_requests=4,
        latency_p95_ms=160,
    )
    assert snapshot["uptime_percentage"] == 99.98
    assert snapshot["slo_status"] == "meeting"
    assert snapshot["latency_p95_ms"] == 160

    # Retrieve history
    history = await slo_calculator.get_history(workspace_id="ws_slo_snap")
    assert len(history) == 1
    assert history[0]["id"] == snapshot["id"]

    # Retrieve burn rate chart data
    chart = await slo_calculator.get_burn_rate_chart_data(workspace_id="ws_slo_snap", hours=24)
    assert len(chart) >= 1


def test_api_slo_status_and_history():
    token = auth_service.generate_test_token(
        user_id="usr_tester",
        tenant_id="tenant_y",
        workspace_id="ws_api_slo",
    )
    headers = {"Authorization": f"Bearer {token}"}

    # Status endpoint
    res_status = client.get("/api/v1/analytics/slo/status?workspace_id=ws_api_slo", headers=headers)
    assert res_status.status_code == 200
    data = res_status.json()
    assert "uptime_percentage" in data
    assert "error_budget_remaining" in data
    assert "burn_rate" in data

    # History endpoint
    res_hist = client.get("/api/v1/analytics/slo/history?workspace_id=ws_api_slo", headers=headers)
    assert res_hist.status_code == 200
    assert "snapshots" in res_hist.json()

    # Burn-rate endpoint
    res_burn = client.get("/api/v1/analytics/slo/burn-rate?workspace_id=ws_api_slo", headers=headers)
    assert res_burn.status_code == 200
    assert "burn_rate_chart" in res_burn.json()
