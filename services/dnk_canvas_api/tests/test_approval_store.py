# --- DNK-MRH-HEADER ---
# mrh_id: "test_approval_store.py"
# purpose: "Tests for approval store: idempotency, timeout, and binding"
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# author: "DNK-e.com Maksym"
# license: "MIT"
# --- END DNK-MRH-HEADER ---
"""Tests for approval store: idempotency, timeout, binding."""
import asyncio
import hashlib
import json
import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from core.security.approval_store import ApprovalBinding
from core.security.models import SecurityApproval


class MockDB:
    """In-memory mock session for SQLAlchemy AsyncSession."""
    
    def __init__(self):
        self.store = {}
    
    def add(self, obj):
        self.store[obj.id] = obj
        
    async def commit(self):
        pass
        
    async def execute(self, stmt):
        class MockResult:
            def __init__(self, val):
                self._val = val
            def scalar_one_or_none(self):
                return self._val
        
        params = stmt.compile().params
        if "idempotency_key_1" in params:
            key = params["idempotency_key_1"]
            match = None
            for item in self.store.values():
                if item.idempotency_key == key and item.status == "pending":
                    match = item
                    break
            return MockResult(match)
        
        if "id_1" in params:
            id_val = params["id_1"]
            match = self.store.get(id_val)
            return MockResult(match)
            
        return MockResult(None)


class TestApprovalBinding:
    """Test approval binding functionality."""
    
    def test_create_approval_request_generates_hash_and_key(self):
        """Create approval request generates args_hash + idempotency_key."""
        async def _test():
            db = MockDB()
            binding = ApprovalBinding(db)
            
            run_id = uuid4()
            agent_id = "agent_123"
            action_name = "delete_canvas"
            args = {"canvas_id": "c-999", "force": True}
            
            approval_id = await binding.create_approval_request(
                run_id=run_id,
                agent_id=agent_id,
                action_name=action_name,
                args=args,
            )
            
            assert approval_id in db.store
            approval = db.store[approval_id]
            
            expected_args_json = json.dumps(args, sort_keys=True)
            expected_args_hash = hashlib.sha256(expected_args_json.encode("utf-8")).hexdigest()
            
            assert approval.args_hash == expected_args_hash
            assert approval.agent_id == agent_id
            assert approval.action_name == action_name
            assert approval.status == "pending"
            assert len(approval.idempotency_key) == 64
            assert approval.timeout_at > datetime.utcnow()

        asyncio.run(_test())
    
    def test_idempotency_returns_existing_approval(self):
        """Idempotency: Same run_id + action_name + args → same approval_id."""
        async def _test():
            db = MockDB()
            binding = ApprovalBinding(db)
            
            run_id = uuid4()
            agent_id = "agent_123"
            action_name = "delete_canvas"
            args = {"canvas_id": "c-999"}
            
            approval_id_1 = await binding.create_approval_request(
                run_id=run_id,
                agent_id=agent_id,
                action_name=action_name,
                args=args,
            )
            
            approval_id_2 = await binding.create_approval_request(
                run_id=run_id,
                agent_id=agent_id,
                action_name=action_name,
                args=args,
            )
            
            assert approval_id_1 == approval_id_2
            assert len(db.store) == 1

        asyncio.run(_test())
    
    def test_check_approval_status_pending(self):
        """Check status: pending → 'pending'."""
        async def _test():
            db = MockDB()
            binding = ApprovalBinding(db)
            
            run_id = uuid4()
            approval_id = await binding.create_approval_request(
                run_id=run_id,
                agent_id="agent_1",
                action_name="archive_repo",
                args={"repo": "main"},
            )
            
            status = await binding.check_approval_status(approval_id)
            assert status == "pending"

        asyncio.run(_test())
    
    def test_check_approval_status_timeout_rejected(self):
        """Check status: timeout_at < now → 'timeout_rejected'."""
        async def _test():
            db = MockDB()
            binding = ApprovalBinding(db)
            
            run_id = uuid4()
            approval_id = await binding.create_approval_request(
                run_id=run_id,
                agent_id="agent_1",
                action_name="drop_table",
                args={"table": "users"},
            )
            
            # Simulate timeout by setting timeout_at in the past
            db.store[approval_id].timeout_at = datetime.utcnow() - timedelta(seconds=1)
            
            status = await binding.check_approval_status(approval_id)
            assert status == "timeout_rejected"
            assert db.store[approval_id].status == "timeout_rejected"

        asyncio.run(_test())
    
    def test_check_approval_status_not_found(self):
        """Check status: invalid approval_id → ValueError."""
        async def _test():
            db = MockDB()
            binding = ApprovalBinding(db)
            
            invalid_id = uuid4()
            with pytest.raises(ValueError) as exc_info:
                await binding.check_approval_status(invalid_id)
            
            assert f"Approval {invalid_id} not found" in str(exc_info.value)

        asyncio.run(_test())
    
    def test_check_approval_status_approved(self):
        """Check status: approved → 'approved'."""
        async def _test():
            db = MockDB()
            binding = ApprovalBinding(db)
            
            run_id = uuid4()
            approval_id = await binding.create_approval_request(
                run_id=run_id,
                agent_id="agent_1",
                action_name="reset_database",
                args={"env": "staging"},
            )
            
            # Manually approve
            db.store[approval_id].status = "approved"
            
            status = await binding.check_approval_status(approval_id)
            assert status == "approved"

        asyncio.run(_test())
