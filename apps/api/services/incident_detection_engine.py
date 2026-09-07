# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_incident_detection_engine"
# purpose: "Dynamic Rule Evaluation, Anomaly Detection & Flap Prevention (DNK-HEALTH-001 Phase 2)"
# author: "DNK-e.com Maksym & Gerych Prime"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import operator
import uuid
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from apps.api.db.models.health_metric_rule import HealthMetricRule
from apps.api.db.models.system_incident import SystemIncident
from apps.api.services.health_metric_aggregator import HealthMetricAggregator


class IncidentDetectionEngine:
    """Evaluates metrics against rules, detects statistical anomalies and handles incident lifecycles."""

    OPERATORS = {
        ">": operator.gt,
        ">=": operator.ge,
        "<": operator.lt,
        "<=": operator.le,
        "==": operator.eq,
        "!=": operator.ne,
    }

    def __init__(self, aggregator: Optional[HealthMetricAggregator] = None):
        self.aggregator = aggregator or HealthMetricAggregator()
        self._rules: Dict[str, HealthMetricRule] = {}
        # (workspace_id, service_name, metric_name, rule_id) -> list of consecutive breach timestamps
        self._breach_history: Dict[tuple, deque] = defaultdict(lambda: deque(maxlen=20))
        # (workspace_id, service_name, incident_key) -> deque of state toggle timestamps for flap detection
        self._toggle_history: Dict[tuple, deque] = defaultdict(lambda: deque(maxlen=20))
        # active incidents: id -> SystemIncident
        self._active_incidents: Dict[str, SystemIncident] = {}

    def register_rule(self, rule: HealthMetricRule) -> str:
        """Registers or updates a health metric threshold rule."""
        rule_dict = rule.to_dict()
        rule_id = rule_dict["id"]
        self._rules[rule_id] = rule
        return rule_id

    def remove_rule(self, rule_id: str) -> bool:
        """Removes a rule by its ID."""
        return bool(self._rules.pop(rule_id, None))

    def list_rules(self, workspace_id: Optional[str] = None) -> List[HealthMetricRule]:
        """Lists registered rules."""
        if workspace_id is None:
            return list(self._rules.values())
        return [r for r in self._rules.values() if r.workspace_id == workspace_id]

    def _compare(self, value: float, comparator: str, threshold: float) -> bool:
        op_fn = self.OPERATORS.get(comparator, operator.gt)
        return bool(op_fn(value, threshold))

    def evaluate_metric(
        self,
        workspace_id: str,
        service_name: str,
        metric_name: str,
        observed_value: float,
        timestamp: Optional[datetime] = None,
    ) -> List[SystemIncident]:
        """Evaluates a single metric update against all matching active rules."""
        ts = timestamp or datetime.now(timezone.utc)
        self.aggregator.record_metric(workspace_id, service_name, metric_name, observed_value, ts)

        triggered_incidents: List[SystemIncident] = []
        matching_rules = [
            r for r in self._rules.values()
            if r.workspace_id == workspace_id
            and r.service_name == service_name
            and r.metric_name == metric_name
            and (r.is_active is None or r.is_active is True)
        ]

        for rule in matching_rules:
            breach_key = (workspace_id, service_name, metric_name, rule.id)
            comp = rule.comparator or ">"

            is_critical = self._compare(observed_value, comp, rule.critical_threshold)
            is_warning = is_critical or self._compare(observed_value, comp, rule.warning_threshold)

            if is_warning or is_critical:
                self._breach_history[breach_key].append(ts)
                req_breaches = rule.consecutive_breaches_required or 1

                # Check if we have enough consecutive breaches within the evaluation window
                window_s = rule.evaluation_window_seconds or 60
                recent_breaches = [
                    t for t in self._breach_history[breach_key]
                    if (ts - t).total_seconds() <= window_s
                ]

                if len(recent_breaches) >= req_breaches:
                    severity = "CRITICAL" if is_critical else "WARNING"
                    incident_title = f"{severity} breach on {service_name}:{metric_name}"
                    thresh = rule.critical_threshold if is_critical else rule.warning_threshold

                    # Check flap detection
                    flap_key = (workspace_id, service_name, f"{rule.id}_flap")
                    self._toggle_history[flap_key].append(ts)
                    flaps = [t for t in self._toggle_history[flap_key] if (ts - t).total_seconds() <= 300]
                    is_flapping = len(flaps) >= 4

                    status = "FLAPPING" if is_flapping else "OPEN"
                    inc_id = f"inc_{uuid.uuid4().hex[:12]}"

                    incident = SystemIncident(
                        id=inc_id,
                        workspace_id=workspace_id,
                        service_name=service_name,
                        rule_id=rule.id,
                        severity=severity,
                        status=status,
                        title=incident_title,
                        description=f"Observed {observed_value} {comp} threshold {thresh} (window: {window_s}s)",
                        metric_name=metric_name,
                        observed_value=float(observed_value),
                        threshold_value=float(thresh),
                        context_data={
                            "consecutive_breaches": len(recent_breaches),
                            "required_breaches": req_breaches,
                            "is_flapping": is_flapping,
                        },
                        opened_at=ts,
                    )
                    self._active_incidents[inc_id] = incident
                    triggered_incidents.append(incident)
            else:
                # Reset consecutive breaches if value returns to normal
                self._breach_history[breach_key].clear()

        return triggered_incidents

    def detect_statistical_anomaly(
        self,
        workspace_id: str,
        service_name: str,
        metric_name: str,
        z_threshold: float = 3.0,
        min_samples: int = 5,
    ) -> Optional[Dict[str, Any]]:
        """Detects whether current metric value is a statistical outlier (Z-score anomaly)."""
        stats = self.aggregator.compute_statistics(workspace_id, service_name, metric_name)
        if stats["count"] < min_samples or stats["stddev"] == 0.0:
            return None

        latest = stats["latest"]
        z_score = abs(latest - stats["mean"]) / stats["stddev"]

        if z_score >= z_threshold:
            return {
                "workspace_id": workspace_id,
                "service_name": service_name,
                "metric_name": metric_name,
                "latest_value": latest,
                "mean": stats["mean"],
                "stddev": stats["stddev"],
                "z_score": round(z_score, 4),
                "is_anomaly": True,
            }
        return None

    def resolve_incident(self, incident_id: str) -> Optional[SystemIncident]:
        """Resolves an active incident."""
        incident = self._active_incidents.get(incident_id)
        if incident:
            incident.status = "RESOLVED"
            incident.resolved_at = datetime.now(timezone.utc)
            self._active_incidents.pop(incident_id, None)
            return incident
        return None

    def get_active_incidents(self, workspace_id: Optional[str] = None) -> List[SystemIncident]:
        """Returns all currently active incidents."""
        if workspace_id is None:
            return list(self._active_incidents.values())
        return [inc for inc in self._active_incidents.values() if inc.workspace_id == workspace_id]
