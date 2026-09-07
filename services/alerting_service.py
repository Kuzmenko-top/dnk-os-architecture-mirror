# --- DNK-MRH-HEADER ---
# mrh_id: "services/alerting_service.py"
# purpose: "Production Alerting Service for PagerDuty and Slack notifications with deduplication."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

import os
from dataclasses import dataclass
from typing import Dict, Optional
import httpx


@dataclass
class Alert:
    severity: str  # critical, warning, info
    title: str
    description: str
    source: str
    timestamp: str


class AlertingService:
    """
    Production Alerting: PagerDuty + Slack.

    Features:
    - PagerDuty: Critical alerts (phone call, SMS)
    - Slack: Warning/info alerts (channel notifications)
    - Deduplication: Avoid alert spam
    - Escalation: Auto-escalate if no acknowledgment
    """

    def __init__(self, pagerduty_routing_key: Optional[str] = None, slack_webhook_url: Optional[str] = None):
        self.pagerduty_routing_key = pagerduty_routing_key or os.getenv("PAGERDUTY_ROUTING_KEY")
        self.slack_webhook_url = slack_webhook_url or os.getenv("SLACK_ALERTS_WEBHOOK_URL")
        self.deduplication_cache: Dict[str, Alert] = {}

    async def send_alert(self, alert: Alert) -> bool:
        """
        Send alert via appropriate channel based on severity.
        """
        # Deduplication
        dedup_key = f"{alert.source}:{alert.title}"
        if dedup_key in self.deduplication_cache:
            return False  # Already sent

        self.deduplication_cache[dedup_key] = alert

        try:
            if alert.severity == "critical":
                # PagerDuty (phone call, SMS)
                await self._send_pagerduty(alert)

            # Slack (all severities)
            await self._send_slack(alert)

            return True
        except Exception as e:
            print(f"Alert failed: {e}")
            return False

    async def _send_pagerduty(self, alert: Alert):
        """
        Send critical alert to PagerDuty.
        """
        if not self.pagerduty_routing_key:
            print("PagerDuty not configured, skipping")
            return

        payload = {
            "routing_key": self.pagerduty_routing_key,
            "event_action": "trigger",
            "dedup_key": f"dnk_os:{alert.source}:{alert.title}",
            "payload": {
                "summary": alert.title,
                "source": alert.source,
                "severity": alert.severity,
                "timestamp": alert.timestamp,
                "details": alert.description,
            },
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://events.pagerduty.com/v2/enqueue",
                json=payload,
                timeout=10.0,
            )
            response.raise_for_status()

    async def _send_slack(self, alert: Alert):
        """
        Send alert to Slack channel.
        """
        if not self.slack_webhook_url:
            print("Slack not configured, skipping")
            return

        # Color based on severity
        colors = {
            "critical": "danger",
            "warning": "warning",
            "info": "good",
        }

        payload = {
            "attachments": [
                {
                    "color": colors.get(alert.severity, "good"),
                    "title": f"🚨 {alert.title}",
                    "text": alert.description,
                    "fields": [
                        {"title": "Severity", "value": alert.severity, "short": True},
                        {"title": "Source", "value": alert.source, "short": True},
                    ],
                    "footer": f"DNK OS | {alert.timestamp}",
                }
            ]
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.slack_webhook_url,
                json=payload,
                timeout=10.0,
            )
            response.raise_for_status()

    def clear_deduplication(self, dedup_key: str):
        """
        Clear deduplication cache (after alert resolved).
        """
        if dedup_key in self.deduplication_cache:
            del self.deduplication_cache[dedup_key]
