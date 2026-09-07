# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_monitoring_alerts"
# purpose: "Multi-Channel Alert Dispatcher & Rate-Limiter for Slack, Email, and Webhooks"
# author: "DNK-e.com Maksym & Gerych Prime"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# --- END DNK-MRH-HEADER ---

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import time
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

try:
    import httpx
except ImportError:
    httpx = None

from apps.api.monitoring.metrics import metrics_registry

logger = logging.getLogger("dnk.monitoring.alerts")


class AlertSeverity(str, Enum):
    """Severity classification for system alerts."""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class AlertNotification(BaseModel):
    """Payload representation of an alert dispatched to notification channels."""
    title: str
    message: str
    severity: AlertSeverity = AlertSeverity.WARNING
    service: str = "dnk_os"
    component: Optional[str] = "core"
    runbook_url: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def fingerprint(self) -> str:
        """Computes a unique signature for deduplication and throttling."""
        key = f"{self.service}:{self.component}:{self.severity}:{self.title}"
        return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


class AlertDispatchResult(BaseModel):
    """Result of dispatching an alert to an individual channel."""
    channel: str
    success: bool
    status_code: Optional[int] = None
    error: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class BaseAlertChannel(ABC):
    """Abstract interface for all notification channel dispatchers."""

    @abstractmethod
    async def send(self, alert: AlertNotification) -> AlertDispatchResult:
        """Dispatches notification to destination channel."""
        pass


class SlackAlertChannel(BaseAlertChannel):
    """Slack Incoming Webhook dispatcher supporting Block Kit layout."""

    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or os.getenv("SLACK_WEBHOOK_URL") or os.getenv("DNK_SLACK_WEBHOOK")

    async def send(self, alert: AlertNotification) -> AlertDispatchResult:
        if not self.webhook_url:
            logger.debug("Slack webhook URL not configured. Simulating dry-run alert: %s", alert.title)
            return AlertDispatchResult(
                channel="slack",
                success=True,
                status_code=200,
                error="dry_run_no_webhook_configured",
            )

        severity_colors = {
            AlertSeverity.INFO: "#36a64f",
            AlertSeverity.WARNING: "#ecaa38",
            AlertSeverity.ERROR: "#e01e5a",
            AlertSeverity.CRITICAL: "#7b001c",
        }
        color = severity_colors.get(alert.severity, "#439FE0")

        fields = [
            {"title": "Service", "value": alert.service, "short": True},
            {"title": "Component", "value": alert.component or "N/A", "short": True},
            {"title": "Severity", "value": alert.severity.value, "short": True},
            {"title": "Time (UTC)", "value": alert.timestamp, "short": True},
        ]

        if alert.runbook_url:
            fields.append({"title": "Runbook", "value": f"<{alert.runbook_url}|View Runbook>", "short": False})

        payload = {
            "attachments": [
                {
                    "fallback": f"[{alert.severity.value}] {alert.title}: {alert.message}",
                    "color": color,
                    "title": f"🚨 [{alert.severity.value}] {alert.title}",
                    "text": alert.message,
                    "fields": fields,
                    "footer": "DNK OS Monitoring & Alerting Engine",
                    "ts": int(time.time()),
                }
            ]
        }

        try:
            if httpx:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.post(self.webhook_url, json=payload)
                    success = resp.status_code in (200, 204)
                    return AlertDispatchResult(
                        channel="slack",
                        success=success,
                        status_code=resp.status_code,
                        error=None if success else f"HTTP {resp.status_code}: {resp.text}",
                    )
            else:
                return AlertDispatchResult(
                    channel="slack",
                    success=False,
                    error="httpx library not available for async HTTP request",
                )
        except Exception as exc:
            logger.error("Failed to send alert to Slack: %s", exc)
            return AlertDispatchResult(
                channel="slack",
                success=False,
                error=str(exc),
            )


