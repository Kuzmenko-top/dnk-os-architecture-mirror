# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_auto_healing_executor"
# purpose: "Automated Self-Healing Playbook Executor & Safety Guards (DNK-HEALTH-001 Phase 3)"
# author: "DNK-e.com Maksym & Gerych Prime"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import time
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional
from apps.api.db.models.auto_healing_policy import AutoHealingPolicy
from apps.api.db.models.remediation_action import RemediationAction
from apps.api.db.models.system_incident import SystemIncident


class AutoHealingExecutor:
    """Executes automated remediation workflows with safety guardrails (circuit breaking & cooldowns)."""

    def __init__(self):
        self._policies: Dict[str, AutoHealingPolicy] = {}
        self._action_handlers: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {}
        # (workspace_id, service_name, action_type) -> last execution timestamp
        self._last_execution_ts: Dict[tuple, float] = {}
        # incident_id -> execution attempts count
        self._incident_attempts: Dict[str, int] = defaultdict(int)
        # action_id -> RemediationAction
        self._action_history: Dict[str, RemediationAction] = {}

        self._register_default_handlers()

    def _register_default_handlers(self) -> None:
        """Registers default simulation/mock remediation action handlers."""
        self._action_handlers["restart_service"] = lambda ctx: {
            "restarted": True,
            "target_service": ctx.get("service_name"),
            "restart_mode": "graceful_drain_reload",
        }
        self._action_handlers["drain_traffic"] = lambda ctx: {
            "drained": True,
            "weight_pct": 0,
            "rerouted_to": ctx.get("fallback_target", "failover_cluster"),
        }
        self._action_handlers["clear_cache"] = lambda ctx: {
            "cache_purged": True,
            "keyspace": ctx.get("keyspace", "*"),
            "items_evicted": 128,
        }
        self._action_handlers["scale_replicas"] = lambda ctx: {
            "scaled": True,
            "target_replicas": ctx.get("target_replicas", 3),
            "scale_delta": +1,
        }
        self._action_handlers["trip_circuit_breaker"] = lambda ctx: {
            "circuit_breaker_opened": True,
            "isolation_level": "mesh_node",
        }

    def register_policy(self, policy: AutoHealingPolicy) -> str:
        """Registers an auto-healing policy."""
        pid = policy.id or f"ahp_{uuid.uuid4().hex[:12]}"
        policy.id = pid
        self._policies[pid] = policy
        return pid

    def remove_policy(self, policy_id: str) -> bool:
        """Removes an auto-healing policy."""
        return bool(self._policies.pop(policy_id, None))

    def list_policies(self, workspace_id: Optional[str] = None) -> List[AutoHealingPolicy]:
        """Lists registered policies."""
        if workspace_id is None:
            return list(self._policies.values())
        return [p for p in self._policies.values() if p.workspace_id == workspace_id]

    def register_custom_handler(
        self,
        action_type: str,
        handler: Callable[[Dict[str, Any]], Dict[str, Any]],
    ) -> None:
        """Registers a custom execution callable for a specific action type."""
        self._action_handlers[action_type] = handler

    def evaluate_and_execute(
        self,
        incident: SystemIncident,
        policy: Optional[AutoHealingPolicy] = None,
    ) -> RemediationAction:
        """Evaluates policy guardrails and executes remediation action for an incident."""
        now_epoch = time.time()
        now_dt = datetime.now(timezone.utc)
        action_id = f"act_{uuid.uuid4().hex[:12]}"

        # Find matching policy if not explicitly provided
        if not policy:
            def _matches_policy(p: AutoHealingPolicy) -> bool:
                if p.workspace_id != incident.workspace_id:
                    return False
                if p.service_name != incident.service_name:
                    return False
                if p.is_enabled is False:
                    return False
                pt = (p.incident_type or "ANY").strip().upper()
                if pt in ("ANY", "*", "ALL"):
                    return True
                if pt == incident.severity.upper() or pt == incident.metric_name.upper():
                    return True
                high_tier = {"HIGH", "CRITICAL", "FATAL"}
                if pt in high_tier and incident.severity.upper() in high_tier:
                    return True
                if pt in {"WARNING", "WARN", "LOW"} and incident.severity.upper() in {"WARNING", "WARN", "LOW"}:
                    return True
                return False

            matching = [p for p in self._policies.values() if _matches_policy(p)]
            if not matching:
                action = RemediationAction(
                    id=action_id,
                    workspace_id=incident.workspace_id,
                    incident_id=incident.id,
                    service_name=incident.service_name,
                    action_type="NONE",
                    status="SKIPPED",
                    execution_result={"reason": "No active policy matching incident condition"},
                    started_at=now_dt,
                    completed_at=now_dt,
                )
                self._action_history[action_id] = action
                return action
            policy = matching[0]

        action_type = policy.remediation_playbook
        guard_key = (incident.workspace_id, incident.service_name, action_type)
        cooldown = policy.cooldown_seconds or 60
        max_retries = policy.max_retries or 3

        # Safety Guard 1: Flap Safety Check
        if incident.status == "FLAPPING":
            action = RemediationAction(
                id=action_id,
                workspace_id=incident.workspace_id,
                incident_id=incident.id,
                policy_id=policy.id,
                service_name=incident.service_name,
                action_type=action_type,
                status="SKIPPED",
                execution_result={"reason": "Execution suppressed: service is in FLAPPING state"},
                started_at=now_dt,
                completed_at=now_dt,
            )
            self._action_history[action_id] = action
            return action

        # Safety Guard 2: Cooldown Enforcement
        last_run = self._last_execution_ts.get(guard_key, 0)
        if now_epoch - last_run < cooldown:
            remaining = int(cooldown - (now_epoch - last_run))
            action = RemediationAction(
                id=action_id,
                workspace_id=incident.workspace_id,
                incident_id=incident.id,
                policy_id=policy.id,
                service_name=incident.service_name,
                action_type=action_type,
                status="SKIPPED",
                execution_result={"reason": f"Execution suppressed: in cooldown period ({remaining}s left)"},
                started_at=now_dt,
                completed_at=now_dt,
            )
            self._action_history[action_id] = action
            return action

        # Safety Guard 3: Max retry attempts per incident
        current_attempts = self._incident_attempts[incident.id]
        if current_attempts >= max_retries:
            action = RemediationAction(
                id=action_id,
                workspace_id=incident.workspace_id,
                incident_id=incident.id,
                policy_id=policy.id,
                service_name=incident.service_name,
                action_type=action_type,
                status="SKIPPED",
                execution_result={"reason": f"Execution suppressed: max retries ({max_retries}) reached"},
                started_at=now_dt,
                completed_at=now_dt,
            )
            self._action_history[action_id] = action
            return action

        # Execute remediation action
        handler = (
            self._action_handlers.get(action_type)
            or self._action_handlers.get(action_type.lower())
            or self._action_handlers.get(action_type.upper())
        )
        if not handler:
            action = RemediationAction(
                id=action_id,
                workspace_id=incident.workspace_id,
                incident_id=incident.id,
                policy_id=policy.id,
                service_name=incident.service_name,
                action_type=action_type,
                status="FAILED",
                execution_result={"error": f"No handler registered for action type {action_type}"},
                started_at=now_dt,
                completed_at=now_dt,
            )
            self._action_history[action_id] = action
            return action

        self._incident_attempts[incident.id] += 1
        self._last_execution_ts[guard_key] = now_epoch

        t_start = time.perf_counter()
        try:
            context = {
                "workspace_id": incident.workspace_id,
                "service_name": incident.service_name,
                "incident_id": incident.id,
                "severity": incident.severity,
                "metric_name": incident.metric_name,
                "policy_config": policy.playbook_config or {},
            }
            res = handler(context)
            duration_ms = (time.perf_counter() - t_start) * 1000.0

            action = RemediationAction(
                id=action_id,
                workspace_id=incident.workspace_id,
                incident_id=incident.id,
                policy_id=policy.id,
                service_name=incident.service_name,
                action_type=action_type,
                status="SUCCEEDED",
                execution_time_ms=round(duration_ms, 2),
                execution_result={
                    "handler_result": res,
                    "attempt_number": self._incident_attempts[incident.id],
                    "action_type": action_type,
                },
                started_at=now_dt,
                completed_at=datetime.now(timezone.utc),
            )
        except Exception as exc:
            duration_ms = (time.perf_counter() - t_start) * 1000.0
            action = RemediationAction(
                id=action_id,
                workspace_id=incident.workspace_id,
                incident_id=incident.id,
                policy_id=policy.id,
                service_name=incident.service_name,
                action_type=action_type,
                status="FAILED",
                execution_time_ms=round(duration_ms, 2),
                execution_result={
                    "error": str(exc),
                    "attempt_number": self._incident_attempts[incident.id],
                },
                started_at=now_dt,
                completed_at=datetime.now(timezone.utc),
            )

        self._action_history[action_id] = action
        return action

    def get_action_history(
        self,
        workspace_id: Optional[str] = None,
        incident_id: Optional[str] = None,
    ) -> List[RemediationAction]:
        """Returns execution history filtered by workspace or incident."""
        actions = list(self._action_history.values())
        if workspace_id:
            actions = [a for a in actions if a.workspace_id == workspace_id]
        if incident_id:
            actions = [a for a in actions if a.incident_id == incident_id]
        return actions
