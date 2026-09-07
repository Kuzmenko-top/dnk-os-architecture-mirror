# --- DNK-MRH-HEADER ---
# mrh_id: "core_services_timeline_knowledge_service"
# purpose: "Service for analyzing successful executions from Timeline DB and synthesizing knowledge records"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-11"
# --- END DNK-MRH-HEADER ---

import time
from typing import List
from uuid import UUID, uuid4

from core.models.knowledge import KnowledgeDocument
from core.ports.timeline_repository import ITimelineRepository
from core.stores.knowledge_store import KnowledgeStore
from core.services.rag_service import DNKRagService

class TimelineKnowledgeService:
    def __init__(self, timeline_repo: ITimelineRepository, knowledge_store: KnowledgeStore, rag_service: DNKRagService):
        self.timeline_repo = timeline_repo
        self.knowledge_store = knowledge_store
        self.rag_service = rag_service

    async def analyze_and_generate_knowledge(self, agent_id: UUID) -> List[KnowledgeDocument]:
        """
        Analyzes successful runs for a specific agent, extracts tasks, synthesizes best practices, and saves them to knowledge base.
        """
        generated_docs: List[KnowledgeDocument] = []
        
        # 1. Fetch runs for the agent
        runs = await self.timeline_repo.get_runs_by_agent(agent_id, limit=50)
        
        for run in runs:
            # We analyze successful runs
            if run.status != "completed":
                continue
                
            # 2. Get completed tasks under this run
            tasks = await self.timeline_repo.get_tasks_by_run(run.id, limit=100)
            
            for task in tasks:
                if task.status != "completed":
                    continue
                
                # 3. Synthesize structured knowledge / best practice content
                content = (
                    f"Knowledge: Successful execution of '{task.task_type}' task in run {run.id}. "
                    f"Payload: {task.payload}. Result: {task.result}. "
                    f"Recommended best practice: Optimize payload structure and implement strict validation guards."
                )
                
                # Compute embedding
                embedding = self.rag_service._get_embedding(content)
                
                # Create knowledge document
                doc = KnowledgeDocument(
                    id=uuid4(),
                    content=content,
                    embedding=embedding,
                    metadata={
                        "source": "timeline",
                        "run_id": str(run.id),
                        "agent_id": str(run.agent_id),
                        "task_id": str(task.id),
                        "task_type": task.task_type
                    },
                    created_at=int(time.time()),
                    updated_at=int(time.time())
                )
                
                # 4. Save to knowledge store
                self.knowledge_store.upsert_document(doc)
                generated_docs.append(doc)
                
        return generated_docs
