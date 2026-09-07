# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_a2a_mesh_router_service"
# purpose: "Resilient Mesh Router, Failover Dispatching & Circuit Breaker (DNK-A2A-004 Phase 3)"
# author: "DNK-e.com Maksym & Gerych Prime"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("dnk.a2a.router")


class CircuitBreakerState:
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class A2AMeshRouterService:
    """Manages routing tables, load-balanced dispatching, resilient failover and Circuit Breaker states."""

    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_timeout_s: float = 30.0,
        half_open_success_threshold: int = 2,
    ):
        self._routes: Dict[str, Dict[str, Any]] = {}
        self._circuit_breakers: Dict[str, Dict[str, Any]] = {}  # agent_id -> state
        self._failure_threshold = failure_threshold
        self._recovery_timeout_s = recovery_timeout_s
        self._half_open_success_threshold = half_open_success_threshold
        self._rr_indices: Dict[str, int] = {}

    def register_route(
        self,
        workspace_id: str,
        capability_key: str,
        primary_agent_id: str,
        fallback_agent_ids: Optional[List[str]] = None,
        routing_strategy: str = "least_loaded",
        priority_weight: float = 1.0,
    ) -> Dict[str, Any]:
        """Registers a routing rule for a capability across primary and fallback agent nodes."""
        route_id = f"route_{uuid.uuid4().hex[:10]}"
        route_record = {
            "id": route_id,
            "workspace_id": workspace_id,
            "capability_key": capability_key,
            "primary_agent_id": primary_agent_id,
            "fallback_agent_ids": list(fallback_agent_ids or []),
            "routing_strategy": routing_strategy,
            "priority_weight": priority_weight,
            "total_routed_requests": 0,
            "failed_requests": 0,
            "avg_latency_ms": 0.0,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._routes[capability_key] = route_record
        logger.info("Registered mesh route for capability '%s' -> primary: %s", capability_key, primary_agent_id)
        return route_record

    def get_route(self, capability_key: str) -> Optional[Dict[str, Any]]:
        return self._routes.get(capability_key)

    def _get_circuit_breaker(self, agent_id: str) -> Dict[str, Any]:
        if agent_id not in self._circuit_breakers:
            self._circuit_breakers[agent_id] = {
                "state": CircuitBreakerState.CLOSED,
                "consecutive_failures": 0,
                "consecutive_successes": 0,
                "last_state_change": time.time(),
            }
        return self._circuit_breakers[agent_id]

    def record_success(self, agent_id: str, latency_ms: float = 0.0):
        """Records successful invocation to reset failure counters or close half-open circuit."""
        cb = self._get_circuit_breaker(agent_id)
        if cb["state"] == CircuitBreakerState.HALF_OPEN:
            cb["consecutive_successes"] += 1
            if cb["consecutive_successes"] >= self._half_open_success_threshold:
                cb["state"] = CircuitBreakerState.CLOSED
                cb["consecutive_failures"] = 0
                cb["consecutive_successes"] = 0
                cb["last_state_change"] = time.time()
                logger.info("Circuit breaker for agent %s transitioned HALF_OPEN -> CLOSED", agent_id)
        elif cb["state"] == CircuitBreakerState.CLOSED:
            cb["consecutive_failures"] = 0

    def record_failure(self, agent_id: str):
        """Records invocation failure and trips circuit breaker if threshold exceeded."""
        cb = self._get_circuit_breaker(agent_id)
        cb["consecutive_failures"] += 1
        cb["consecutive_successes"] = 0

        if cb["state"] == CircuitBreakerState.HALF_OPEN:
            cb["state"] = CircuitBreakerState.OPEN
            cb["last_state_change"] = time.time()
            logger.warning("Circuit breaker for agent %s returned to OPEN (failed in HALF_OPEN)", agent_id)
        elif cb["state"] == CircuitBreakerState.CLOSED:
            if cb["consecutive_failures"] >= self._failure_threshold:
                cb["state"] = CircuitBreakerState.OPEN
                cb["last_state_change"] = time.time()
                logger.warning(
                    "Circuit breaker for agent %s tripped CLOSED -> OPEN (failures: %d)",
                    agent_id,
                    cb["consecutive_failures"],
                )

    def is_agent_available(self, agent_id: str) -> bool:
        """Checks if agent circuit breaker allows dispatching traffic."""
        cb = self._get_circuit_breaker(agent_id)
        if cb["state"] == CircuitBreakerState.CLOSED:
            return True

        if cb["state"] == CircuitBreakerState.OPEN:
            # Check if recovery timeout elapsed
            elapsed = time.time() - cb["last_state_change"]
            if elapsed >= self._recovery_timeout_s:
                cb["state"] = CircuitBreakerState.HALF_OPEN
                cb["consecutive_successes"] = 0
                cb["last_state_change"] = time.time()
                logger.info("Circuit breaker for agent %s transitioned OPEN -> HALF_OPEN (probing)", agent_id)
                return True
            return False

        if cb["state"] == CircuitBreakerState.HALF_OPEN:
            return True

        return False

    def select_target_agent(
        self,
        capability_key: str,
        available_agents_map: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Resolves target agent with automatic failover across primary and fallbacks."""
        route = self._routes.get(capability_key)
        if not route:
            # Fallback to direct capability search among available agents
            candidates = [
                a for a in available_agents_map.values()
                if capability_key in a.get("capabilities", []) and self.is_agent_available(a["id"])
            ]
            if not candidates:
                return {"success": False, "error": f"No available agent found for capability '{capability_key}'"}
            return {"success": True, "agent_id": candidates[0]["id"], "is_fallback": False, "route_id": None}

        primary_id = route["primary_agent_id"]
        primary_agent = available_agents_map.get(primary_id)

        # Check if primary is healthy & circuit closed
        if primary_agent and primary_agent.get("status") == "active" and self.is_agent_available(primary_id):
            route["total_routed_requests"] += 1
            return {
                "success": True,
                "agent_id": primary_id,
                "is_fallback": False,
                "route_id": route["id"],
                "strategy": route["routing_strategy"],
            }

        # Primary failed or tripped -> iterate fallbacks
        logger.warning(
            "Primary agent %s unavailable for capability '%s'. Attempting failover.", primary_id, capability_key
        )
        for fb_id in route.get("fallback_agent_ids", []):
            fb_agent = available_agents_map.get(fb_id)
            if fb_agent and fb_agent.get("status") == "active" and self.is_agent_available(fb_id):
                route["total_routed_requests"] += 1
                logger.info("Failover succeeded: capability '%s' routed to fallback agent %s", capability_key, fb_id)
                return {
                    "success": True,
                    "agent_id": fb_id,
                    "is_fallback": True,
                    "primary_agent_id": primary_id,
                    "route_id": route["id"],
                }

        route["failed_requests"] += 1
        return {
            "success": False,
            "error": f"All primary and fallback agents exhausted/unavailable for capability '{capability_key}'",
        }
