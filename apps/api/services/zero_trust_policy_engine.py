# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_zero_trust_policy_engine"
# purpose: "Zero-Trust Dynamic RBAC/ABAC Evaluation Engine with Multi-Context Verification (DNK-SECURITY-001 Phase 2)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import fnmatch
import ipaddress
from datetime import datetime, time, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RequestContext(BaseModel):
    subject_id: str
    subject_type: str = "user"  # user, service, agent
    roles: List[str] = Field(default_factory=list)
    trust_score: float = 1.0  # 0.0 to 1.0
    mfa_authenticated: bool = False
    ip_address: str = "127.0.0.1"
    geo_country: Optional[str] = None
    request_time_utc: Optional[datetime] = None
    user_agent: Optional[str] = None
    request_count_last_minute: int = 1
    attributes: Dict[str, Any] = Field(default_factory=dict)


class PolicyEvaluationResult(BaseModel):
    allowed: bool
    decision: str  # "ALLOW" or "DENY"
    matched_policy_id: Optional[str] = None
    matched_policy_name: Optional[str] = None
    reason: str
    required_mfa: bool = False
    context_evaluations: Dict[str, Any] = Field(default_factory=dict)


class ZeroTrustPolicyEngine:
    """
    Evaluates dynamic RBAC + ABAC security policies against incoming request context.
    Default-closed zero-trust model: requests are DENIED unless explicitly matched by an ALLOW policy.
    """

    @staticmethod
    def _matches_pattern(value: str, patterns: List[str]) -> bool:
        if not patterns or "*" in patterns:
            return True
        return any(fnmatch.fnmatch(value, pat) for pat in patterns)

    @staticmethod
    def _is_ip_in_list(ip_str: str, cidr_list: List[str]) -> bool:
        if not cidr_list:
            return False
        try:
            ip_obj = ipaddress.ip_address(ip_str)
            for cidr in cidr_list:
                try:
                    if "/" in cidr:
                        if ip_obj in ipaddress.ip_network(cidr, strict=False):
                            return True
                    else:
                        if ip_obj == ipaddress.ip_address(cidr):
                            return True
                except ValueError:
                    continue
        except ValueError:
            return False
        return False

    @staticmethod
    def _is_within_time_window(current_time_utc: datetime, start_str: Optional[str], end_str: Optional[str]) -> bool:
        if not start_str or not end_str:
            return True
        try:
            start_parts = [int(p) for p in start_str.split(":")]
            end_parts = [int(p) for p in end_str.split(":")]
            t_start = time(start_parts[0], start_parts[1], start_parts[2] if len(start_parts) > 2 else 0)
            t_end = time(end_parts[0], end_parts[1], end_parts[2] if len(end_parts) > 2 else 0)
            cur_t = current_time_utc.time()

            if t_start <= t_end:
                return t_start <= cur_t <= t_end
            else:
                # Overnight window (e.g., 22:00 to 06:00)
                return cur_t >= t_start or cur_t <= t_end
        except Exception:
            return True

    def evaluate(
        self,
        context: RequestContext,
        resource: str,
        action: str,
        policies: List[Dict[str, Any]],
    ) -> PolicyEvaluationResult:
        """
        Evaluates a set of policies against the context, resource, and action.
        Policies are evaluated in priority order (ascending priority number).
        """
        if not policies:
            return PolicyEvaluationResult(
                allowed=False,
                decision="DENIED",
                reason="Default Zero-Trust Deny: No active policies matched the request.",
            )

        # Sort policies by priority (lowest integer = highest priority)
        sorted_policies = sorted(
            [p for p in policies if p.get("is_active", True)],
            key=lambda x: x.get("priority", 100),
        )

        req_time = context.request_time_utc or datetime.now(timezone.utc)

        for pol in sorted_policies:
            pol_id = pol.get("id")
            pol_name = pol.get("policy_name", "Unnamed Policy")
            effect = pol.get("effect", "ALLOW").upper()

            # 1. Resource pattern check
            res_patterns = pol.get("resource_patterns", ["*"])
            if not self._matches_pattern(resource, res_patterns):
                continue

            # 2. Action pattern check
            act_patterns = pol.get("action_patterns", ["*"])
            if not self._matches_pattern(action, act_patterns):
                continue

            # 3. Subject Role match
            sub_roles = pol.get("subject_roles", [])
            if sub_roles and "*" not in sub_roles:
                if not any(r in sub_roles for r in context.roles):
                    continue

            # 4. Subject Type match
            sub_types = pol.get("subject_types", [])
            if sub_types and "*" not in sub_types:
                if context.subject_type not in sub_types:
                    continue

            context_checks: Dict[str, Any] = {}

            # 5. IP Denylist (Immediate violation if matched)
            ip_denylist = pol.get("ip_denylist", [])
            if ip_denylist and self._is_ip_in_list(context.ip_address, ip_denylist):
                return PolicyEvaluationResult(
                    allowed=False,
                    decision="DENIED",
                    matched_policy_id=pol_id,
                    matched_policy_name=pol_name,
                    reason=f"Policy '{pol_name}' DENIED: IP {context.ip_address} is in denylist.",
                    context_evaluations={"ip_denylist_matched": True},
                )

            # 6. IP Allowlist
            ip_allowlist = pol.get("ip_allowlist", [])
            if ip_allowlist:
                if not self._is_ip_in_list(context.ip_address, ip_allowlist):
                    context_checks["ip_allowlist_passed"] = False
                    continue
                context_checks["ip_allowlist_passed"] = True

            # 7. Geo Country restriction
            geo_allowed = pol.get("allowed_geo_countries", [])
            if geo_allowed:
                if not context.geo_country or context.geo_country.upper() not in [g.upper() for g in geo_allowed]:
                    context_checks["geo_passed"] = False
                    continue
                context_checks["geo_passed"] = True

            # 8. Time Window UTC
            t_start = pol.get("time_window_start_utc")
            t_end = pol.get("time_window_end_utc")
            if not self._is_within_time_window(req_time, t_start, t_end):
                context_checks["time_window_passed"] = False
                continue
            context_checks["time_window_passed"] = True

            # 9. Minimum Trust Score
            min_trust = pol.get("min_trust_score")
            if min_trust is not None:
                if context.trust_score < float(min_trust):
                    context_checks["trust_score_passed"] = False
                    continue
                context_checks["trust_score_passed"] = True

            # 10. MFA Requirement
            require_mfa = pol.get("require_mfa", False)
            if require_mfa and not context.mfa_authenticated:
                return PolicyEvaluationResult(
                    allowed=False,
                    decision="DENIED",
                    matched_policy_id=pol_id,
                    matched_policy_name=pol_name,
                    reason=f"Policy '{pol_name}' requires MFA authentication.",
                    required_mfa=True,
                    context_evaluations=context_checks,
                )

            # 11. Request Velocity
            max_velocity = pol.get("max_velocity_rpm")
            if max_velocity is not None:
                if context.request_count_last_minute > max_velocity:
                    return PolicyEvaluationResult(
                        allowed=False,
                        decision="DENIED",
                        matched_policy_id=pol_id,
                        matched_policy_name=pol_name,
                        reason=f"Policy '{pol_name}' DENIED: Request velocity ({context.request_count_last_minute} rpm) exceeds limit of {max_velocity} rpm.",
                        context_evaluations=context_checks,
                    )

            # Decision outcome
            is_allow = effect == "ALLOW"
            return PolicyEvaluationResult(
                allowed=is_allow,
                decision="ALLOWED" if is_allow else "DENIED",
                matched_policy_id=pol_id,
                matched_policy_name=pol_name,
                reason=f"Policy '{pol_name}' applied: {effect}.",
                required_mfa=require_mfa,
                context_evaluations=context_checks,
            )

        return PolicyEvaluationResult(
            allowed=False,
            decision="DENIED",
            reason="Default Zero-Trust Deny: No active policies matched the request context.",
        )
