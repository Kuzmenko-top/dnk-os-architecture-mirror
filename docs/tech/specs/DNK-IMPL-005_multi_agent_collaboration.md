# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-IMPL-005_multi_agent_collaboration"
# purpose: "Technical Specification and Documentation for Multi-Agent Collaboration & Self-Healing"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-11"
# --- END DNK-MRH-HEADER ---

# DNK-IMPL-005: Multi-Agent Collaboration Technical Specification

This document specifies the architecture, models, interfaces, and concrete implementations of the Multi-Agent Collaboration engine inside the DNK OS MVP.

---

## 1. Task Queues

The system defines a decoupled Hexagonal Port `TaskQueue` that handles concurrent agent operations with prioritization and FIFO ordering within same priority classes.

### 1.1 Interfaces and Models

Located at `core/queues/task_queue.py` and `core/models/collaboration.py`.

```python
from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID
from core.models.collaboration import Task, TaskPriority

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
```

### 1.2 Implementations
- **RedisTaskQueue** (`core/adapters/redis_task_queue.py`): Redis-based prioritized queue using Sorted Sets (`ZSET`).
- **PostgresTaskQueue** (`core/adapters/postgres_task_queue.py`): PostgreSQL-based queue using `FOR UPDATE SKIP LOCKED` for lock-free high concurrency.

---

## 2. Agent Coordinator

The Agent Coordinator ports and concrete adapter handle agent assignment, task distribution (using round-robin load-balancing) and resilient recovery loops.

### 2.1 Interface

Located at `core/coordinators/agent_coordinator.py`.

```python
from abc import ABC, abstractmethod
from typing import List, Dict
from uuid import UUID
from core.models.collaboration import AgentRole, Task

class AgentCoordinator(ABC):
    @abstractmethod
    def assign_role(self, agent_id: UUID, role: AgentRole) -> None:
        pass

    @abstractmethod
    def distribute_tasks(self, tasks: List[Task], agents: List[UUID]) -> Dict[UUID, List[Task]]:
        pass

    @abstractmethod
    def handle_failures(self, failed_tasks: List[Task]) -> List[Task]:
        pass
```

---

## 3. Integration with LangGraph & crewAI

Located at `core/adapters/langgraph_crewai_coordinator.py`.

The `LangGraphCrewAICoordinator` compiles a stateful execution graph using `DNKLangGraphAdapter` and maps nodes to persona-driven `DNKCrewAgent` instances.
Nodes dequeue role-specific tasks, execute them sequentially via crewAI protocols, and gracefully handle failover recovery.

---

## 4. Self-Healing Architecture

When a collaborative task fails:
1. **Adaptive Retry**: The coordinator allows up to `3` retries. The task's status is reset to `PENDING` and re-queued.
2. **Reassignment**: If retries are exhausted, the coordinator finds another agent with the same role and reassigns the task.
3. **Escalation**: If no eligible agent is available, the task is escalated to an Orchestrator agent.
4. **Audit Trail Logging**: Each phase of the lifecycle transition is persisted as an Event in the `timeline` schema database with types: `task_failed`, `task_retried`, `task_reassigned`, `task_escalated`.

---

## 5. Configuration

Located at `core/config/collaboration_config.py`.

Key parameters:
- `MAX_AGENTS_PER_RUN` (default: 10)
- `MAX_RETRY_ATTEMPTS` (default: 3)
- `ROLE_ASSIGNMENT_STRATEGY` (default: "round_robin")

---

## 6. Verification and Tests

Located at `tests/verification/test_multi_agent_collaboration.py`.

The suite covers:
1. `test_enqueue_dequeue` - prioritised task queues.
2. `test_assign_role` - role mappings.
3. `test_distribute_tasks` - round-robin and priority task routing.
4. `test_handle_failures_retry` - retry transition.
5. `test_handle_failures_reassign` - peer failover transition.
6. `test_handle_failures_escalate` - orchestrator escalation transition.
7. `test_langgraph_crewai_integration` - end-to-end adapters pipeline.
8. `test_audit_trail` - real PostgreSQL schema event logging and validation.
