# --- DNK-MRH-HEADER ---
# mrh_id: "TEST-SWARM-HEALTH-DASHBOARD-PRIORITY4"
# purpose: "Comprehensive Integration Tests for Unified Swarm Health Dashboard (/api/v1/health/swarm & WebSocket)"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from core.orchestrator.swarm_health import SwarmHealthEngine

client = TestClient(app)


class TestSwarmHealthEngineUnit:
    """Unit tests for the underlying SwarmHealthEngine."""

    def test_engine_initialization(self):
        engine = SwarmHealthEngine()
        assert engine.hub_root.exists()
        assert engine.start_time > 0

    def test_workers_health_structure(self):
        engine = SwarmHealthEngine()
        workers_data = engine.get_workers_health(include_details=True)

        assert "total_workers" in workers_data
        assert workers_data["total_workers"] >= 14
        assert "ready_workers" in workers_data
        assert "busy_workers" in workers_data
        assert "workers" in workers_data
        assert len(workers_data["workers"]) >= 14

        # Verify Gerych Prime and key worker details
        agent_ids = [w["agent_id"] for w in workers_data["workers"]]
        assert "gerych_prime" in agent_ids
        assert "gerych_builder" in agent_ids
        assert "dnk_dev_fullstack" in agent_ids
        assert "dnk_shopify" in agent_ids
        assert "gerych_auditor" in agent_ids

        # Check badge and color enrichment
        prime_worker = next(w for w in workers_data["workers"] if w["agent_id"] == "gerych_prime")
        assert prime_worker["badge"] == "👑 Gerych Prime"
        assert prime_worker["hex"] == "#8B5CF6"
        assert prime_worker["canvas_color"] == "6"

    def test_workers_health_without_details(self):
        engine = SwarmHealthEngine()
        workers_data = engine.get_workers_health(include_details=False)

        assert workers_data["total_workers"] >= 14
        assert "workers" not in workers_data

    def test_sentinel_health_clean_state(self, tmp_path):
        engine = SwarmHealthEngine(hub_root=tmp_path)
        sentinel_data = engine.get_sentinel_health()

        assert sentinel_data["status"] == "clean"
        assert sentinel_data["active_alerts_count"] == 0
        assert sentinel_data["critical_alerts_count"] == 0
        assert sentinel_data["warning_alerts_count"] == 0
        assert sentinel_data["self_heal_plans_count"] == 0

    def test_sentinel_health_critical_alerts(self, tmp_path):
        data_dir = tmp_path / "data"
        data_dir.mkdir(parents=True)
        alerts_file = data_dir / "sentinel_alerts.json"

        alerts_content = {
            "updated_at": "2026-09-06T12:00:00Z",
            "alerts": [
                {
                    "type": "MEMORY_LEAK_ANOMALY",
                    "severity": "CRITICAL",
                    "title": "Critical memory pressure detected",
                },
                {
                    "type": "STALE_WORKER",
                    "severity": "WARNING",
                    "title": "Worker heartbeat delayed",
                },
            ],
        }
        alerts_file.write_text(json.dumps(alerts_content), encoding="utf-8")

        # Also create self-heal plan
        plans_dir = tmp_path / "docs" / "plans" / "self_heal"
        plans_dir.mkdir(parents=True)
        (plans_dir / "TASK-DNK-SELFHEAL-001.md").write_text("# Plan", encoding="utf-8")

        engine = SwarmHealthEngine(hub_root=tmp_path)
        sentinel_data = engine.get_sentinel_health()

        assert sentinel_data["status"] in ("critical", "alerts_active")
        assert sentinel_data["active_alerts_count"] == 2
        assert sentinel_data["critical_alerts_count"] == 1
        assert sentinel_data["warning_alerts_count"] == 1
        assert sentinel_data["self_heal_plans_count"] == 1

        # Overall health must be 'unhealthy' due to critical alert
        overall = engine.get_health_status()
        assert overall["overall_status"] == "unhealthy"

    def test_accounting_health_limits(self):
        engine = SwarmHealthEngine()

        # Normal spend limit
        acc_normal = engine.get_accounting_health(spend_limit_usd=1000.0)
        assert acc_normal["budget_status"] == "normal"
        assert acc_normal["spend_limit_usd"] == 1000.0

        # Exceeded spend limit
        acc_exceeded = engine.get_accounting_health(spend_limit_usd=0.000001)
        if acc_exceeded["total_cost_usd"] > 0:
            assert acc_exceeded["budget_status"] == "exceeded"

    def test_canvas_bridge_health(self):
        engine = SwarmHealthEngine()
        bridge_data = engine.get_canvas_bridge_health()

        assert "status" in bridge_data
        assert "active_connections" in bridge_data
        assert "subscribed_canvases_count" in bridge_data
        assert "total_events_broadcast" in bridge_data

    def test_system_metrics(self):
        engine = SwarmHealthEngine()
        metrics = engine.get_system_metrics()

        assert "uptime_seconds" in metrics
        assert metrics["uptime_seconds"] >= 0
        assert "python_version" in metrics


