# --- DNK-MRH-HEADER ---
# mrh_id: "tests/core/test_approval_gate.py"
# purpose: "Test suite for DNKApprovalGate Human-in-the-Loop (HITL) gate"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-23"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

"""
Unit tests for DNKApprovalGate.
"""

import time
import pytest
from dnk_os.core.approval_gate import DNKApprovalGate, ApprovalStatus
from dnk_os.core.checkpointer import MemoryCheckpointer, SQLiteCheckpointer


class TestDNKApprovalGate:
    """Test suite for DNKApprovalGate."""

    def test_init_default(self):
        """Test initialization with default parameters."""
        gate = DNKApprovalGate()
        assert gate is not None
        assert gate.timeout_seconds == 300
        assert isinstance(gate.checkpointer, MemoryCheckpointer)

    def test_init_custom_checkpointer(self, tmp_path):
        """Test initialization with custom SQLite checkpointer."""
        db_path = str(tmp_path / "approval_test.db")
        sqlite_cp = SQLiteCheckpointer(db_path=db_path)
        gate = DNKApprovalGate(checkpointer=sqlite_cp, timeout_seconds=60)
        assert gate.checkpointer == sqlite_cp
        assert gate.timeout_seconds == 60

    def test_request_approval(self):
        """Test approval request creation."""
        gate = DNKApprovalGate()
        request_id = gate.request_approval(
            action="delete_agent",
            context={"agent_name": "Герич"},
            thread_id="thread_1",
            approver_id="admin"
        )
        assert request_id is not None
        assert request_id.startswith("req_")

    def test_get_approval_status(self):
        """Test approval status retrieval."""
        gate = DNKApprovalGate()
        request_id = gate.request_approval(
            action="delete_agent",
            context={"agent_name": "Герич"},
            thread_id="thread_1"
        )
        status = gate.get_approval_status(request_id=request_id, thread_id="thread_1")
        assert status == ApprovalStatus.PENDING

    def test_get_approval_status_from_checkpointer(self):
        """Test approval status retrieved from checkpointer when not in local memory."""
        gate = DNKApprovalGate()
        request_id = gate.request_approval(
            action="delete_agent",
            context={"agent_name": "Герич"},
            thread_id="thread_1"
        )
        # Clear in-memory dict
        gate._requests.clear()
        status = gate.get_approval_status(request_id=request_id, thread_id="thread_1")
        assert status == ApprovalStatus.PENDING

    def test_get_approval_status_nonexistent(self):
        """Test approval status for unknown request."""
        gate = DNKApprovalGate()
        status = gate.get_approval_status(request_id="nonexistent", thread_id="thread_1")
        assert status == ApprovalStatus.REJECTED

    def test_approve(self):
        """Test approval flow."""
        gate = DNKApprovalGate()
        request_id = gate.request_approval(
            action="delete_agent",
            context={"agent_name": "Герич"},
            thread_id="thread_1"
        )
        result = gate.approve(
            request_id=request_id,
            thread_id="thread_1",
            approver_id="admin",
            comments="Approved for migration"
        )
        assert result is True
        status = gate.get_approval_status(request_id=request_id, thread_id="thread_1")
        assert status == ApprovalStatus.APPROVED

    def test_approve_from_checkpointer(self):
        """Test approve retrieves from checkpointer when not in local memory."""
        gate = DNKApprovalGate()
        request_id = gate.request_approval(
            action="delete_agent",
            context={"agent_name": "Герич"},
            thread_id="thread_1"
        )
        gate._requests.clear()
        res = gate.approve(request_id=request_id, thread_id="thread_1", approver_id="admin")
        assert res is True
        assert gate.get_approval_status(request_id=request_id, thread_id="thread_1") == ApprovalStatus.APPROVED

    def test_reject_from_checkpointer(self):
        """Test reject retrieves from checkpointer when not in local memory."""
        gate = DNKApprovalGate()
        request_id = gate.request_approval(
            action="delete_agent",
            context={"agent_name": "Герич"},
            thread_id="thread_1"
        )
        gate._requests.clear()
        res = gate.reject(request_id=request_id, thread_id="thread_1", approver_id="admin", reason="no")
        assert res is True
        assert gate.get_approval_status(request_id=request_id, thread_id="thread_1") == ApprovalStatus.REJECTED

    def test_approve_nonexistent(self):
        """Test approve with nonexistent request."""
        gate = DNKApprovalGate()
        result = gate.approve(
            request_id="nonexistent",
            thread_id="thread_1",
            approver_id="admin"
        )
        assert result is False

    def test_reject(self):
        """Test rejection flow."""
        gate = DNKApprovalGate()
        request_id = gate.request_approval(
            action="delete_agent",
            context={"agent_name": "Герич"},
            thread_id="thread_1"
        )
        result = gate.reject(
            request_id=request_id,
            thread_id="thread_1",
            approver_id="admin",
            reason="Operation unsafe"
        )
        assert result is True
        status = gate.get_approval_status(request_id=request_id, thread_id="thread_1")
        assert status == ApprovalStatus.REJECTED

    def test_reject_nonexistent(self):
        """Test reject with nonexistent request."""
        gate = DNKApprovalGate()
        result = gate.reject(
            request_id="nonexistent",
            thread_id="thread_1",
            approver_id="admin"
        )
        assert result is False

    def test_timeout_in_get_status(self):
        """Test automatic timeout detection on get_approval_status."""
        gate = DNKApprovalGate(timeout_seconds=0)
        request_id = gate.request_approval(
            action="deploy",
            context={"target": "prod"},
            thread_id="thread_1"
        )
        time.sleep(0.01)
        status = gate.get_approval_status(request_id=request_id, thread_id="thread_1", timeout_seconds=0)
        assert status == ApprovalStatus.TIMEOUT

    def test_wait_for_approval_timeout(self):
        """Test wait_for_approval timing out."""
        gate = DNKApprovalGate(timeout_seconds=1)
        request_id = gate.request_approval(
            action="deploy",
            context={"target": "prod"},
            thread_id="thread_1"
        )
        status = gate.wait_for_approval(
            request_id=request_id,
            thread_id="thread_1",
            poll_interval=0.01,
            timeout_seconds=0.05
        )
        assert status == ApprovalStatus.TIMEOUT

    def test_wait_for_approval_approved(self):
        """Test wait_for_approval when approved."""
        gate = DNKApprovalGate()
        request_id = gate.request_approval(
            action="deploy",
            context={"target": "prod"},
            thread_id="thread_1"
        )
        gate.approve(request_id=request_id, thread_id="thread_1", approver_id="admin")
        status = gate.wait_for_approval(request_id=request_id, thread_id="thread_1")
        assert status == ApprovalStatus.APPROVED

    def test_get_pending_requests(self):
        """Test pending requests listing with and without thread filter."""
        gate = DNKApprovalGate()
        req1 = gate.request_approval(action="action1", context={}, thread_id="thread_1")
        req2 = gate.request_approval(action="action2", context={}, thread_id="thread_2")
        gate.request_approval(action="action3", context={}, thread_id="thread_1")
        
        # Approve one request
        gate.approve(request_id=req1, thread_id="thread_1", approver_id="admin")
        
        all_pending = gate.get_pending_requests()
        assert len(all_pending) == 2
        
        thread1_pending = gate.get_pending_requests(thread_id="thread_1")
        assert len(thread1_pending) == 1
        assert thread1_pending[0]["action"] == "action3"

    def test_get_audit_log(self):
        """Test audit log retrieval and filtering."""
        gate = DNKApprovalGate()
        request_id = gate.request_approval(action="delete_agent", context={}, thread_id="thread_1")
        gate.approve(request_id=request_id, thread_id="thread_1", approver_id="admin")
        gate.request_approval(action="other_action", context={}, thread_id="thread_2")
        
        audit_all = gate.get_audit_log(limit=50)
        assert len(audit_all) == 3
        
        audit_thread1 = gate.get_audit_log(thread_id="thread_1")
        assert len(audit_thread1) == 2

    def test_execute_with_approval_auto(self):
        """Test execute with auto-approval."""
        gate = DNKApprovalGate()

        def dummy_action():
            return {"result": "success"}

        result = gate.execute_with_approval(
            action="safe_action",
            action_function=dummy_action,
            context={},
            thread_id="thread_1",
            auto_approve_actions=["safe_action"]
        )
        assert result["status"] == "success"
        assert result["approval_status"] == ApprovalStatus.APPROVED
        assert result["output"] == {"result": "success"}

    def test_execute_with_approval_manual_pending(self):
        """Test execute with manual approval in non-blocking mode."""
        gate = DNKApprovalGate()

        def dummy_action():
            return {"result": "success"}

        result = gate.execute_with_approval(
            action="delete_agent",
            action_function=dummy_action,
            context={},
            thread_id="thread_1",
            auto_approve_actions=[]
        )
        assert result["status"] == "pending_approval"
        assert result["approval_status"] == ApprovalStatus.PENDING
        assert result["output"] is None

    def test_execute_with_approval_blocking_approved(self):
        """Test execute with approval in blocking mode when approved."""
        gate = DNKApprovalGate()

        def dummy_action():
            return {"result": "executed"}

        # Request approval beforehand and approve
        req_id = gate.request_approval(action="deploy", context={}, thread_id="thread_1", request_id="custom_req_1")
        gate.approve(request_id=req_id, thread_id="thread_1", approver_id="admin")

        result = gate.execute_with_approval(
            action="deploy",
            action_function=dummy_action,
            context={},
            thread_id="thread_1",
            request_id="custom_req_1",
            blocking=True
        )
        assert result["status"] == "success"
        assert result["approval_status"] == ApprovalStatus.APPROVED
        assert result["output"] == {"result": "executed"}

    def test_execute_with_approval_blocking_rejected(self):
        """Test execute with approval in blocking mode when rejected."""
        gate = DNKApprovalGate()

        def dummy_action():
            return {"result": "executed"}

        req_id = gate.request_approval(action="deploy", context={}, thread_id="thread_1", request_id="custom_req_2")
        gate.reject(request_id=req_id, thread_id="thread_1", approver_id="admin", reason="denied")

        result = gate.execute_with_approval(
            action="deploy",
            action_function=dummy_action,
            context={},
            thread_id="thread_1",
            request_id="custom_req_2",
            blocking=True
        )
        assert result["status"] == "blocked"
        assert result["approval_status"] == ApprovalStatus.REJECTED
        assert result["output"] is None
