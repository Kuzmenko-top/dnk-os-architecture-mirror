# --- DNK-MRH-HEADER ---
# mrh_id: "core_generators_improvement_generator"
# purpose: "Improvement Generator interface and concrete implementation to synthesize improvement plans"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-11"
# --- END DNK-MRH-HEADER ---

from abc import ABC, abstractmethod
from typing import List

from core.models.improvement import ImprovementSuggestion, ImprovementPlan

class ImprovementGenerator(ABC):
    @abstractmethod
    def generate_plan(
        self,
        agent_id: str,
        suggestions: List[ImprovementSuggestion],
    ) -> ImprovementPlan:
        pass

class HeuristicImprovementGenerator(ImprovementGenerator):
    def generate_plan(
        self,
        agent_id: str,
        suggestions: List[ImprovementSuggestion],
    ) -> ImprovementPlan:
        # Priority mapping for sorting
        priority_map = {"high": 3, "medium": 2, "low": 1}
        
        # Sort suggestions by priority descending
        sorted_suggestions = sorted(
            suggestions,
            key=lambda x: priority_map.get(x.priority.lower(), 0),
            reverse=True
        )

        # Generate priority order list
        priority_order = [s.suggested_action for s in sorted_suggestions]

        # Determine total impact
        impact_levels = [s.estimated_impact.lower() for s in suggestions]
        if "high" in impact_levels:
            estimated_total_impact = "high"
        elif "medium" in impact_levels:
            estimated_total_impact = "medium"
        else:
            estimated_total_impact = "low"

        rollback_plan = (
            "Для відкату змін необхідно повернути попереднє значення конфігурації у файлі "
            f"improvement_config або конфігурації агента {agent_id}."
        )

        return ImprovementPlan(
            agent_id=agent_id,
            improvements=sorted_suggestions,
            priority_order=priority_order,
            estimated_total_impact=estimated_total_impact,
            rollback_plan=rollback_plan
        )
