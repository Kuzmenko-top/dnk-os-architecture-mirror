# --- DNK-MRH-HEADER ---
# mrh_id: "core_services_improvement_security_service"
# purpose: "Security Service to enforce policy evaluations and manual approvals on self-improvement actions"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-11"
# --- END DNK-MRH-HEADER ---

from uuid import UUID
from typing import Dict, Any

from core.models.improvement import ImprovementSuggestion
from core.ports.security_gate_service import SecurityGateService
from core.models.security import GateDecision

class ImprovementSecurityService:
    def __init__(self, gate_service: SecurityGateService):
        self.gate_service = gate_service

    def evaluate_improvement(
        self,
        run_id: UUID,
        suggestion: ImprovementSuggestion,
    ) -> bool:
        """
        Evaluates whether an improvement suggestion can be applied safely.
        Returns True if allowed, False if rejected, or raises an exception if approval is required.
        """
        action = f"improvement.apply.{suggestion.category}"
        arguments = {
            "category": suggestion.category,
            "priority": suggestion.priority,
            "estimated_impact": suggestion.estimated_impact,
            "suggested_action": suggestion.suggested_action
        }
        context = {
            "source": "self_improvement_loop",
            "impact": suggestion.estimated_impact
        }

        # Evaluate policy via the SecurityGateService
        decision: GateDecision = self.gate_service.evaluate_policy(
            run_id=run_id,
            action=action,
            arguments=arguments,
            context=context
        )

        # High impact suggestions or require_approval triggers manual approval demand
        if suggestion.estimated_impact.lower() == "high" or decision.approval_run_id is not None:
            # Under the specification: "якщо require_approval=True -> зачекати на manual approval"
            # We can raise a manual approval exception or return a status indicating "approval_required"
            raise PermissionError(f"Manual approval required for high-impact improvement: {suggestion.suggested_action}")

        if not decision.allowed:
            # "якщо allowed=False -> скасувати покращення."
            return False

        return True
