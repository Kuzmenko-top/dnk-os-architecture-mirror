# --- DNK-MRH-HEADER ---
# mrh_id: "tests_analytics_test_workspace_analytics_frontend"
# purpose: "Verification test suite for Workspace Analytics frontend hooks, components, and dashboard integration"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import pathlib
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]

def test_analytics_client_hook_exists():
    """Verify that analytics_client.ts exists and implements REST and WebSocket hooks."""
    client_path = ROOT / "apps/web/lib/api/analytics_client.ts"
    assert client_path.exists(), f"Missing analytics client file: {client_path}"

    content = client_path.read_text(encoding="utf-8")
    assert "useWorkspaceAnalytics" in content
    assert "useWorkspaceLiveMetrics" in content
    assert "WorkspaceMetrics" in content
    assert "LiveMetricsUpdate" in content
    assert "metrics_update" in content
    assert "/api/v1/analytics/workspaces/" in content
    assert "live" in content

def test_live_metrics_pulse_card():
    """Verify LiveMetricsPulseCard component structure and WebSocket connection indicators."""
    card_path = ROOT / "apps/web/components/analytics/LiveMetricsPulseCard.tsx"
    assert card_path.exists(), f"Missing LiveMetricsPulseCard at: {card_path}"

    content = card_path.read_text(encoding="utf-8")
    assert "useWorkspaceLiveMetrics" in content
    assert "Live Metrics" in content
    assert "CONNECTED" in content
    assert "activity_count" in content
    assert "avg_latency" in content
    assert "error_count" in content

def test_activity_timeline_chart():
    """Verify ActivityTimelineChart component structure and time range rendering."""
    chart_path = ROOT / "apps/web/components/analytics/ActivityTimelineChart.tsx"
    assert chart_path.exists(), f"Missing ActivityTimelineChart at: {chart_path}"

    content = chart_path.read_text(encoding="utf-8")
    assert "ActivityTimelineChart" in content
    assert "Activity Timeline" in content
    assert "timeRange" in content
    assert "activity" in content

def test_performance_percentiles_card():
    """Verify PerformancePercentilesCard component percentiles p50/p95/p99/avg layout."""
    card_path = ROOT / "apps/web/components/analytics/PerformancePercentilesCard.tsx"
    assert card_path.exists(), f"Missing PerformancePercentilesCard at: {card_path}"

    content = card_path.read_text(encoding="utf-8")
    assert "PerformancePercentilesCard" in content
    assert "Performance Percentiles" in content
    assert "p50" in content
    assert "p95" in content
    assert "p99" in content
    assert "avg" in content

def test_workspace_users_activity_table():
    """Verify WorkspaceUsersActivityTable component rendering team activity."""
    table_path = ROOT / "apps/web/components/analytics/WorkspaceUsersActivityTable.tsx"
    assert table_path.exists(), f"Missing WorkspaceUsersActivityTable at: {table_path}"

    content = table_path.read_text(encoding="utf-8")
    assert "WorkspaceUsersActivityTable" in content
    assert "Team Activity" in content

def test_workspace_errors_log():
    """Verify WorkspaceErrorsLog component structure and incident counters."""
    log_path = ROOT / "apps/web/components/analytics/WorkspaceErrorsLog.tsx"
    assert log_path.exists(), f"Missing WorkspaceErrorsLog at: {log_path}"

    content = log_path.read_text(encoding="utf-8")
    assert "WorkspaceErrorsLog" in content
    assert "Workspace Errors Log" in content

def test_analytics_dashboard_page():
    """Verify Analytics Page integrates all widgets into responsive grid layout."""
    page_path = ROOT / "apps/web/app/analytics/page.tsx"
    assert page_path.exists(), f"Missing Analytics Page at: {page_path}"

    content = page_path.read_text(encoding="utf-8")
    assert "useWorkspaceAnalytics" in content
    assert "LiveMetricsPulseCard" in content
    assert "ActivityTimelineChart" in content
    assert "PerformancePercentilesCard" in content
    assert "WorkspaceUsersActivityTable" in content
    assert "WorkspaceErrorsLog" in content
    assert "timeRange" in content
    assert "workspaceId" in content
