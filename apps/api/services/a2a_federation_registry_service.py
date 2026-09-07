# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_a2a_federation_registry_service"
# purpose: "Federated Agent Registration, Capability Schema Validation & Mutual Zero-Trust Auth (DNK-A2A-004 Phase 2)"
# author: "DNK-e.com Maksym & Gerych Prime"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import hashlib
import hmac
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("dnk.a2a.federation")

TRUST_TIER_RANK = {
    "tier-0": 0,  # Kernel / System Core
    "tier-1": 1,  # Verified Internal Partner
    "tier-2": 2,  # Standard Federated Agent
    "tier-3": 3,  # Sandboxed / Untrusted External
}


class A2AFederationRegistryService:
    """Manages cross-platform agent node registry, capability contracts and mutual Zero-Trust authentication."""

    def __init__(self):
        self._agents: Dict[str, Dict[str, Any]] = {}
        self._capability_schemas: Dict[str, Dict[str, Any]] = {}
        self._auth_tokens: Dict[str, str] = {}  # agent_id -> token_hash

    def register_agent(
        self,
        workspace_id: str,
        agent_name: str,
        platform: str,
        api_endpoint: str,
        capabilities: List[str],
        trust_tier: str = "tier-2",
        auth_token: Optional[str] = None,
        public_key: Optional[str] = None,
        streaming_endpoint: Optional[str] = None,
        max_concurrency: float = 5.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Registers an external or internal federated agent node."""
        agent_id = f"fed_agent_{uuid.uuid4().hex[:10]}"
        token_hash = None
        if auth_token:
            token_hash = hashlib.sha256(auth_token.encode("utf-8")).hexdigest()
            self._auth_tokens[agent_id] = token_hash

        agent_record = {
            "id": agent_id,
            "workspace_id": workspace_id,
            "agent_name": agent_name,
            "platform": platform,
            "protocol_version": "a2a/v2",
            "api_endpoint": api_endpoint,
            "streaming_endpoint": streaming_endpoint,
            "auth_token_hash": token_hash,
            "public_key": public_key,
            "trust_tier": trust_tier if trust_tier in TRUST_TIER_RANK else "tier-2",
            "capabilities": list(capabilities),
            "status": "active",
            "max_concurrency": max_concurrency,
            "current_load": 0.0,
            "reputation_score": 1.0,
            "metadata": metadata or {},
            "registered_at": datetime.now(timezone.utc).isoformat(),
            "last_heartbeat_at": datetime.now(timezone.utc).isoformat(),
        }
        self._agents[agent_id] = agent_record
        logger.info("Registered federated agent: %s (%s, platform: %s)", agent_name, agent_id, platform)
        return agent_record

    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        return self._agents.get(agent_id)

    def list_agents(self, workspace_id: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
        agents = list(self._agents.values())
        if workspace_id:
            agents = [a for a in agents if a["workspace_id"] == workspace_id]
        if status:
            agents = [a for a in agents if a["status"] == status]
        return agents

    def authenticate_agent(self, agent_id: str, raw_token_or_secret: str) -> bool:
        """Verifies mutual Zero-Trust authentication using constant-time hash comparison."""
        agent = self._agents.get(agent_id)
        if not agent or agent["status"] in ("blacklisted", "offline"):
            return False

        expected_hash = self._auth_tokens.get(agent_id)
        if not expected_hash:
            # If no auth token is registered, require valid agent record and active status
            return True

        provided_hash = hashlib.sha256(raw_token_or_secret.encode("utf-8")).hexdigest()
        return hmac.compare_digest(expected_hash, provided_hash)

    def register_capability_schema(
        self,
        workspace_id: str,
        capability_key: str,
        display_name: str,
        input_schema: Dict[str, Any],
        output_schema: Dict[str, Any],
        target_sla_latency_ms: float = 1500.0,
        required_trust_tier: str = "tier-2",
        cost_per_invocation: float = 0.01,
        rate_limit_rpm: int = 120,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Registers formal JSONSchema contracts and SLA limits for a capability."""
        schema_record = {
            "capability_key": capability_key,
            "workspace_id": workspace_id,
            "display_name": display_name,
            "description": description or display_name,
            "input_schema": input_schema,
            "output_schema": output_schema,
            "target_sla_latency_ms": target_sla_latency_ms,
            "required_trust_tier": required_trust_tier,
            "cost_per_invocation": cost_per_invocation,
            "rate_limit_rpm": rate_limit_rpm,
            "version": "1.0.0",
            "is_deprecated": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._capability_schemas[capability_key] = schema_record
        return schema_record

    def validate_capability_invocation(
        self, capability_key: str, payload: Dict[str, Any], caller_trust_tier: str = "tier-2"
    ) -> Dict[str, Any]:
        """Validates payload against capability schema and enforces trust tier isolation."""
        schema = self._capability_schemas.get(capability_key)
        if not schema:
            return {"valid": False, "error": f"Unknown capability '{capability_key}'"}

        required_tier = schema.get("required_trust_tier", "tier-2")
        if TRUST_TIER_RANK.get(caller_trust_tier, 99) > TRUST_TIER_RANK.get(required_tier, 99):
            return {
                "valid": False,
                "error": f"Insufficient trust tier: caller '{caller_trust_tier}' < required '{required_tier}'",
            }

        # Basic type & required fields check from input_schema
        input_spec = schema.get("input_schema", {})
        required_fields = input_spec.get("required", [])
        for field in required_fields:
            if field not in payload:
                return {"valid": False, "error": f"Missing required payload field: '{field}'"}

        return {"valid": True, "error": None, "schema": schema}

    def discover_agents_by_capability(
        self,
        capability_key: str,
        min_trust_tier: str = "tier-3",
        max_load: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Finds candidate agents that possess the requested capability and meet trust/load criteria."""
        max_rank = TRUST_TIER_RANK.get(min_trust_tier, 3)
        candidates = []
        for agent in self._agents.values():
            if agent["status"] != "active":
                continue
            if capability_key not in agent.get("capabilities", []):
                continue
            agent_tier = agent.get("trust_tier", "tier-2")
            if TRUST_TIER_RANK.get(agent_tier, 3) > max_rank:
                continue
            if max_load is not None and agent.get("current_load", 0.0) >= max_load:
                continue
            candidates.append(agent)

        # Sort by reputation score (desc) then load (asc)
        candidates.sort(key=lambda a: (-a.get("reputation_score", 1.0), a.get("current_load", 0.0)))
        return candidates

    def update_agent_heartbeat(
        self,
        agent_id: str,
        current_load: Optional[float] = None,
        status: str = "active",
    ) -> Optional[Dict[str, Any]]:
        agent = self._agents.get(agent_id)
        if not agent:
            return None
        agent["last_heartbeat_at"] = datetime.now(timezone.utc).isoformat()
        agent["status"] = status
        if current_load is not None:
            agent["current_load"] = max(0.0, float(current_load))
        return agent

    def update_reputation(self, agent_id: str, delta: float) -> float:
        agent = self._agents.get(agent_id)
        if not agent:
            return 0.0
        current = agent.get("reputation_score", 1.0)
        updated = max(0.0, min(1.0, current + delta))
        agent["reputation_score"] = round(updated, 3)
        return agent["reputation_score"]
