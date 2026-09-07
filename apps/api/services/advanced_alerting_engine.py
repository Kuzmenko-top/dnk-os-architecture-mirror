# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_advanced_alerting_engine"
# purpose: "Advanced Composite Alert Rule Evaluator, Deduplication, and Grouping Engine for DNK-ANALYTICS-004"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


class CompositeRuleEvaluator:
    """Evaluates composite logic (AND / OR nested rules) against incoming metric snapshots."""

    @staticmethod
    def evaluate_condition(condition: Dict[str, Any], metrics: Dict[str, float]) -> bool:
        """
        Evaluate a single metric condition.
        Condition format:
          {"metric": "error_rate", "operator": "gt", "value": 0.05}
          {"metric": "latency_p95", "operator": "between", "value": [200, 500]}
        """
        metric_name = condition.get("metric")
        operator = str(condition.get("operator", "gt")).lower()
        target_val = condition.get("value")

        if not metric_name or metric_name not in metrics or target_val is None:
            return False

        actual_val = metrics[metric_name]

        try:
            if operator in ("gt", ">"):
                return actual_val > float(target_val)
            elif operator in ("gte", ">="):
                return actual_val >= float(target_val)
            elif operator in ("lt", "<"):
                return actual_val < float(target_val)
            elif operator in ("lte", "<="):
                return actual_val <= float(target_val)
            elif operator in ("eq", "=="):
                return abs(actual_val - float(target_val)) < 1e-6
            elif operator in ("neq", "!="):
                return abs(actual_val - float(target_val)) >= 1e-6
            elif operator == "between" and isinstance(target_val, (list, tuple)) and len(target_val) == 2:
                return float(target_val[0]) <= actual_val <= float(target_val[1])
        except (ValueError, TypeError):
            return False
        return False

    @classmethod
    def evaluate_composite_logic(cls, logic: Dict[str, Any], metrics: Dict[str, float]) -> bool:
        """
        Evaluate composite logic tree.
        Supports:
          {"and": [condition1, condition2, ...]}
          {"or": [condition1, condition2, ...]}
        Can be recursively nested.
        """
        if "and" in logic:
            conditions = logic["and"]
            if not isinstance(conditions, list) or not conditions:
                return False
            for cond in conditions:
                if "and" in cond or "or" in cond:
                    if not cls.evaluate_composite_logic(cond, metrics):
                        return False
                else:
                    if not cls.evaluate_condition(cond, metrics):
                        return False
            return True

        elif "or" in logic:
            conditions = logic["or"]
            if not isinstance(conditions, list) or not conditions:
                return False
            for cond in conditions:
                if "and" in cond or "or" in cond:
                    if cls.evaluate_composite_logic(cond, metrics):
                        return True
                else:
                    if cls.evaluate_condition(cond, metrics):
                        return True
            return False

        # Direct single condition fallback
        return cls.evaluate_condition(logic, metrics)


class AlertDeduplicator:
    """Manages cooldown intervals per rule / workspace to prevent alert flooding."""

    def __init__(self):
        self._last_triggered: Dict[str, float] = {}

    def is_in_cooldown(self, rule_id: str, cooldown_seconds: int = 300) -> bool:
        """Check if an alert rule is currently within its cooldown window."""
        now = time.time()
        last_time = self._last_triggered.get(rule_id, 0.0)
        return (now - last_time) < cooldown_seconds

    def record_trigger(self, rule_id: str):
        """Record the trigger timestamp for an alert rule."""
        self._last_triggered[rule_id] = time.time()

    def reset_rule(self, rule_id: str):
        """Clear cooldown state for a rule."""
        self._last_triggered.pop(rule_id, None)


class AdvancedAlertingEngine:
    """
    Main Engine for Composite Alert Evaluation, Cooldown Deduplication,
    Workspace/Region Alert Grouping, and Resolution Management.
    """

    def __init__(self):
        self.evaluator = CompositeRuleEvaluator()
        self.deduplicator = AlertDeduplicator()

    def evaluate_rule(
        self,
        rule_id: str,
        composite_logic: Dict[str, Any],
        metrics_snapshot: Dict[str, float],
        cooldown_seconds: int = 300,
    ) -> Tuple[bool, bool]:
        """
        Evaluate alert rule against metric snapshot.
        Returns Tuple[is_triggered, is_suppressed_by_cooldown].
        """
        triggered = self.evaluator.evaluate_composite_logic(composite_logic, metrics_snapshot)
        if not triggered:
            return False, False

        suppressed = self.deduplicator.is_in_cooldown(rule_id, cooldown_seconds)
        if not suppressed:
            self.deduplicator.record_trigger(rule_id)

        return triggered, suppressed

    @staticmethod
    def group_alerts_by_workspace(
        alerts: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Group alert events by workspace_id."""
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for alert in alerts:
            ws_id = alert.get("workspace_id", "default")
            grouped.setdefault(ws_id, []).append(alert)
        return grouped

    @staticmethod
    def group_alerts_by_severity(
        alerts: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Group alert events by severity ('info', 'warning', 'critical')."""
        grouped: Dict[str, List[Dict[str, Any]]] = {
            "critical": [],
            "warning": [],
            "info": [],
        }
        for alert in alerts:
            sev = str(alert.get("severity", "warning")).lower()
            grouped.setdefault(sev, []).append(alert)
        return grouped
