# --- DNK-MRH-HEADER ---
# mrh_id: "core_executors_improvement_executor"
# purpose: "Improvement Executor interface and concrete implementation to apply configuration/prompt optimizations"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-11"
# --- END DNK-MRH-HEADER ---

from abc import ABC, abstractmethod
from uuid import UUID, uuid4
from datetime import datetime, UTC
from typing import Dict, Any, Optional

from core.models.improvement import ImprovementPlan
from core.models.timeline import Event
from core.ports.timeline_repository import ITimelineRepository

class ImprovementExecutor(ABC):
    @abstractmethod
    async def execute_plan(
        self,
        plan: ImprovementPlan,
        run_id: UUID,
    ) -> bool:
        pass

class PostgresImprovementExecutor(ImprovementExecutor):
    def __init__(self, repo: ITimelineRepository):
        self.repo = repo
        # Mock active agent configurations registry
        self.agent_configs: Dict[str, Dict[str, Any]] = {}

    async def execute_plan(
        self,
        plan: ImprovementPlan,
        run_id: UUID,
    ) -> bool:
        agent_id_str = str(plan.agent_id)
        if agent_id_str not in self.agent_configs:
            self.agent_configs[agent_id_str] = {
                "prompt": "Default agent prompt",
                "retry_policy": {"max_retries": 3, "backoff": "linear"},
                "timeout": 30,
                "tool_selection": []
            }

        for imp in plan.improvements:
            category = imp.category.lower()
            
            # Apply configuration updates based on suggestion category
            if category == "prompt":
                self.agent_configs[agent_id_str]["prompt"] = imp.suggested_action
            elif category == "retry_policy":
                self.agent_configs[agent_id_str]["retry_policy"] = {
                    "max_retries": 5,
                    "backoff": "exponential",
                    "action": imp.suggested_action
                }
            elif category == "timeout":
                self.agent_configs[agent_id_str]["timeout"] = 60
            elif category == "tool_selection":
                self.agent_configs[agent_id_str]["tool_selection"] = [imp.suggested_action]

            # Log audit trail event into Timeline DB
            event = Event(
                id=uuid4(),
                run_id=run_id,
                event_type="improvement_applied",
                payload={
                    "agent_id": agent_id_str,
                    "improvement": imp.suggested_action,
                    "category": imp.category,
                    "run_id": str(run_id)
                },
                created_at=datetime.now(UTC)
            )
            await self.repo.create_event(event)

        return True
