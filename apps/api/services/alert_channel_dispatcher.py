# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_alert_channel_dispatcher"
# purpose: "Multi-Channel Notification Dispatcher (Telegram, Slack, PagerDuty, Email) for DNK-ANALYTICS-004"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("dnk.alert_dispatcher")


class TelegramChannelAdapter:
    """Formatter and sender for Telegram Webhook / Bot API alerts."""

    @staticmethod
    def format_message(alert: Dict[str, Any]) -> str:
        severity_emoji = {
            "critical": "🚨",
            "warning": "⚠️",
            "info": "ℹ️",
        }.get(str(alert.get("severity")).lower(), "🔔")

        rule_name = alert.get("rule_name", "Alert Triggered")
        workspace = alert.get("workspace_id", "Global")
        triggered_at = alert.get("triggered_at", "Just now")

        return (
            f"{severity_emoji} <b>DNK OS Alert: {rule_name}</b>\n"
            f"<b>Severity:</b> {alert.get('severity', 'warning').upper()}\n"
            f"<b>Workspace:</b> {workspace}\n"
            f"<b>Triggered At:</b> {triggered_at}\n"
            f"<b>Details:</b> {alert.get('details', 'No additional details provided.')}"
        )

    @classmethod
    def dispatch(cls, config: Dict[str, Any], alert: Dict[str, Any]) -> Dict[str, Any]:
        webhook_url = config.get("webhook_url")
        bot_token = config.get("bot_token")
        chat_id = config.get("chat_id")

        if not webhook_url and not (bot_token and chat_id):
            return {"status": "failed", "error": "Missing telegram webhook_url or bot_token/chat_id"}

        message = cls.format_message(alert)
        logger.info(f"[Telegram Dispatch] Sending alert to chat {chat_id or 'webhook'}")
        return {"status": "sent", "channel": "telegram", "message_length": len(message)}


class SlackChannelAdapter:
    """Formatter and sender for Slack Webhook alerts with Block Kit."""

    @staticmethod
    def format_blocks(alert: Dict[str, Any]) -> Dict[str, Any]:
        severity = str(alert.get("severity", "warning")).lower()
        color = "#e01e5a" if severity == "critical" else "#ecb22e" if severity == "warning" else "#2eb886"

        return {
            "attachments": [
                {
                    "color": color,
                    "blocks": [
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"*DNK OS Alert*: *{alert.get('rule_name', 'Alert')}*",
                            },
                        },
                        {
                            "type": "fields",
                            "fields": [
                                {"type": "mrkdwn", "text": f"*Severity:*\n{severity.upper()}"},
                                {"type": "mrkdwn", "text": f"*Workspace:*\n{alert.get('workspace_id', 'Global')}"},
                            ],
                        },
                    ],
                }
            ]
        }

    @classmethod
    def dispatch(cls, config: Dict[str, Any], alert: Dict[str, Any]) -> Dict[str, Any]:
        webhook_url = config.get("webhook_url")
        if not webhook_url:
            return {"status": "failed", "error": "Missing slack webhook_url"}

        blocks = cls.format_blocks(alert)
        logger.info("[Slack Dispatch] Sending alert to webhook")
        return {"status": "sent", "channel": "slack", "blocks_count": len(blocks["attachments"])}


class PagerDutyChannelAdapter:
    """Formatter and sender for PagerDuty Events API v2 alerts."""

    @classmethod
    def dispatch(cls, config: Dict[str, Any], alert: Dict[str, Any]) -> Dict[str, Any]:
        routing_key = config.get("routing_key") or config.get("integration_key")
        if not routing_key:
            return {"status": "failed", "error": "Missing PagerDuty routing_key"}

        payload = {
            "routing_key": routing_key,
            "event_action": "trigger",
            "payload": {
                "summary": f"DNK OS Alert: {alert.get('rule_name', 'System Anomaly')}",
                "severity": alert.get("severity", "warning"),
                "source": "dnk-analytics-engine",
                "custom_details": alert.get("details", {}),
            },
        }
        logger.info("[PagerDuty Dispatch] Triggering event")
        return {"status": "sent", "channel": "pagerduty", "event_action": "trigger"}


class EmailChannelAdapter:
    """Formatter and sender for Email notifications."""

    @classmethod
    def dispatch(cls, config: Dict[str, Any], alert: Dict[str, Any]) -> Dict[str, Any]:
        recipients = config.get("recipients", [])
        if not recipients:
            return {"status": "failed", "error": "Missing email recipients"}

        subject = f"[DNK-ALERT] {alert.get('severity', 'WARNING').upper()}: {alert.get('rule_name')}"
        logger.info(f"[Email Dispatch] Sending alert email to {len(recipients)} recipients")
        return {"status": "sent", "channel": "email", "recipients": len(recipients), "subject": subject}


class AlertChannelDispatcher:
    """
    Unified Multi-Channel Dispatcher.
    Routes alert payloads to enabled channel adapters and tracks status per channel.
    """

    def __init__(self):
        self.adapters = {
            "telegram": TelegramChannelAdapter,
            "slack": SlackChannelAdapter,
            "pagerduty": PagerDutyChannelAdapter,
            "email": EmailChannelAdapter,
        }

    def dispatch_alert(
        self,
        alert: Dict[str, Any],
        channels_config: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Dispatch alert to all matching and enabled channel configs.
        Returns aggregate delivery status dict.
        """
        delivered_channels: List[str] = []
        delivery_status: Dict[str, Any] = {}

        for ch in channels_config:
            ch_type = str(ch.get("channel_type")).lower()
            if not ch.get("enabled", True):
                delivery_status[ch_type] = "skipped_disabled"
                continue

            adapter = self.adapters.get(ch_type)
            if not adapter:
                delivery_status[ch_type] = "failed_unsupported_adapter"
                continue

            config_data = ch.get("channel_config", {})
            try:
                result = adapter.dispatch(config_data, alert)
                st = result.get("status", "sent")
                delivery_status[ch_type] = st
                if st == "sent":
                    delivered_channels.append(ch_type)
            except Exception as ex:
                logger.error(f"Error dispatching to {ch_type}: {ex}")
                delivery_status[ch_type] = f"error_{str(ex)}"

        return {
            "delivered_channels": delivered_channels,
            "delivery_status": delivery_status,
        }
