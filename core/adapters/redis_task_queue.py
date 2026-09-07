# --- DNK-MRH-HEADER ---
# mrh_id: "core_adapters_redis_task_queue"
# purpose: "Redis-based Task Queue implementation with prioritization and FIFO within same priority"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-11"
# --- END DNK-MRH-HEADER ---

import json
import time
from typing import Optional, List
from uuid import UUID
import redis

from core.queues.task_queue import TaskQueue
from core.models.collaboration import Task, TaskPriority, TaskStatus

class RedisTaskQueue(TaskQueue):
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0, prefix: str = "dnk_"):
        self.client = redis.Redis(host=host, port=port, db=db, decode_responses=True)
        self.prefix = prefix

    def _task_key(self, task_id: UUID) -> str:
        return f"{self.prefix}task:{task_id}"

    def _queue_key(self, agent_id: UUID) -> str:
        return f"{self.prefix}agent_queue:{agent_id}"

    def _get_priority_weight(self, priority: TaskPriority) -> int:
        weights = {
            TaskPriority.CRITICAL: 4,
            TaskPriority.HIGH: 3,
            TaskPriority.MEDIUM: 2,
            TaskPriority.LOW: 1
        }
        return weights.get(priority, 1)

    def _calculate_score(self, priority: TaskPriority, created_at: int) -> float:
        # score = weight * 10^10 - created_at
        # Newer tasks (larger created_at) will have slightly lower score in the same priority
        return float(self._get_priority_weight(priority) * 1e11 - created_at)

    def enqueue(self, task: Task) -> None:
        task_json = task.model_dump_json()
        self.client.set(self._task_key(task.id), task_json)
        
        score = self._calculate_score(task.priority, task.created_at)
        self.client.zadd(self._queue_key(task.agent_id), {str(task.id): score})

    def dequeue(self, agent_id: UUID) -> Optional[Task]:
        queue_key = self._queue_key(agent_id)
        popped = self.client.zpopmax(queue_key)
        if not popped:
            return None
        
        task_id_str, _ = popped[0]
        task_id = UUID(task_id_str)
        
        task_json = self.client.get(self._task_key(task_id))
        if not task_json:
            return None
        
        task_data = json.loads(task_json)
        task = Task(**task_data)
        task.status = TaskStatus.RUNNING
        task.updated_at = int(time.time())
        
        # Save updated status
        self.client.set(self._task_key(task.id), task.model_dump_json())
        return task

    def get_pending_tasks(self, agent_id: UUID) -> List[Task]:
        queue_key = self._queue_key(agent_id)
        # Get elements sorted by score descending (highest priority first)
        task_ids = self.client.zrevrange(queue_key, 0, -1)
        tasks = []
        for tid in task_ids:
            task_json = self.client.get(self._task_key(UUID(tid)))
            if task_json:
                tasks.append(Task(**json.loads(task_json)))
        return tasks

    def reprioritize(self, task_id: UUID, new_priority: TaskPriority) -> None:
        task_key = self._task_key(task_id)
        task_json = self.client.get(task_key)
        if not task_json:
            return
        
        task = Task(**json.loads(task_json))
        task.priority = new_priority
        task.updated_at = int(time.time())
        
        # Update task payload
        self.client.set(task_key, task.model_dump_json())
        
        # Update sorted set score
        score = self._calculate_score(new_priority, task.created_at)
        self.client.zadd(self._queue_key(task.agent_id), {str(task_id): score})