class EmailAlertChannel(BaseAlertChannel):
    """SMTP Email dispatcher with plain-text and HTML formatting."""

    def __init__(
        self,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None,
        from_email: Optional[str] = None,
        to_email: Optional[str] = None,
    ):
        self.smtp_host = smtp_host or os.getenv("SMTP_HOST")
        self.smtp_port = int(smtp_port or os.getenv("SMTP_PORT", "587"))
        self.smtp_user = smtp_user or os.getenv("SMTP_USER")
        self.smtp_password = smtp_password or os.getenv("SMTP_PASSWORD")
        self.from_email = from_email or os.getenv("SMTP_FROM", "alerts@dnk-os.local")
        self.to_email = to_email or os.getenv("ALERT_EMAIL_TO")

    def _sync_send_mail(self, alert: AlertNotification) -> AlertDispatchResult:
        if not self.smtp_host or not self.to_email:
            logger.debug("SMTP host or recipient not configured. Simulating dry-run alert: %s", alert.title)
            return AlertDispatchResult(
                channel="email",
                success=True,
                status_code=250,
                error="dry_run_no_smtp_configured",
            )

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[{alert.severity.value}] {alert.title} - DNK OS"
        msg["From"] = self.from_email
        msg["To"] = self.to_email

        text_content = f"""
DNK OS ALERT NOTIFICATION
----------------------------------------
Severity:  {alert.severity.value}
Title:     {alert.title}
Service:   {alert.service}
Component: {alert.component}
Time:      {alert.timestamp}

Details:
{alert.message}

Metadata:
{json.dumps(alert.metadata, indent=2)}

Runbook: {alert.runbook_url or 'N/A'}
"""
        html_content = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.5; color: #333;">
    <h2 style="color: {'#d9534f' if alert.severity in (AlertSeverity.ERROR, AlertSeverity.CRITICAL) else '#f0ad4e'};">
        [{alert.severity.value}] {alert.title}
    </h2>
    <p><strong>Service:</strong> {alert.service} | <strong>Component:</strong> {alert.component}</p>
    <p><strong>Timestamp:</strong> {alert.timestamp}</p>
    <div style="background: #f8f9fa; border-left: 4px solid #007bff; padding: 12px; margin: 12px 0;">
        <pre style="white-space: pre-wrap; font-family: inherit;">{alert.message}</pre>
    </div>
    {f'<p><a href="{alert.runbook_url}" style="color: #0056b3;">View Incident Runbook</a></p>' if alert.runbook_url else ''}
</body>
</html>
"""
        msg.attach(MIMEText(text_content, "plain"))
        msg.attach(MIMEText(html_content, "html"))

        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
                server.starttls()
                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.from_email, [self.to_email], msg.as_string())
            return AlertDispatchResult(channel="email", success=True, status_code=250)
        except Exception as exc:
            logger.error("Failed sending email alert via SMTP: %s", exc)
            return AlertDispatchResult(channel="email", success=False, error=str(exc))

    async def send(self, alert: AlertNotification) -> AlertDispatchResult:
        return await asyncio.to_thread(self._sync_send_mail, alert)


class AlertManager:
    """
    Central Alert Router with rate-limiting, deduplication, and channel fan-out.
    """

    def __init__(self, throttle_cooldown_seconds: int = 300):
        self.throttle_cooldown = throttle_cooldown_seconds
        self._last_dispatched: Dict[str, float] = {}
        self.channels: Dict[str, BaseAlertChannel] = {
            "slack": SlackAlertChannel(),
            "email": EmailAlertChannel(),
        }

    def register_channel(self, name: str, channel: BaseAlertChannel) -> None:
        """Registers a custom alert notification channel."""
        self.channels[name] = channel

    def should_throttle(self, alert: AlertNotification) -> bool:
        """Determines if the given alert should be suppressed due to cooldown."""
        fp = alert.fingerprint
        now = time.time()
        last_time = self._last_dispatched.get(fp)

        # Do not throttle CRITICAL alerts
        if alert.severity == AlertSeverity.CRITICAL:
            self._last_dispatched[fp] = now
            return False

        if last_time and (now - last_time) < self.throttle_cooldown:
            return True

        self._last_dispatched[fp] = now
        return False

    async def dispatch(
        self,
        alert: AlertNotification,
        channels: Optional[List[str]] = None,
    ) -> List[AlertDispatchResult]:
        """
        Dispatches alert notification across specified or all registered channels.
        """
        if self.should_throttle(alert):
            logger.info("Throttling repeated alert: %s (fingerprint: %s)", alert.title, alert.fingerprint)
            return [
                AlertDispatchResult(
                    channel="all",
                    success=True,
                    error="throttled_cooldown_active",
                )
            ]

        target_channel_names = channels or list(self.channels.keys())
        tasks = []

        for ch_name in target_channel_names:
            ch = self.channels.get(ch_name)
            if ch:
                tasks.append((ch_name, ch.send(alert)))

        results: List[AlertDispatchResult] = []
        for ch_name, coro in tasks:
            try:
                res = await coro
                results.append(res)
                metrics_registry.record_alert_dispatched(
                    severity=alert.severity.value,
                    channel=ch_name,
                    success=res.success,
                )
            except Exception as exc:
                err_res = AlertDispatchResult(channel=ch_name, success=False, error=str(exc))
                results.append(err_res)
                metrics_registry.record_alert_dispatched(
                    severity=alert.severity.value,
                    channel=ch_name,
                    success=False,
                )

        return results


# Global singleton alert manager
alert_manager = AlertManager()
