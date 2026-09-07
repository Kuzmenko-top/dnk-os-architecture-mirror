# --- DNK-MRH-HEADER ---
# mrh_id: "test_security_gates.py"
# purpose: "Tests for security gate decorator: fail-closed, timeout, idempotency, audit trail"
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# author: "DNK-e.com Maksym"
# license: "MIT"
# --- END DNK-MRH-HEADER ---
"""Tests for security gates: fail-closed, timeout, idempotency."""
import asyncio
import pytest
from typing import Any
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4, UUID

from core.security.gates import security_gate
from core.security.approval_store import ApprovalBinding
from core.security.idempotency_key import generate_idempotency_key


class TestSecurityGates:
    """Test security gate decorator functionality."""

    def test_fail_closed_on_validation_error(self):
        """Fail-Closed: Validation error (e.g., missing params) -> PermissionError (action blocked)."""
        async def _test():
            @security_gate(level="high")
            async def delete_canvas(canvas_id: str, run_id: UUID, agent_id: str, db_session: Any):
                return "deleted"

            # Call without required params
            with pytest.raises(PermissionError) as exc_info:
                await delete_canvas(canvas_id="123")
            
            err_msg = str(exc_info.value)
            assert "Missing required security parameters" in err_msg or "Security gate failed" in err_msg

        asyncio.run(_test())

    def test_fail_closed_on_network_failure(self):
        """Fail-Closed: Network failure / DB exception -> PermissionError (action blocked)."""
        async def _test():
            mock_db = AsyncMock()
            
            @security_gate(level="high", poll_interval=0.01)
            async def delete_canvas(canvas_id: str, run_id: UUID, agent_id: str, db_session: Any):
                return "deleted"

            with patch.object(ApprovalBinding, "create_approval_request", side_effect=RuntimeError("DB Connection Error")):
                with pytest.raises(PermissionError) as exc_info:
                    await delete_canvas(
                        canvas_id="123",
                        run_id=uuid4(),
                        agent_id="test_agent",
                        db_session=mock_db,
                    )
                
                assert "Action blocked (fail-closed)" in str(exc_info.value)

        asyncio.run(_test())

    def test_timeout_rejection_no_auto_approve(self):
        """Timeout -> timeout_rejected (NEVER auto-approve)."""
        async def _test():
            mock_db = AsyncMock()
            run_id = uuid4()
            approval_id = uuid4()

            @security_gate(level="high", timeout_seconds=1, poll_interval=0.05)
            async def delete_canvas(canvas_id: str, run_id: UUID, agent_id: str, db_session: Any):
                return "deleted"

            with patch.object(ApprovalBinding, "create_approval_request", return_value=approval_id), \
                 patch.object(ApprovalBinding, "check_approval_status", return_value="pending"), \
                 patch("core.security.gates.AuditLogger") as mock_audit_cls:
                
                mock_audit = mock_audit_cls.return_value
                mock_audit.log_timeout_rejected = AsyncMock()

                with pytest.raises(PermissionError) as exc_info:
                    await delete_canvas(
                        canvas_id="123",
                        run_id=run_id,
                        agent_id="test_agent",
                        db_session=mock_db,
                    )

                assert "timed out after 1s" in str(exc_info.value)
                mock_audit.log_timeout_rejected.assert_called_once_with(approval_id=approval_id)

        asyncio.run(_test())

    def test_successful_execution_on_approved(self):
        """Action executes and return value is returned when status is approved."""
        async def _test():
            mock_db = AsyncMock()
            run_id = uuid4()
            approval_id = uuid4()

            @security_gate(level="high", poll_interval=0.01)
            async def delete_canvas(canvas_id: str, run_id: UUID, agent_id: str, db_session: Any):
                return f"canvas_{canvas_id}_deleted"

            with patch.object(ApprovalBinding, "create_approval_request", return_value=approval_id) as mock_create, \
                 patch.object(ApprovalBinding, "check_approval_status", return_value="approved"), \
                 patch("core.security.gates.AuditLogger") as mock_audit_cls:
                
                mock_audit = mock_audit_cls.return_value
                mock_audit.log_approved = AsyncMock()

                result = await delete_canvas(
                    canvas_id="canvas_99",
                    run_id=run_id,
                    agent_id="test_agent",
                    db_session=mock_db,
                )

                assert result == "canvas_canvas_99_deleted"
                mock_create.assert_called_once_with(
                    run_id=run_id,
                    agent_id="test_agent",
                    action_name="delete_canvas",
                    args={"canvas_id": "canvas_99"},
                )
                mock_audit.log_approved.assert_called_once_with(
                    approval_id=approval_id,
                    approved_by="supervisor",
                )

        asyncio.run(_test())

    def test_rejection_raises_permission_error(self):
        """Action raises PermissionError and logs rejection when status is rejected."""
        async def _test():
            mock_db = AsyncMock()
            run_id = uuid4()
            approval_id = uuid4()

            @security_gate(level="high", poll_interval=0.01)
            async def delete_canvas(canvas_id: str, run_id: UUID, agent_id: str, db_session: Any):
                return "deleted"

            with patch.object(ApprovalBinding, "create_approval_request", return_value=approval_id), \
                 patch.object(ApprovalBinding, "check_approval_status", return_value="rejected"), \
                 patch("core.security.gates.AuditLogger") as mock_audit_cls:
                
                mock_audit = mock_audit_cls.return_value
                mock_audit.log_rejected = AsyncMock()

                with pytest.raises(PermissionError) as exc_info:
                    await delete_canvas(
                        canvas_id="123",
                        run_id=run_id,
                        agent_id="test_agent",
                        db_session=mock_db,
                    )

                assert "rejected by supervisor" in str(exc_info.value)
                mock_audit.log_rejected.assert_called_once_with(
                    approval_id=approval_id,
                    rejected_by="supervisor",
                    reason="Manual rejection",
                )

        asyncio.run(_test())

    def test_approval_binding_run_id_action_hash(self):
        """Approval binding: run_id + action_name + SHA-256 args hash."""
        async def _test():
            mock_db = AsyncMock()
            run_id = uuid4()

            @security_gate(level="high", poll_interval=0.01)
            async def deploy_service(service_name: str, config: dict, run_id: UUID, agent_id: str, db_session: Any):
                return "deployed"

            with patch.object(ApprovalBinding, "create_approval_request", return_value=uuid4()) as mock_create, \
                 patch.object(ApprovalBinding, "check_approval_status", return_value="approved"), \
                 patch("core.security.gates.AuditLogger") as mock_audit_cls:
                
                mock_audit = mock_audit_cls.return_value
                mock_audit.log_approved = AsyncMock()

                await deploy_service(
                    service_name="api",
                    config={"env": "prod"},
                    run_id=run_id,
                    agent_id="deploy_agent",
                    db_session=mock_db,
                )

                mock_create.assert_called_once_with(
                    run_id=run_id,
                    agent_id="deploy_agent",
                    action_name="deploy_service",
                    args={"service_name": "api", "config": {"env": "prod"}},
                )

        asyncio.run(_test())

    def test_idempotency_key_prevents_duplicates(self):
        """Idempotency key prevents duplicate destructive actions."""
        run_id = str(uuid4())
        action_name = "delete_canvas"
        args = {"canvas_id": "123"}

        key1 = generate_idempotency_key(run_id, action_name, args)
        key2 = generate_idempotency_key(run_id, action_name, args)

        assert key1 == key2  # Same inputs -> same key
        assert len(key1) == 64  # SHA-256 hex

    def test_audit_trail_logs_all_states(self):
        """Audit trail logs approved/rejected/timeout_rejected."""
        async def _test():
            mock_db = AsyncMock()
            run_id = uuid4()

            @security_gate(level="high", timeout_seconds=1, poll_interval=0.01)
            async def sample_action(run_id: UUID, agent_id: str, db_session: Any):
                return "done"

            # Test Approved logging
            with patch.object(ApprovalBinding, "create_approval_request", return_value=uuid4()), \
                 patch.object(ApprovalBinding, "check_approval_status", return_value="approved"), \
                 patch("core.security.gates.AuditLogger") as mock_audit_cls:
                mock_audit = mock_audit_cls.return_value
                mock_audit.log_approved = AsyncMock()
                await sample_action(run_id=run_id, agent_id="agent1", db_session=mock_db)
                assert mock_audit.log_approved.called

            # Test Rejected logging
            with patch.object(ApprovalBinding, "create_approval_request", return_value=uuid4()), \
                 patch.object(ApprovalBinding, "check_approval_status", return_value="rejected"), \
                 patch("core.security.gates.AuditLogger") as mock_audit_cls:
                mock_audit = mock_audit_cls.return_value
                mock_audit.log_rejected = AsyncMock()
                with pytest.raises(PermissionError):
                    await sample_action(run_id=run_id, agent_id="agent1", db_session=mock_db)
                assert mock_audit.log_rejected.called

            # Test Timeout logging
            with patch.object(ApprovalBinding, "create_approval_request", return_value=uuid4()), \
                 patch.object(ApprovalBinding, "check_approval_status", return_value="pending"), \
                 patch("core.security.gates.AuditLogger") as mock_audit_cls:
                mock_audit = mock_audit_cls.return_value
                mock_audit.log_timeout_rejected = AsyncMock()
                with pytest.raises(PermissionError):
                    await sample_action(run_id=run_id, agent_id="agent1", db_session=mock_db)
                assert mock_audit.log_timeout_rejected.called

        asyncio.run(_test())
