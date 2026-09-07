# --- DNK-MRH-HEADER ---
# mrh_id: "tests_workspace_test_workspace_postgres_persistence"
# purpose: "Integration and unit tests for PostgreSQL asyncpg connection pool, repositories, and workspace persistence layer"
# author: "DNK-e.com Maksym"
# license: "MIT"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from apps.api.db.database import DatabaseManager
from apps.api.repositories.workspace_repository import (
    WorkspaceRepository,
    WorkspacePromptRepository,
    WorkspaceDiffRepository,
    WorkspaceApprovalRepository,
    WorkspaceSnapshotRepository,
    WorkspaceCommitRepository,
    WorkspaceAuditRepository
)
from apps.api.services.workspace_service import WorkspaceService


@pytest.mark.asyncio
async def test_database_manager_pool_lifecycle():
    db = DatabaseManager(dsn="postgresql://dnk:dnk_password@localhost:5432/dnk_os")
    assert db.is_connected is False
    assert db.get_pool() is None

    # Mock asyncpg.create_pool
    mock_pool = MagicMock()
    mock_pool._closed = False
    mock_pool.close = AsyncMock()

    with patch("asyncpg.create_pool", new=AsyncMock(return_value=mock_pool)):
        pool = await db.connect(min_size=2, max_size=10, timeout=15.0)
        assert pool == mock_pool
        assert db.is_connected is True
        assert db.get_pool() == mock_pool

        await db.disconnect()
        mock_pool.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_workspace_repository_crud():
    mock_conn = AsyncMock()
    mock_pool = MagicMock()
    mock_pool._closed = False

    class MockAcquireContext:
        async def __aenter__(self):
            return mock_conn
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    mock_pool.acquire = MagicMock(return_value=MockAcquireContext())

    repo = WorkspaceRepository(pool=mock_pool)

    # Test get_workspace when workspace exists
    mock_conn.fetchrow.return_value = {
        "id": "ws_test_01",
        "tenant_id": "tenant_1",
        "name": "Test Workspace",
        "version": 3,
        "state": "ACTIVE",
        "last_active": datetime.now(timezone.utc),
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    mock_conn.fetch.side_effect = [
        [{"node_id": "n1", "type": "section", "label": "Hero", "file_path": "sections/hero.liquid", "data": None}],
        [{"source": "n1", "target": "n2", "type": "flow"}]
    ]

    ws = await repo.get_workspace("ws_test_01", "tenant_1")
    assert ws is not None
    assert ws["workspace_id"] == "ws_test_01"
    assert ws["tenant_id"] == "tenant_1"
    assert ws["metadata"]["version"] == 3
    assert len(ws["nodes"]) == 1
    assert len(ws["edges"]) == 1

    # Test update_workspace_version
    await repo.update_workspace_version("ws_test_01", 4)
    mock_conn.execute.assert_called()


@pytest.mark.asyncio
async def test_workspace_prompt_diff_approval_repositories():
    mock_conn = AsyncMock()
    mock_pool = MagicMock()
    mock_pool._closed = False

    class MockAcquireContext:
        async def __aenter__(self):
            return mock_conn
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    mock_pool.acquire = MagicMock(return_value=MockAcquireContext())

    prompt_repo = WorkspacePromptRepository(mock_pool)
    diff_repo = WorkspaceDiffRepository(mock_pool)
    approval_repo = WorkspaceApprovalRepository(mock_pool)

    # Prompt repo
    prompt_entry = {
        "prompt_id": "prm_100",
        "task_id": "task_100",
        "workspace_id": "ws_1",
        "tenant_id": "t_1",
        "user_id": "u_1",
        "prompt": "Add navigation banner",
        "target_node_id": None,
        "context_parameters": {},
        "status": "SUBMITTED"
    }
    await prompt_repo.save_prompt(prompt_entry)
    mock_conn.fetchrow.return_value = prompt_entry
    fetched_prompt = await prompt_repo.get_prompt("prm_100")
    assert fetched_prompt["prompt_id"] == "prm_100"

    # Diff repo
    diff_entry = {
        "diff_id": "diff_100",
        "task_id": "task_100",
        "workspace_id": "ws_1",
        "tenant_id": "t_1",
        "status": "STAGED",
        "staged_diff_hash": "hash_abc",
        "preview_hash": "prev_abc",
        "files": [{"file_path": "sections/nav.liquid", "staged_snippet": "+nav"}]
    }
    await diff_repo.save_diff(diff_entry)
    mock_conn.fetchrow.return_value = diff_entry
    fetched_diff = await diff_repo.get_diff("diff_100")
    assert fetched_diff["diff_id"] == "diff_100"

    # Approval repo
    approval_entry = {
        "approval_id": "appr_100",
        "workspace_id": "ws_1",
        "tenant_id": "t_1",
        "staged_diff_hash": "hash_abc",
        "summary": "Staged navigation update",
        "status": "PENDING",
        "approval_signature": "sig_123",
        "created_by": "u_1",
        "expires_at": 1800000000
    }
    await approval_repo.save_approval(approval_entry)
    mock_conn.fetchrow.return_value = approval_entry
    fetched_appr = await approval_repo.get_approval("appr_100")
    assert fetched_appr["approval_id"] == "appr_100"


@pytest.mark.asyncio
async def test_snapshot_commit_audit_repositories():
    mock_conn = AsyncMock()
    mock_pool = MagicMock()
    mock_pool._closed = False

    class MockAcquireContext:
        async def __aenter__(self):
            return mock_conn
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    mock_pool.acquire = MagicMock(return_value=MockAcquireContext())

    snap_repo = WorkspaceSnapshotRepository(mock_pool)
    commit_repo = WorkspaceCommitRepository(mock_pool)
    audit_repo = WorkspaceAuditRepository(mock_pool)

    # Snapshot repo
    snap_data = {
        "snapshot_id": "snap_100",
        "workspace_id": "ws_1",
        "tenant_id": "t_1",
        "pre_hash": "hash_xyz",
        "nodes_state": [],
        "edges_state": [],
        "version": 1,
        "created_by": "u_1"
    }
    await snap_repo.save_snapshot(snap_data)
    mock_conn.fetchrow.return_value = snap_data
    fetched_snap = await snap_repo.get_snapshot("snap_100")
    assert fetched_snap["snapshot_id"] == "snap_100"

    # Commit repo & Idempotency
    commit_data = {
        "commit_id": "commit_100",
        "workspace_id": "ws_1",
        "tenant_id": "t_1",
        "status": "COMMITTED",
        "new_version": 2,
        "diff_id": "diff_100",
        "idempotency_key": "idem_100"
    }
    await commit_repo.save_commit(commit_data)
    await commit_repo.save_idempotency("idem_100", "ws_1", "t_1", commit_data)
    mock_conn.fetchrow.return_value = {"response_data": commit_data}
    idem_res = await commit_repo.get_idempotency("idem_100")
    assert idem_res["commit_id"] == "commit_100"

    # Audit repo
    event_data = {
        "event_id": "evt_100",
        "workspace_id": "ws_1",
        "tenant_id": "t_1",
        "actor": "u_1",
        "action": "COMMIT_MUTATION",
        "details": {"version": 2}
    }
    await audit_repo.save_event(event_data)
    mock_conn.fetch.return_value = [{
        "event_id": "evt_100",
        "workspace_id": "ws_1",
        "tenant_id": "t_1",
        "actor": "u_1",
        "action": "COMMIT_MUTATION",
        "details": {"version": 2},
        "timestamp": datetime.now(timezone.utc)
    }]
    audit_trail = await audit_repo.get_audit_trail("ws_1", "t_1")
    assert len(audit_trail) == 1
    assert audit_trail[0]["action"] == "COMMIT_MUTATION"


def test_service_with_database_integration():
    service = WorkspaceService()
    # Test service methods operate with high integrity
    state = service.get_workspace_state("ws_alpha", "tenant_corp_a")
    assert state["workspace_id"] == "ws_alpha"
    assert state["metadata"]["version"] == 1

    prompt_res = service.submit_prompt(
        workspace_id="ws_alpha",
        tenant_id="tenant_corp_a",
        user_id="user_test",
        prompt="Integration test prompt"
    )
    assert prompt_res["status"] == "SUBMITTED"

    diff_res = service.stage_diff_preview(
        workspace_id="ws_alpha",
        tenant_id="tenant_corp_a",
        task_id=prompt_res["task_id"],
        files=[{"file_path": "sections/header.liquid", "staged_snippet": "header_v2"}]
    )
    assert diff_res["status"] == "STAGED"

    appr_res = service.create_approval_card(
        workspace_id="ws_alpha",
        tenant_id="tenant_corp_a",
        user_id="user_test",
        role="developer",
        staged_diff_hash=diff_res["staged_diff_hash"],
        summary="Update header section"
    )
    assert appr_res["status"] == "PENDING"
