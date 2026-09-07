# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_alert_dispatcher_service"
# purpose: "Multi-Channel Alert Dispatching & Rate Limiting (DNK-HEALTH-001 Phase 3)"
# author: "DNK-e.com Maksym & Gerych Prime"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import time
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional
from apps.api.db.models.alert_notification_log import AlertNotificationLog
from apps.api.db.models.system_incident import SystemIncident


class AlertDispatcherService:
    """Dispatches notifications across channels (Telegram, Slack, Webhooks, PagerDuty, Email) with rate limiting."""

    def __init__(self, default_cooldown_seconds: int = 300):
        self.default_cooldown = default_cooldown_seconds
        self._logs: Dict[str, AlertNotificationLog] = {}
        # (workspace_id, service_name, channel) -> timestamp of last dispatch
        self._last_dispatch_ts: Dict[tuple, float] = {}
        self._channel_handlers: Dict[str, Callable[[str, SystemIncident, Dict[str, Any]], Dict[str, Any]]] = {}

        self._register_default_channel_handlers()

    def _register_default_channel_handlers(self) -> None:
        """Registers default simulation senders for supported alert channels."""
        self._channel_handlers["TELEGRAM"] = self._send_telegram_mock
        self._channel_handlers["SLACK"] = self._send_slack_mock
        self._channel_handlers["WEBHOOK"] = self._send_webhook_mock
        self._channel_handlers["PAGERDUTY"] = self._send_pagerduty_mock
        self._channel_handlers["EMAIL"] = self._send_email_mock

    def register_channel_handler(
        self,
        channel: str,
        handler: Callable[[str, SystemIncident, Dict[str, Any]], Dict[str, Any]],
    ) -> None:
        """Registers a custom channel dispatcher."""
        self._channel_handlers[channel.upper()] = handler

    def _send_telegram_mock(self, channel: str, inc: SystemIncident, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "channel": "TELEGRAM",
            "message_id": 99881,
            "chat_id": payload.get("target", "@dnk_sre_alerts"),
            "status": "delivered",
        }

    def _send_slack_mock(self, channel: str, inc: SystemIncident, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "channel": "SLACK",
            "ts": f"{time.time():.6f}",
            "channel_id": payload.get("target", "#sre-alerts"),
            "status": "delivered",
        }

    def _send_webhook_mock(self, channel: str, inc: SystemIncident, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "channel": "WEBHOOK",
            "url": payload.get("target", "https://api.dnk.local/webhooks/alerts"),
            "http_status": 200,
            "status": "delivered",
        }

    def _send_pagerduty_mock(self, channel: str, inc: SystemIncident, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "channel": "PAGERDUTY",
            "dedup_key": f"pd_{inc.id}",
            "status": "triggered",
        }

    def _send_email_mock(self, channel: str, inc: SystemIncident, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "channel": "EMAIL",
            "recipient": payload.get("target", "sre-ops@dnk-e.com"),
            "status": "sent",
        }

    def dispatch_alert(
        self,
        incident: SystemIncident,
        channel: str = "WEBHOOK",
        target: Optional[str] = None,
        custom_payload: Optional[Dict[str, Any]] = None,
        force: bool = False,
    ) -> AlertNotificationLog:
        """Dispatches an incident alert to the specified channel."""
        ch_upper = channel.upper()
        now_epoch = time.time()
        now_dt = datetime.now(timezone.utc)
        log_id = f"anl_{uuid.uuid4().hex[:12]}"
        rate_key = (incident.workspace_id, incident.service_name, ch_upper)

        # Rate limiting check
        last_sent = self._last_dispatch_ts.get(rate_key, 0)
        if not force and (now_epoch - last_sent) < self.default_cooldown:
            log = AlertNotificationLog(
                id=log_id,
                workspace_id=incident.workspace_id,
                incident_id=incident.id,
                channel=ch_upper,
                recipient=target or "default",
                status="SUPPRESSED",
                payload={"reason": f"Rate limited: sent {(now_epoch - last_sent):.1f}s ago"},
                response_body={},
                dispatched_at=now_dt,
            )
            self._logs[log_id] = log
            return log

        handler = self._channel_handlers.get(ch_upper)
        if not handler:
            log = AlertNotificationLog(
                id=log_id,
                workspace_id=incident.workspace_id,
                incident_id=incident.id,
                channel=ch_upper,
                recipient=target or "unknown",
                status="FAILED",
                payload=custom_payload or {},
                response_body={"error": f"Unsupported channel: {channel}"},
                dispatched_at=now_dt,
            )
            self._logs[log_id] = log
            return log

        payload = {
            "incident_id": incident.id,
            "service_name": incident.service_name,
            "severity": incident.severity,
            "title": incident.title,
            "target": target,
            **(custom_payload or {}),
        }

        try:
            res = handler(ch_upper, incident, payload)
            self._last_dispatch_ts[rate_key] = now_epoch

            log = AlertNotificationLog(
                id=log_id,
                workspace_id=incident.workspace_id,
                incident_id=incident.id,
                channel=ch_upper,
                recipient=target or "configured_channel",
                status="SENT",
                payload=payload,
                response_body=res,
                dispatched_at=now_dt,
            )
        except Exception as exc:
            log = AlertNotificationLog(
                id=log_id,
                workspace_id=incident.workspace_id,
                incident_id=incident.id,
                channel=ch_upper,
                recipient=target or "configured_channel",
                status="FAILED",
                payload=payload,
                response_body={"error": str(exc)},
                dispatched_at=now_dt,
            )

        self._logs[log_id] = log
        return log

    def get_logs(
        self,
        workspace_id: Optional[str] = None,
        incident_id: Optional[str] = None,
    ) -> List[AlertNotificationLog]:
        """Returns notification audit logs filtered by workspace or incident."""
        logs = list(self._logs.values())
        if workspace_id:
            logs = [lg for lg in logs if lg.workspace_id == workspace_id]
        if incident_id:
            logs = [lg for lg in logs if lg.incident_id == incident_id]
        return logs
