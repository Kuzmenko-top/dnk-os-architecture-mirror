# --- DNK-MRH-HEADER ---
# mrh_id: "core_queues_task_queue"
# purpose: "Abstract interface (Port) defining all operations on multi-agent task queue"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-11"
# --- END DNK-MRH-HEADER ---

from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from core.models.collaboration import Task, TaskPriority, TaskStatus

class TaskQueue(ABC):
    @abstractmethod
    def enqueue(self, task: Task) -> None:
        pass

    @abstractmethod
    def dequeue(self, agent_id: UUID) -> Optional[Task]:
        pass

    @abstractmethod
    def get_pending_tasks(self, agent_id: UUID) -> List[Task]:
        pass

    @abstractmethod
    def reprioritize(self, task_id: UUID, new_priority: TaskPriority) -> None:
        pass
