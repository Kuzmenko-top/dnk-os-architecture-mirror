# --- DNK-MRH-HEADER ---
# mrh_id: "tests_verification_test_agent_execution_resilience"
# purpose: "Regression suite verifying resilient agent execution, structured execution status, and graceful audit handling"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from apps.api.main import app
import core.flows.research_write_validate as rwv_module

client = TestClient(app)

def test_agent_run_success_with_db_unavailable():
    """Verify that agent run completes safely even when PostgreSQL is unreachable (no Broken pipe, structured degraded persistence)."""
    # Force pool creation to return None (DB unreachable)
    with patch.object(rwv_module, "get_or_create_pool", new_callable=AsyncMock) as mock_pool:
        mock_pool.return_value = None
        
        response = client.post("/api/agent/run", json={
            "canvas_id": "test-canvas-001",
            "query": "build analytics widget",
            "flow_type": "research_write_validate"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["execution_status"] == "completed"
        assert data["persistence_status"] == "degraded"
        assert data["audit_status"] == "deferred"
        assert "trace_id" in data
        assert "workflow_id" in data
        assert "Artifact for build analytics widget" in data["content"]

def test_agent_run_success_with_db_persisted():
    """Verify that agent run marks status as persisted when database pool succeeds."""
    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock(return_value=None)
    
    mock_acquire_ctx = MagicMock()
    mock_acquire_ctx.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_acquire_ctx.__aexit__ = AsyncMock(return_value=None)
    
    mock_pool_instance = MagicMock()
    mock_pool_instance._closed = False
    mock_pool_instance.acquire.return_value = mock_acquire_ctx
    
    with patch.object(rwv_module, "get_or_create_pool", new_callable=AsyncMock) as mock_pool, \
         patch("core.flows.research_write_validate.PostgresTimelineRepository") as mock_repo_cls:
        
        mock_pool.return_value = mock_pool_instance
        mock_repo = AsyncMock()
        mock_repo.create_event = AsyncMock(return_value=None)
        mock_repo_cls.return_value = mock_repo
        
        response = client.post("/api/agent/run", json={
            "canvas_id": "00000000-0000-0000-0000-000000000001",
            "query": "research and write docs",
            "flow_type": "research_write_validate"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["execution_status"] == "completed"
        assert data["persistence_status"] == "persisted"
        assert data["audit_status"] == "recorded"
        assert "trace_id" in data
        assert "workflow_id" in data

def test_agent_run_security_gate_denial():
    """Verify that Security Gate denial is caught and returned with clean structured audit error."""
    with patch("core.flows.research_write_validate.get_security_gate_service") as mock_gate_svc:
        mock_gate = MagicMock()
        mock_decision = MagicMock()
        mock_decision.allowed = False
        mock_decision.reason = "Content violates safety policy"
        mock_gate.evaluate_policy.return_value = mock_decision
        mock_gate_svc.return_value = mock_gate
        
        response = client.post("/api/agent/run", json={
            "canvas_id": "test-canvas-001",
            "query": "generate malicious content",
            "flow_type": "research_write_validate"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["execution_status"] == "failed"
        assert "Security Gate Denied" in data["error"]

def test_agent_run_unsupported_flow_type():
    """Verify that unsupported flow types return 400."""
    response = client.post("/api/agent/run", json={
        "canvas_id": "test-canvas-001",
        "flow_type": "unknown_invalid_flow"
    })
    assert response.status_code == 400
