# --- DNK-MRH-HEADER ---
# mrh_id: "core_config_collaboration_config"
# purpose: "Configuration constants for multi-agent collaboration (limits, retries, weights)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-11"
# --- END DNK-MRH-HEADER ---

from typing import Dict
from core.models.collaboration import TaskPriority

MAX_AGENTS_PER_RUN: int = 10
MAX_RETRY_ATTEMPTS: int = 3

TASK_PRIORITY_WEIGHTS: Dict[TaskPriority, int] = {
    TaskPriority.CRITICAL: 4,
    TaskPriority.HIGH: 3,
    TaskPriority.MEDIUM: 2,
    TaskPriority.LOW: 1,
}

ROLE_ASSIGNMENT_STRATEGY: str = "round_robin"
