# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_alert_notification_log"
# purpose: "ORM Model for Alert Notification Audit Trail (DNK-HEALTH-001 Phase 1)"
# author: "DNK-e.com Maksym & Gerych Prime"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import uuid
from datetime import datetime, timezone
from typing import Any, Dict
from sqlalchemy import Column, String, DateTime, JSON
from apps.api.db.models.workspace import Base


class AlertNotificationLog(Base):
    __tablename__ = "alert_notification_logs"

    id = Column(String(64), primary_key=True, default=lambda: f"anl_{uuid.uuid4().hex[:12]}")
    workspace_id = Column(String(64), nullable=False, default="ws-default", index=True)
    incident_id = Column(String(64), nullable=True, index=True)
    channel = Column(String(64), nullable=False)  # telegram, webhook, email, slack, pagerduty
    recipient = Column(String(255), nullable=False)
    status = Column(String(32), default="SENT")  # SENT, DELIVERED, FAILED
    payload = Column(JSON, default=dict)
    response_body = Column(JSON, default=dict)
    dispatched_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id or f"anl_{uuid.uuid4().hex[:12]}",
            "workspace_id": self.workspace_id or "ws-default",
            "incident_id": self.incident_id,
            "channel": self.channel,
            "recipient": self.recipient,
            "status": self.status or "SENT",
            "payload": self.payload or {},
            "response_body": self.response_body or {},
            "dispatched_at": self.dispatched_at.isoformat() if self.dispatched_at else datetime.now(timezone.utc).isoformat(),
        }
