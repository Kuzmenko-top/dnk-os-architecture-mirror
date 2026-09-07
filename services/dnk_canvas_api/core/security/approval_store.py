# --- DNK-MRH-HEADER ---
# mrh_id: "approval_store.py"
# purpose: "Approval binding management for security gates"
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# author: "DNK-e.com Maksym"
# license: "MIT"
# --- END DNK-MRH-HEADER ---
"""Approval binding: run_id + action_name + SHA-256 args hash."""
import hashlib
import json
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .idempotency_key import generate_idempotency_key
from .models import SecurityApproval


class ApprovalBinding:
    """Manages approval binding for security gates."""
    
    TIMEOUT_SECONDS = 600  # 10 minutes
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def create_approval_request(
        self,
        run_id: UUID,
        agent_id: str,
        action_name: str,
        args: Dict[str, Any],
    ) -> UUID:
        """
        Create new approval request with binding.
        
        Features:
        - Generates args_hash (SHA-256 of sorted args JSON)
        - Generates idempotency_key (SHA-256 of run_id + action_name + args)
        - Idempotency: Returns existing approval_id if pending request exists
        - Timeout: timeout_at = created_at + 600 seconds
        
        Args:
            run_id: Current agent run identifier
            agent_id: Agent identifier
            action_name: Name of the action (e.g., "delete_canvas")
            args: Dictionary of action arguments
        
        Returns:
            approval_id (UUID) for tracking
        """
        # Generate args hash (SHA-256)
        args_json = json.dumps(args, sort_keys=True)
        args_hash = hashlib.sha256(args_json.encode('utf-8')).hexdigest()
        
        # Generate idempotency key
        idempotency_key = generate_idempotency_key(run_id, action_name, args)
        
        # Check for existing pending request (idempotency)
        existing = await self._find_pending_request(idempotency_key)
        if existing:
            return existing.id
        
        # Create new approval request
        timeout_at = datetime.utcnow() + timedelta(seconds=self.TIMEOUT_SECONDS)
        
        approval_id = uuid4()
        approval = SecurityApproval(
            id=approval_id,
            run_id=run_id,
            agent_id=agent_id,
            action_name=action_name,
            args_hash=args_hash,
            idempotency_key=idempotency_key,
            status='pending',
            timeout_at=timeout_at,
        )
        
        self.db.add(approval)
        await self.db.commit()
        
        return approval_id
    
    async def check_approval_status(self, approval_id: UUID) -> str:
        """
        Check approval status.
        
        Returns:
            'approved', 'rejected', 'timeout_rejected', or 'pending'
        """
        # Query approval from database
        stmt = select(SecurityApproval).where(SecurityApproval.id == approval_id)
        result = await self.db.execute(stmt)
        approval = result.scalar_one_or_none()
        
        if not approval:
            raise ValueError(f"Approval {approval_id} not found")
        
        # Check for timeout
        if approval.status == 'pending' and datetime.utcnow() > approval.timeout_at:
            # Update status to timeout_rejected
            approval.status = 'timeout_rejected'
            await self.db.commit()
            return 'timeout_rejected'
        
        return approval.status
    
    async def _find_pending_request(self, idempotency_key: str) -> Optional[SecurityApproval]:
        """Find existing pending request by idempotency key."""
        stmt = select(SecurityApproval).where(
            SecurityApproval.idempotency_key == idempotency_key,
            SecurityApproval.status == 'pending',
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
