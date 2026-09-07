# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/db/models/batch_schedule_rule.py"
# purpose: "ORM Model representing recurring cron/interval scheduling rules for batch jobs."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class BatchScheduleRule(BaseModel):
    """Represents a scheduled batch execution policy (cron expression or interval)."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., description="Schedule title")
    job_template_name: str = Field(..., description="Target job handler or template")
    tenant_id: str = Field(default="ws-alpha-001")
    
    cron_expression: Optional[str] = Field(default=None, description="e.g. '0 * * * *'")
    interval_seconds: Optional[int] = Field(default=None, description="Interval in seconds if cron is not used")
    
    is_active: bool = Field(default=True)
    payload_template: Dict[str, Any] = Field(default_factory=dict)
    
    last_triggered_at: Optional[datetime] = Field(default=None)
    next_run_at: Optional[datetime] = Field(default=None)
    total_runs_count: int = Field(default=0)
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def mark_triggered(self) -> None:
        self.last_triggered_at = datetime.now(timezone.utc)
        self.total_runs_count += 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "job_template_name": self.job_template_name,
            "tenant_id": self.tenant_id,
            "cron_expression": self.cron_expression,
            "interval_seconds": self.interval_seconds,
            "is_active": self.is_active,
            "payload_template": self.payload_template,
            "last_triggered_at": self.last_triggered_at.isoformat() if self.last_triggered_at else None,
            "next_run_at": self.next_run_at.isoformat() if self.next_run_at else None,
            "total_runs_count": self.total_runs_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "metadata": self.metadata,
        }
