# --- DNK-MRH-HEADER ---
# mrh_id: "core_adapters_security_gate_timeline_adapter"
# purpose: "Security Gate Timeline Adapter to record audit trails of security gate evaluations safely with exception isolation"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-08-11"
# --- END DNK-MRH-HEADER ---

import sys
from datetime import datetime, UTC
from uuid import UUID, uuid4
from typing import Optional

from core.models.timeline import Event
from core.ports.timeline_repository import ITimelineRepository

class SecurityGateTimelineAdapter:
    def __init__(self, timeline_repo: Optional[ITimelineRepository] = None):
        self.timeline_repo = timeline_repo

    async def log_decision(
        self,
        run_id: UUID,
        action: str,
        allowed: bool,
        reason: str,
    ) -> Optional[Event]:
        if not self.timeline_repo:
            return None
            
        try:
            event = Event(
                id=uuid4(),
                run_id=run_id,
                task_id=None,
                event_type="security_gate_evaluated",
                payload={
                    "run_id": str(run_id),
                    "action": action,
                    "allowed": allowed,
                    "reason": reason,
                },
                created_at=datetime.now(UTC)
            )
            return await self.timeline_repo.create_event(event)
        except Exception as e:
            # Safely catch all exceptions (such as ForeignKeyViolationError if run_id is not in DB)
            # to prevent background task crashes or leaking exceptions into pytest run loops.
            print(f"[AUDIT_LOG_ERROR] Failed to log security gate decision: {e}", file=sys.stderr)
            return None
