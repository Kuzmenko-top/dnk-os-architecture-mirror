# --- DNK-MRH-HEADER ---
# mrh_id: "core/task_forest/stages.py"
# purpose: "Execution stages, lifecycle state transitions, and stage metrics."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

from enum import Enum
from typing import List, Dict
from datetime import datetime
from core.task_forest.models import ExecutionStage, TaskNode


class StageTransition(str, Enum):
    BACKLOG_TO_PLANNED = "backlog_to_planned"
    PLANNED_TO_IN_PROGRESS = "planned_to_in_progress"
    IN_PROGRESS_TO_REVIEW = "in_progress_to_review"
    REVIEW_TO_DONE = "review_to_done"
    REVIEW_TO_IN_PROGRESS = "review_to_in_progress"  # Reopen
    IN_PROGRESS_TO_BACKLOG = "in_progress_to_backlog"  # Deprioritize


class StageManager:
    """
    Manages task execution stage transitions and validation rules.
    """

    def __init__(self):
        self.valid_transitions: Dict[ExecutionStage, List[ExecutionStage]] = {
            ExecutionStage.BACKLOG: [ExecutionStage.PLANNED],
            ExecutionStage.PLANNED: [ExecutionStage.IN_PROGRESS, ExecutionStage.BACKLOG],
            ExecutionStage.IN_PROGRESS: [ExecutionStage.REVIEW, ExecutionStage.BACKLOG],
            ExecutionStage.REVIEW: [ExecutionStage.DONE, ExecutionStage.IN_PROGRESS],
            ExecutionStage.DONE: [],  # Terminal state
        }

    def can_transition(self, from_stage: ExecutionStage, to_stage: ExecutionStage) -> bool:
        """
        Check if transition from one stage to another is permitted.
        """
        allowed = self.valid_transitions.get(from_stage, [])
        return to_stage in allowed

    def transition(self, node: TaskNode, to_stage: ExecutionStage) -> bool:
        """
        Transition node to new stage. Returns True if successful.
        """
        if not self.can_transition(node.stage, to_stage):
            return False

        now = datetime.now()
        node.stage = to_stage
        node.updated_at = now

        if to_stage == ExecutionStage.DONE:
            node.completed_at = now
        else:
            node.completed_at = None

        return True

    def get_stage_stats(self, nodes: List[TaskNode]) -> Dict[str, int]:
        """
        Get count of nodes in each stage.
        """
        stats = {stage.value: 0 for stage in ExecutionStage}
        for node in nodes:
            stats[node.stage.value] = stats.get(node.stage.value, 0) + 1
        return stats
