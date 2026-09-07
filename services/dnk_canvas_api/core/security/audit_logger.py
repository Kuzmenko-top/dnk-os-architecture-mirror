# --- DNK-MRH-HEADER ---
# mrh_id: "audit_logger.py"
# purpose: "Audit Trail Log for security gates"
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# author: "DNK-e.com Maksym"
# license: "MIT"
# --- END DNK-MRH-HEADER ---
"""Audit Trail Log for security gates."""
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from .models import SecurityAuditLog


class AuditLogger:
    """Logs security gate events to audit trail."""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def log_approved(
        self,
        approval_id: UUID,
        approved_by: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log approval event.
        
        Args:
            approval_id: Approval request identifier
            approved_by: User/agent who approved
            payload: Additional context (optional)
        """
        event_payload = {
            'approved_by': approved_by,
            'approved_at': datetime.now(timezone.utc).isoformat(),
            **(payload or {}),
        }
        
        await self._log_event(
            approval_id=approval_id,
            event_type='approved',
            event_payload=event_payload,
        )
    
    async def log_rejected(
        self,
        approval_id: UUID,
        rejected_by: str,
        reason: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log rejection event.
        
        Args:
            approval_id: Approval request identifier
            rejected_by: User/agent who rejected
            reason: Rejection reason
            payload: Additional context (optional)
        """
        event_payload = {
            'rejected_by': rejected_by,
            'reason': reason,
            'rejected_at': datetime.now(timezone.utc).isoformat(),
            **(payload or {}),
        }
        
        await self._log_event(
            approval_id=approval_id,
            event_type='rejected',
            event_payload=event_payload,
        )
    
    async def log_timeout_rejected(
        self,
        approval_id: UUID,
        payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log timeout rejection event.
        
        Args:
            approval_id: Approval request identifier
            payload: Additional context (optional)
        """
        event_payload = {
            'timeout_at': datetime.now(timezone.utc).isoformat(),
            **(payload or {}),
        }
        
        await self._log_event(
            approval_id=approval_id,
            event_type='timeout_rejected',
            event_payload=event_payload,
        )
    
    async def _log_event(
        self,
        approval_id: UUID,
        event_type: str,
        event_payload: Dict[str, Any],
    ) -> None:
        """Internal method to log event to security_audit_logs table."""
        stmt = insert(SecurityAuditLog).values(
            id=uuid4(),
            approval_id=approval_id,
            event_type=event_type,
            event_payload=event_payload,
        )
        
        await self.db.execute(stmt)
        await self.db.commit()
