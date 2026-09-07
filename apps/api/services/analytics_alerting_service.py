# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_analytics_alerting_service"
# purpose: "Alerting Engine supporting threshold evaluation, composite AND/OR logic, rate limiting, and webhook dispatching"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import asyncio
import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional, Union
import httpx


class OperatorEvaluator:
    """Evaluates mathematical comparisons between metric values and thresholds."""

    @staticmethod
    def evaluate(operator: str, value: float, threshold: float) -> bool:
        op = operator.lower().strip()
        if op in ("gt", ">"):
            return value > threshold
        elif op in ("gte", ">="):
            return value >= threshold
        elif op in ("lt", "<"):
            return value < threshold
        elif op in ("lte", "<="):
            return value <= threshold
        elif op in ("eq", "=="):
            return abs(value - threshold) < 1e-6
        elif op in ("neq", "!="):
            return abs(value - threshold) >= 1e-6
        raise ValueError(f"Unsupported operator: {operator}")


class AnalyticsAlertingService:
    """Core Alerting Service managing alert rules, composite evaluators, rate limiting, audit logs, and dispatching."""

    def __init__(self, webhook_timeout: float = 5.0):
        self._rules: Dict[str, Dict[str, Any]] = {}
        self._events: List[Dict[str, Any]] = []
        self._last_triggered: Dict[str, datetime] = {}  # rule_id -> last trigger time (cooldown)
        self._listeners: List[Callable[[Dict[str, Any]], Any]] = []
        self.webhook_timeout = webhook_timeout

    def add_listener(self, listener: Callable[[Dict[str, Any]], Any]):
        """Register a real-time listener callback (e.g., for WebSocket streaming)."""
        if listener not in self._listeners:
            self._listeners.append(listener)

    def remove_listener(self, listener: Callable[[Dict[str, Any]], Any]):
        """Remove a real-time listener callback."""
        if listener in self._listeners:
            self._listeners.remove(listener)

    async def _notify_listeners(self, event: Dict[str, Any]):
        """Broadcast an event to all registered listeners."""
        for listener in self._listeners:
            try:
                res = listener(event)
                if asyncio.iscoroutine(res):
                    await res
            except Exception:
                pass

    # ==========================
    # Rules CRUD
    # ==========================

    async def create_rule(
        self,
        workspace_id: str,
        name: str,
        metric_type: str,
        operator: str,
        threshold_value: float,
        window_seconds: int = 300,
        composite_logic: Optional[Dict[str, Any]] = None,
        severity: str = "warning",
        enabled: bool = True,
        cooldown_seconds: int = 300,
        webhook_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new alerting rule."""
        rule_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        rule = {
            "id": rule_id,
            "workspace_id": workspace_id,
            "name": name,
            "metric_type": metric_type,
            "operator": operator,
            "threshold_value": float(threshold_value),
            "window_seconds": int(window_seconds),
            "composite_logic": composite_logic,
            "severity": severity,
            "enabled": enabled,
            "cooldown_seconds": cooldown_seconds,
            "webhook_url": webhook_url,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }
        self._rules[rule_id] = rule
        return rule

    async def get_rule(self, rule_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve an alert rule by ID."""
        return self._rules.get(rule_id)

    async def list_rules(
        self,
        workspace_id: Optional[str] = None,
        enabled_only: bool = False,
    ) -> List[Dict[str, Any]]:
        """List alert rules with optional workspace filtering."""
        rules = list(self._rules.values())
        if workspace_id:
            rules = [r for r in rules if r["workspace_id"] == workspace_id]
        if enabled_only:
            rules = [r for r in rules if r.get("enabled", True)]
        return rules

    async def update_rule(self, rule_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing alert rule."""
        if rule_id not in self._rules:
            return None
        rule = self._rules[rule_id]
        for k, v in updates.items():
            if k not in ("id", "created_at"):
                rule[k] = v
        rule["updated_at"] = datetime.now(timezone.utc).isoformat()
        return rule

    async def delete_rule(self, rule_id: str) -> bool:
        """Delete an alert rule."""
        if rule_id in self._rules:
            del self._rules[rule_id]
            self._last_triggered.pop(rule_id, None)
            return True
        return False

    # ==========================
    # Rule Evaluation
    # ==========================

    def evaluate_threshold(self, operator: str, value: float, threshold: float) -> bool:
        """Evaluate a single metric comparison."""
        return OperatorEvaluator.evaluate(operator, value, threshold)

    def evaluate_composite(self, composite_logic: Dict[str, Any], metric_context: Dict[str, float]) -> bool:
        """
        Recursively evaluate composite logic (AND / OR).
        Format:
          {"and": [{"metric": "error_rate", "op": "gt", "val": 0.05}, ...]}
          or nested {"or": [...]}
        """
        if "and" in composite_logic:
            conditions = composite_logic["and"]
            for cond in conditions:
                if "and" in cond or "or" in cond:
                    if not self.evaluate_composite(cond, metric_context):
                        return False
                else:
                    metric_name = cond.get("metric")
                    val = metric_context.get(metric_name, 0.0)
                    op = cond.get("op", "gt")
                    threshold = cond.get("val", 0.0)
                    if not OperatorEvaluator.evaluate(op, val, threshold):
                        return False
            return True

        elif "or" in composite_logic:
            conditions = composite_logic["or"]
            for cond in conditions:
                if "and" in cond or "or" in cond:
                    if self.evaluate_composite(cond, metric_context):
                        return True
                else:
                    metric_name = cond.get("metric")
                    val = metric_context.get(metric_name, 0.0)
                    op = cond.get("op", "gt")
                    threshold = cond.get("val", 0.0)
                    if OperatorEvaluator.evaluate(op, val, threshold):
                        return True
            return False

        return False

    async def evaluate_and_trigger(
        self,
        rule_id: str,
        current_value: float,
        metric_context: Optional[Dict[str, float]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        force: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """
        Evaluate a rule against current metrics. If breached and cooldown expired, generate an event.
        """
        rule = self._rules.get(rule_id)
        if not rule or not rule.get("enabled", True):
            return None

        # Check composite or simple threshold
        triggered = False
        if rule.get("composite_logic"):
            context = metric_context or {}
            context.setdefault(rule["metric_type"], current_value)
            triggered = self.evaluate_composite(rule["composite_logic"], context)
        else:
            triggered = self.evaluate_threshold(
                rule["operator"],
                current_value,
                rule["threshold_value"],
            )

        if not triggered:
            return None

        # Check rate limiting / cooldown
        now = datetime.now(timezone.utc)
        cooldown = timedelta(seconds=rule.get("cooldown_seconds", 300))
        last_time = self._last_triggered.get(rule_id)
        if not force and last_time and (now - last_time < cooldown):
            # Cooldown active, suppress duplicate event
            return None

        # Update last triggered timestamp
        self._last_triggered[rule_id] = now

        # Create alert event
        event_id = str(uuid.uuid4())
        event = {
            "id": event_id,
            "rule_id": rule_id,
            "workspace_id": rule["workspace_id"],
            "rule_name": rule["name"],
            "metric_type": rule["metric_type"],
            "metric_value": float(current_value),
            "threshold_value": float(rule["threshold_value"]),
            "severity": rule["severity"],
            "triggered_at": now.isoformat(),
            "resolved_at": None,
            "resolution_note": None,
            "metadata": metadata or {},
        }
        self._events.append(event)

        # Notify real-time listeners
        await self._notify_listeners(event)

        # Dispatch Webhook if configured
        webhook_url = rule.get("webhook_url")
        if webhook_url:
            asyncio.create_task(self.dispatch_webhook(webhook_url, event))

        return event

    async def dispatch_webhook(self, url: str, payload: Dict[str, Any], retries: int = 2) -> bool:
        """Dispatch an HTTP POST alert payload to a webhook URL with retries."""
        for attempt in range(retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.webhook_timeout) as client:
                    resp = await client.post(url, json=payload)
                    if resp.status_code in (200, 201, 202, 204):
                        return True
            except Exception:
                if attempt < retries:
                    await asyncio.sleep(0.5 * (attempt + 1))
        return False

    # ==========================
    # Events & Resolution
    # ==========================

    async def list_events(
        self,
        workspace_id: Optional[str] = None,
        unresolved_only: bool = False,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """List triggered alert events."""
        events = self._events
        if workspace_id:
            events = [e for e in events if e["workspace_id"] == workspace_id]
        if unresolved_only:
            events = [e for e in events if e.get("resolved_at") is None]
        # Return newest first
        return sorted(events, key=lambda e: e["triggered_at"], reverse=True)[:limit]

    async def resolve_event(
        self,
        event_id: str,
        resolution_note: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Resolve a triggered alert event with an optional note."""
        for event in self._events:
            if event["id"] == event_id:
                now = datetime.now(timezone.utc)
                event["resolved_at"] = now.isoformat()
                event["resolution_note"] = resolution_note or "Resolved manually"
                await self._notify_listeners({
                    "type": "alert_resolved",
                    "event_id": event_id,
                    "resolved_at": event["resolved_at"],
                    "resolution_note": event["resolution_note"],
                })
                return event
        return None

    def clear(self):
        """Helper to reset in-memory state for testing."""
        self._rules.clear()
        self._events.clear()
        self._last_triggered.clear()


analytics_alerting_service = AnalyticsAlertingService()