class TestSwarmHealthRestApi:
    """Tests for the REST API endpoints."""

    def test_get_api_v1_health_swarm(self):
        response = client.get("/api/v1/health/swarm")
        assert response.status_code == 200

        data = response.json()
        assert "overall_status" in data
        assert data["overall_status"] in ("healthy", "degraded", "unhealthy")
        assert "timestamp" in data
        assert "workspace_id" in data
        assert data["workspace_id"] == "ws-alpha-001"

        assert "active_workers" in data
        assert data["active_workers"]["total_workers"] >= 14
        assert len(data["active_workers"]["workers"]) >= 14

        assert "sentinel" in data
        assert "accounting" in data
        assert "canvas_bridge" in data
        assert "system_metrics" in data

    def test_get_health_swarm_root_alias(self):
        response = client.get("/health/swarm")
        assert response.status_code == 200
        data = response.json()
        assert data["workspace_id"] == "ws-alpha-001"
        assert "overall_status" in data

    def test_get_swarm_health_without_details(self):
        response = client.get("/api/v1/health/swarm?details=false")
        assert response.status_code == 200
        data = response.json()
        assert "workers" not in data["active_workers"]
        assert data["active_workers"]["total_workers"] >= 14

    def test_get_swarm_health_custom_workspace(self):
        response = client.get("/api/v1/health/swarm?workspace_id=ws-custom-999")
        assert response.status_code == 200
        data = response.json()
        assert data["workspace_id"] == "ws-custom-999"

    def test_post_api_v1_health_swarm_heal(self):
        response = client.post("/api/v1/health/swarm/heal", json={"alert_id": "all", "action": "test_heal"})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["action"] == "test_heal"
        assert "healed_alerts_count" in data


class TestSwarmHealthWebSocket:
    """Tests for the WebSocket streaming endpoint."""

    def test_websocket_swarm_health_lifecycle(self):
        with client.websocket_connect("/api/v1/health/swarm/ws") as ws:
            # 1. First message is immediate snapshot
            initial = ws.receive_json()
            assert initial["type"] == "SWARM_HEALTH_SNAPSHOT"
            assert "overall_status" in initial["data"]
            assert initial["data"]["active_workers"]["total_workers"] >= 14

            # 2. Ping / Pong
            ws.send_json({"action": "ping"})
            pong = ws.receive_json()
            assert pong["type"] == "PONG"
            assert "timestamp" in pong

            # 3. Explicit Refresh
            ws.send_json({"action": "refresh", "workspace_id": "ws-test-ws", "details": False})
            update = ws.receive_json()
            assert update["type"] == "SWARM_HEALTH_UPDATE"
            assert update["data"]["workspace_id"] == "ws-test-ws"
            assert "workers" not in update["data"]["active_workers"]

            # 4. Unknown action returns ERROR
            ws.send_json({"action": "invalid_command"})
            err = ws.receive_json()
            assert err["type"] == "ERROR"
            assert "Unknown action" in err["detail"]

    def test_websocket_auto_heal_action(self):
        with client.websocket_connect("/api/v1/health/swarm/ws") as ws:
            # Consume initial snapshot
            initial = ws.receive_json()
            assert initial["type"] == "SWARM_HEALTH_SNAPSHOT"

            # Send heal action
            ws.send_json({"action": "heal", "alert_id": "non_existent_alert_id"})
            heal_resp = ws.receive_json()
            assert heal_resp["type"] == "SWARM_HEAL_RESULT"
            assert heal_resp["result"]["success"] is True
            assert "data" in heal_resp
