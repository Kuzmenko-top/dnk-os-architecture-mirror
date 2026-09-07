# --- DNK-MRH-HEADER ---
# mrh_id: "core_flows_research_write_validate"
# purpose: "Simple agent flow (Research -> Write -> Validate) with resilient Timeline DB persistence and Security Gate audit"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import asyncio
import os
import time
from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

import asyncpg
from core.models.timeline import Event
from core.adapters.postgres_timeline_repository import PostgresTimelineRepository
from core.config.timeline_config import DATABASE_URL
from core.decorators.security_gate import get_security_gate_service, SecurityGateDenied

# In-memory backup of events in case PostgreSQL is not available
GLOBAL_EVENTS_LOG: List[Dict[str, Any]] = []

# Persistent pool and availability cache to prevent timeout hangs
_DB_POOL: Optional[asyncpg.Pool] = None
_DB_LAST_CHECK_TIME: float = 0.0
_DB_IS_AVAILABLE: bool = True
_DB_RETRY_INTERVAL: float = 10.0  # seconds between reconnection attempts if down

async def get_or_create_pool() -> Optional[asyncpg.Pool]:
    """Resilient pool manager with fast fail-check."""
    global _DB_POOL, _DB_LAST_CHECK_TIME, _DB_IS_AVAILABLE
    
    current_time = time.time()
    
    # If known to be down recently, fail-fast without hanging
    if not _DB_IS_AVAILABLE and (current_time - _DB_LAST_CHECK_TIME) < _DB_RETRY_INTERVAL:
        return None

    if _DB_POOL is not None and not _DB_POOL._closed:
        return _DB_POOL

    try:
        _DB_LAST_CHECK_TIME = current_time
        # Use short timeout (1.0s) so unreachability does not cause broken pipe
        _DB_POOL = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=1,
            max_size=5,
            command_timeout=5,
            timeout=1.0
        )
        _DB_IS_AVAILABLE = True
        return _DB_POOL
    except Exception as e:
        _DB_IS_AVAILABLE = False
        _DB_LAST_CHECK_TIME = current_time
        _DB_POOL = None
        return None

async def try_save_event(event: Event) -> bool:
    """Saves event to in-memory audit log and attempts Postgres persistence.
    
    Returns:
        bool: True if persisted to PostgreSQL, False if safely buffered in memory.
    """
    # 1. Always save to in-memory audit log
    GLOBAL_EVENTS_LOG.append({
        "id": str(event.id),
        "run_id": str(event.run_id),
        "task_id": str(event.task_id) if event.task_id else None,
        "event_type": event.event_type,
        "payload": event.payload,
        "created_at": event.created_at.isoformat()
    })
    
    # 2. Try to write to Postgres
    try:
        pool = await get_or_create_pool()
        if pool:
            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO timeline.agents (id, name, created_at, updated_at)
                    VALUES ($1, $2, NOW(), NOW())
                    ON CONFLICT (id) DO NOTHING;
                """, event.run_id, "Visual Shell Agent")
                
                await conn.execute("""
                    INSERT INTO timeline.runs (id, agent_id, run_type, status, created_at, updated_at)
                    VALUES ($1, $1, $2, $3, NOW(), NOW())
                    ON CONFLICT (id) DO NOTHING;
                """, event.run_id, "agent_flow", "running")
            
            repo = PostgresTimelineRepository(pool)
            await repo.create_event(event)
            return True
    except Exception as e:
        # Graceful non-crashing audit bypass
        pass
        
    return False

async def run_flow(run_id: UUID, canvas_id: UUID, query: str) -> Dict[str, Any]:
    """Executes the research_write_validate flow and returns structured execution & persistence metadata."""
    trace_id = str(uuid4())
    all_persisted = True

    # 1. Flow Started
    started_event = Event(
        id=uuid4(),
        run_id=run_id,
        event_type="flow_started",
        payload={"canvas_id": str(canvas_id), "query": query, "trace_id": trace_id},
        created_at=datetime.now(timezone.utc)
    )
    if not await try_save_event(started_event):
        all_persisted = False

    # 2. Research Step
    await asyncio.sleep(0.05)  # Simulate fast async research
    research_results = f"SOTA Research results for query '{query}': Visual Shell is an interactive canvas that syncs with Timeline DB and enforces Security Gate rules."
    
    research_event = Event(
        id=uuid4(),
        run_id=run_id,
        event_type="research_completed",
        payload={"canvas_id": str(canvas_id), "results": research_results, "trace_id": trace_id},
        created_at=datetime.now(timezone.utc)
    )
    if not await try_save_event(research_event):
        all_persisted = False

    # 3. Write Step & Validate loop
    attempts = 0
    max_attempts = 3
    artifact_content = ""
    
    while attempts < max_attempts:
        attempts += 1
        
        # Simulate writing
        artifact_content = f"# Artifact for {query}\n\nThis is a SOTA AI generated document based on research.\n\n## Details\n{research_results}\n\nGenerated at: {datetime.now(timezone.utc).isoformat()}"
        if attempts == 1 and "invalid" in query.lower():
            # Force validation failure for testing on first attempt
            artifact_content = "Short text"

        # Risky Action: Update Artifact -> MUST EVALUATE THROUGH SECURITY GATE
        gate = get_security_gate_service()
        decision = gate.evaluate_policy(
            run_id=run_id,
            action="artifact.update",
            arguments={"canvas_id": str(canvas_id), "content": artifact_content},
            context={"trace_id": trace_id}
        )
        
        if not decision.allowed:
            raise SecurityGateDenied(f"Security Gate Denied: {decision.reason}")

        write_event = Event(
            id=uuid4(),
            run_id=run_id,
            event_type="write_completed",
            payload={"canvas_id": str(canvas_id), "content": artifact_content, "attempt": attempts, "trace_id": trace_id},
            created_at=datetime.now(timezone.utc)
        )
        if not await try_save_event(write_event):
            all_persisted = False

        # 4. Validate Step
        is_valid = len(artifact_content) > 50
        
        validate_event = Event(
            id=uuid4(),
            run_id=run_id,
            event_type="validate_completed",
            payload={"canvas_id": str(canvas_id), "is_valid": is_valid, "attempt": attempts, "trace_id": trace_id},
            created_at=datetime.now(timezone.utc)
        )
        if not await try_save_event(validate_event):
            all_persisted = False

        if is_valid:
            break

    # 5. Flow Completed
    completed_event = Event(
        id=uuid4(),
        run_id=run_id,
        event_type="flow_completed",
        payload={"canvas_id": str(canvas_id), "final_content": artifact_content, "trace_id": trace_id},
        created_at=datetime.now(timezone.utc)
    )
    if not await try_save_event(completed_event):
        all_persisted = False

    persistence_status = "persisted" if all_persisted else "degraded"
    audit_status = "recorded" if all_persisted else "deferred"

    return {
        "content": artifact_content,
        "trace_id": trace_id,
        "persistence_status": persistence_status,
        "audit_status": audit_status
    }
