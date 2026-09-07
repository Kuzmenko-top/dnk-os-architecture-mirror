# --- DNK-MRH-HEADER ---
# mrh_id: "core_services_security_gate_service"
# purpose: "Concrete implementation of SecurityGateService (InlineSecurityGateService) with caching, conditions verification, and audit trail"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-08-11"
# --- END DNK-MRH-HEADER ---

import asyncio
import fnmatch
import hashlib
import json
import time
from typing import Optional, Dict, Any, Tuple, List
from uuid import UUID

from core.ports.security_gate_service import SecurityGateService
from core.models.security import SecurityPolicy, GateDecision
from core.config.security_gate_config import (
    SECURITY_GATE_CACHE_TTL,
    SECURITY_GATE_MAX_ARGUMENTS_SIZE
)
from core.adapters.security_gate_timeline_adapter import SecurityGateTimelineAdapter

def _json_serial(obj):
    if isinstance(obj, UUID):
        return str(obj)
    raise TypeError(f"Type {type(obj)} not serializable")

class InlineSecurityGateService(SecurityGateService):
    def __init__(self, timeline_adapter: Optional[SecurityGateTimelineAdapter] = None):
        self.timeline_adapter = timeline_adapter
        self.policies: Dict[UUID, SecurityPolicy] = {}
        # Cache stores: run_id:action:arguments_hash -> (decision, cached_at_timestamp)
        self._cache: Dict[str, Tuple[GateDecision, float]] = {}

    def _compute_arguments_hash(self, arguments: Dict[str, Any]) -> str:
        # Sort keys and serialize UUIDs properly to ensure stable serialized string
        serialized = json.dumps(arguments, sort_keys=True, default=_json_serial)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def _log_audit_trail(self, run_id: UUID, action: str, allowed: bool, reason: str) -> None:
        if self.timeline_adapter:
            coro = self.timeline_adapter.log_decision(run_id, action, allowed, reason)
            try:
                # If there's an active running event loop (like during async tests),
                # schedule the task concurrently on the same loop to avoid cross-loop asyncpg state conflicts!
                loop = asyncio.get_running_loop()
                loop.create_task(coro)
            except RuntimeError:
                # No active event loop, run it synchronously
                asyncio.run(coro)

    def create_policy(self, policy: SecurityPolicy) -> SecurityPolicy:
        self.policies[policy.id] = policy
        return policy

    def get_policy(self, policy_id: UUID) -> Optional[SecurityPolicy]:
        return self.policies.get(policy_id)

    def evaluate_policy(
        self,
        run_id: UUID,
        action: str,
        arguments: Dict[str, Any],
        context: Dict[str, Any],
    ) -> GateDecision:
        # Strict Fail Closed Check: Check arguments size limits first
        try:
            serialized_args = json.dumps(arguments, default=_json_serial)
            if len(serialized_args.encode("utf-8")) > SECURITY_GATE_MAX_ARGUMENTS_SIZE:
                decision = GateDecision(
                    allowed=False,
                    reason=f"Arguments size exceeds limit ({SECURITY_GATE_MAX_ARGUMENTS_SIZE} bytes)"
                )
                self._log_audit_trail(run_id, action, decision.allowed, decision.reason)
                return decision
        except Exception as e:
            decision = GateDecision(allowed=False, reason=f"Failed to serialize arguments: {e}")
            self._log_audit_trail(run_id, action, decision.allowed, decision.reason)
            return decision

        # Compute arguments hash and check cache (Idempotency + Expiry)
        args_hash = self._compute_arguments_hash(arguments)
        cache_key = f"{run_id}:{action}:{args_hash}"
        now = time.time()
        
        if cache_key in self._cache:
            cached_decision, cached_at = self._cache[cache_key]
            ttl = cached_decision.expiry if cached_decision.expiry is not None else SECURITY_GATE_CACHE_TTL
            if now < cached_at + ttl:
                # Return cached decision safely (idempotent result)
                return cached_decision

        # Find matching policy based on action patterns
        matching_policy: Optional[SecurityPolicy] = None
        for policy in self.policies.values():
            for pattern in policy.action_patterns:
                if fnmatch.fnmatch(action, pattern):
                    matching_policy = policy
                    break
            if matching_policy:
                break

        # Evaluate matched policy
        if not matching_policy:
            # Default fallback: allow if no policy matches, but cache it
            decision = GateDecision(allowed=True, reason="No matching policy found, default allowed")
        else:
            if matching_policy.require_approval:
                # Require manual approval
                decision = GateDecision(
                    allowed=False,
                    reason=f"Manual approval required by policy: {matching_policy.name}",
                    approval_run_id=run_id
                )
            else:
                # Verify conditions
                decision = GateDecision(allowed=True, reason="Policy evaluated allowed")
                conditions = matching_policy.conditions
                
                # Verify "max_file_size" condition if applicable
                if "max_file_size" in conditions:
                    limit = conditions["max_file_size"]
                    size = arguments.get("size")
                    if size is None:
                        content = arguments.get("content")
                        if isinstance(content, str):
                            size = len(content.encode("utf-8"))
                        elif isinstance(content, bytes):
                            size = len(content)
                    if size is not None and size > limit:
                        decision = GateDecision(
                            allowed=False,
                            reason=f"File size ({size} bytes) exceeds policy limit of {limit} bytes"
                        )
                
                # Check general simple conditions (strict equality)
                if decision.allowed:
                    for cond_key, cond_val in conditions.items():
                        if cond_key == "max_file_size":
                            continue
                        if cond_key in arguments:
                            if arguments[cond_key] != cond_val:
                                decision = GateDecision(
                                    allowed=False,
                                    reason=f"Condition '{cond_key}' mismatch: expected '{cond_val}', got '{arguments[cond_key]}'"
                                )
                                break

        # Cache the decision with current timestamp
        self._cache[cache_key] = (decision, now)
        
        # Log to Timeline DB
        self._log_audit_trail(run_id, action, decision.allowed, decision.reason)
        
        return decision
