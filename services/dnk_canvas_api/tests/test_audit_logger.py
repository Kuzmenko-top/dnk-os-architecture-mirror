# --- DNK-MRH-HEADER ---
# mrh_id: "test_audit_logger.py"
# purpose: "Tests for audit logger: approved, rejected, timeout_rejected"
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# author: "DNK-e.com Maksym"
# license: "MIT"
# --- END DNK-MRH-HEADER ---
"""Tests for audit logger: approved, rejected, timeout_rejected."""
import asyncio
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from core.security.audit_logger import AuditLogger
from core.security.models import SecurityAuditLog


class TestAuditLogger:
    """Test audit logger functionality."""
    
    def test_log_approved(self):
        """Log approved event with approved_by + approved_at."""
        async def _test():
            mock_db = AsyncMock()
            logger = AuditLogger(mock_db)
            
            approval_id = uuid4()
            approved_by = "supervisor"
            
            await logger.log_approved(approval_id, approved_by)
            
            assert mock_db.execute.called
            assert mock_db.commit.called
            
            # Verify call args
            stmt = mock_db.execute.call_args[0][0]
            params = stmt.compile().params
            assert params['approval_id'] == approval_id
            assert params['event_type'] == 'approved'
            assert params['event_payload']['approved_by'] == approved_by
            assert 'approved_at' in params['event_payload']

        asyncio.run(_test())
    
    def test_log_rejected(self):
        """Log rejected event with rejected_by + reason."""
        async def _test():
            mock_db = AsyncMock()
            logger = AuditLogger(mock_db)
            
            approval_id = uuid4()
            rejected_by = "supervisor"
            reason = "Safety violation"
            
            await logger.log_rejected(approval_id, rejected_by, reason)
            
            assert mock_db.execute.called
            assert mock_db.commit.called
            
            stmt = mock_db.execute.call_args[0][0]
            params = stmt.compile().params
            assert params['approval_id'] == approval_id
            assert params['event_type'] == 'rejected'
            assert params['event_payload']['rejected_by'] == rejected_by
            assert params['event_payload']['reason'] == reason
            assert 'rejected_at' in params['event_payload']

        asyncio.run(_test())
    
    def test_log_timeout_rejected(self):
        """Log timeout_rejected event with timeout_at."""
        async def _test():
            mock_db = AsyncMock()
            logger = AuditLogger(mock_db)
            
            approval_id = uuid4()
            
            await logger.log_timeout_rejected(approval_id)
            
            assert mock_db.execute.called
            assert mock_db.commit.called
            
            stmt = mock_db.execute.call_args[0][0]
            params = stmt.compile().params
            assert params['approval_id'] == approval_id
            assert params['event_type'] == 'timeout_rejected'
            assert 'timeout_at' in params['event_payload']

        asyncio.run(_test())
    
    def test_log_approved_with_payload(self):
        """Log approved event with additional payload."""
        async def _test():
            mock_db = AsyncMock()
            logger = AuditLogger(mock_db)
            
            approval_id = uuid4()
            approved_by = "supervisor"
            payload = {"action_name": "delete_canvas", "canvas_id": "123"}
            
            await logger.log_approved(approval_id, approved_by, payload)
            
            assert mock_db.execute.called
            assert mock_db.commit.called
            
            stmt = mock_db.execute.call_args[0][0]
            params = stmt.compile().params
            assert params['approval_id'] == approval_id
            assert params['event_type'] == 'approved'
            assert params['event_payload']['approved_by'] == approved_by
            assert params['event_payload']['action_name'] == "delete_canvas"
            assert params['event_payload']['canvas_id'] == "123"

        asyncio.run(_test())
