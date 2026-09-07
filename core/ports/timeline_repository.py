# --- DNK-MRH-HEADER ---
# mrh_id: "core_ports_timeline_repository"
# purpose: "Repository interface (Port) defining all operations on agent executions timeline"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-08-11"
# --- END DNK-MRH-HEADER ---

from typing import Optional, List, Protocol
from uuid import UUID

from core.models.timeline import Agent, Run, Task, Event

class ITimelineRepository(Protocol):
    async def create_agent(self, agent: Agent) -> Agent:
        ...

    async def get_agent(self, agent_id: UUID) -> Optional[Agent]:
        ...

    async def create_run(self, run: Run) -> Run:
        ...

    async def get_run(self, run_id: UUID) -> Optional[Run]:
        ...

    async def get_runs_by_agent(self, agent_id: UUID, limit: int = 50) -> List[Run]:
        ...

    async def create_task(self, task: Task) -> Task:
        ...

    async def get_task(self, task_id: UUID) -> Optional[Task]:
        ...

    async def get_tasks_by_run(self, run_id: UUID, limit: int = 100) -> List[Task]:
        ...

    async def create_event(self, event: Event) -> Event:
        ...

    async def get_events_by_run(self, run_id: UUID, limit: int = 200) -> List[Event]:
        ...

    async def get_events_by_task(self, task_id: UUID, limit: int = 100) -> List[Event]:
        ...
