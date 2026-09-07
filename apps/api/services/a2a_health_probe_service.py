# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_a2a_health_probe_service"
# purpose: "Synthetic Probing, Failure Detection, Quarantine & Auto-Recovery (DNK-A2A-004 Phase 3)"
# author: "DNK-e.com Maksym & Gerych Prime"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("dnk.a2a.health")


class A2AHealthProbeService:
    """Performs synthetic health probes, detects node degradation, and manages automatic node quarantine / recovery."""

    def __init__(
        self,
        quarantine_failure_threshold: int = 3,
        recovery_success_threshold: int = 2,
        max_acceptable_latency_ms: float = 3000.0,
    ):
        self._probe_history: List[Dict[str, Any]] = []
        self._node_health_state: Dict[str, Dict[str, Any]] = {}  # agent_id -> state
        self._quarantine_failure_threshold = quarantine_failure_threshold
        self._recovery_success_threshold = recovery_success_threshold
        self._max_acceptable_latency_ms = max_acceptable_latency_ms

    def _get_node_state(self, agent_id: str) -> Dict[str, Any]:
        if agent_id not in self._node_health_state:
            self._node_health_state[agent_id] = {
                "agent_id": agent_id,
                "status": "healthy",
                "is_quarantined": False,
                "consecutive_failures": 0,
                "consecutive_successes": 0,
                "total_probes": 0,
                "failed_probes": 0,
                "latencies": [],
                "last_probe_at": None,
                "quarantined_at": None,
            }
        return self._node_health_state[agent_id]

    def record_probe_result(
        self,
        workspace_id: str,
        agent_id: str,
        probe_type: str = "http_ping",
        is_healthy: bool = True,
        latency_ms: float = 120.0,
        cpu_usage_pct: Optional[float] = None,
        memory_usage_pct: Optional[float] = None,
        error_message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Records a synthetic or active probe measurement and evaluates quarantine / recovery transitions."""
        probe_id = f"probe_{uuid.uuid4().hex[:10]}"
        now_iso = datetime.now(timezone.utc).isoformat()

        # Check if latency exceeds max acceptable threshold
        if latency_ms > self._max_acceptable_latency_ms:
            is_healthy = False
            error_message = error_message or f"Latency {latency_ms}ms exceeded SLA {self._max_acceptable_latency_ms}ms"

        probe_record = {
            "id": probe_id,
            "workspace_id": workspace_id,
            "agent_id": agent_id,
            "probe_type": probe_type,
            "is_healthy": is_healthy,
            "latency_ms": latency_ms,
            "cpu_usage_pct": cpu_usage_pct,
            "memory_usage_pct": memory_usage_pct,
            "error_message": error_message,
            "probed_at": now_iso,
        }
        self._probe_history.append(probe_record)

        state = self._get_node_state(agent_id)
        state["total_probes"] += 1
        state["last_probe_at"] = now_iso
        state["latencies"].append(latency_ms)
        if len(state["latencies"]) > 100:
            state["latencies"].pop(0)

        if is_healthy:
            state["consecutive_successes"] += 1
            state["consecutive_failures"] = 0

            # Check if quarantined node can be restored
            if state["is_quarantined"] and state["consecutive_successes"] >= self._recovery_success_threshold:
                state["is_quarantined"] = False
                state["status"] = "healthy"
                state["quarantined_at"] = None
                logger.info("Agent %s recovered and removed from quarantine", agent_id)
            elif not state["is_quarantined"]:
                state["status"] = "healthy"
        else:
            state["failed_probes"] += 1
            state["consecutive_failures"] += 1
            state["consecutive_successes"] = 0

            # Check if node should be quarantined
            if state["consecutive_failures"] >= self._quarantine_failure_threshold and not state["is_quarantined"]:
                state["is_quarantined"] = True
                state["status"] = "quarantined"
                state["quarantined_at"] = now_iso
                logger.warning(
                    "Agent %s placed into quarantine after %d consecutive failures",
                    agent_id,
                    state["consecutive_failures"],
                )
            elif state["is_quarantined"]:
                state["status"] = "quarantined"
            else:
                state["status"] = "degraded"

        return {
            "probe": probe_record,
            "node_status": state["status"],
            "is_quarantined": state["is_quarantined"],
        }

    def get_agent_health_summary(self, agent_id: str) -> Dict[str, Any]:
        """Calculates comprehensive health telemetry (uptime %, avg latency, current status)."""
        state = self._get_node_state(agent_id)
        total = state["total_probes"]
        failed = state["failed_probes"]
        uptime_pct = 100.0 if total == 0 else round(((total - failed) / total) * 100.0, 2)

        latencies = state["latencies"]
        avg_latency = round(sum(latencies) / len(latencies), 2) if latencies else 0.0

        return {
            "agent_id": agent_id,
            "status": state["status"],
            "is_quarantined": state["is_quarantined"],
            "uptime_pct": uptime_pct,
            "avg_latency_ms": avg_latency,
            "total_probes": total,
            "failed_probes": failed,
            "consecutive_failures": state["consecutive_failures"],
            "last_probe_at": state["last_probe_at"],
            "quarantined_at": state["quarantined_at"],
        }

    def list_quarantined_agents(self) -> List[str]:
        return [agent_id for agent_id, s in self._node_health_state.items() if s["is_quarantined"]]
