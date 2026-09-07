# --- DNK-MRH-HEADER ---
# mrh_id: "core_ports_security_gate_service"
# purpose: "SecurityGateService abstract Port interface standard defining policy evaluations"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-11"
# --- END DNK-MRH-HEADER ---

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from uuid import UUID

from core.models.security import SecurityPolicy, GateDecision

class SecurityGateService(ABC):
    @abstractmethod
    def evaluate_policy(
        self,
        run_id: UUID,
        action: str,
        arguments: Dict[str, Any],
        context: Dict[str, Any],
    ) -> GateDecision:
        pass

    @abstractmethod
    def get_policy(self, policy_id: UUID) -> Optional[SecurityPolicy]:
        pass

    @abstractmethod
    def create_policy(self, policy: SecurityPolicy) -> SecurityPolicy:
        pass
