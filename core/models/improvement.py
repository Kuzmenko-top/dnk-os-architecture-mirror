# --- DNK-MRH-HEADER ---
# mrh_id: "core_models_improvement"
# purpose: "Domain models for the self-improvement loop (RunAnalysis, ImprovementSuggestion, ImprovementPlan)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-11"
# --- END DNK-MRH-HEADER ---

from pydantic import BaseModel
from typing import List, Optional

class ImprovementSuggestion(BaseModel):
    category: str  # "prompt", "retry_policy", "timeout", "tool_selection"
    description: str
    priority: str  # "high", "medium", "low"
    estimated_impact: str  # "high", "medium", "low"
    suggested_action: str  # наприклад, "збільшити timeout для research task"

class RunAnalysis(BaseModel):
    agent_id: str
    total_runs: int
    success_rate: float  # 0.0–1.0
    avg_duration_seconds: float
    common_errors: List[str]
    bottlenecks: List[str]  # наприклад, "task_type=research часто фейлиться"
    suggestions: List[ImprovementSuggestion]

class ImprovementPlan(BaseModel):
    agent_id: str
    improvements: List[ImprovementSuggestion]
    priority_order: List[str]  # ID або опис у порядку виконання
    estimated_total_impact: str
    rollback_plan: str  # як відкотити, якщо щось піде не так
