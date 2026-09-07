# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/workers/sleep_consolidation_worker.py"
# purpose: "Autonomous Background Sleep Consolidation Worker for SCONES L3 Long-Term Memory (L2 -> L3 Semantic Distillation & Temporal Decay)"
# canonical_source: true
# alters_files: []
# triggers_tasks: ["DNK-SCONES-L3-001", "DNK-SCONES-L3-002"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from core.scones_l3_memory import SCONESL3Memory

try:
    from core.memory.pgvector_store import PgVectorStore as PGVectorStore
except ImportError:
    try:
        from core.memory.pgvector_store import PgVectorStore as PGVectorStore
    except ImportError:
        PGVectorStore = None

logger = logging.getLogger("SleepConsolidationWorker")


class SleepConsolidationWorker:
    """
    Background worker that runs periodic sleep consolidation cycles:
    - Distills unarchived episodic memories (>7 days) into L3 semantic facts.
    - Applies temporal recency decay across all long-term memories.
    """

    def __init__(self, pgvector_store: Optional[Any] = None, scones_l3: Optional[SCONESL3Memory] = None):
        self.pgvector = pgvector_store or (PGVectorStore() if PGVectorStore else None)
        self.scones_l3 = scones_l3 or SCONESL3Memory(self.pgvector)

    async def run_consolidation_cycle(self) -> Dict[str, Any]:
        """
        Execute one consolidation cycle (analogous to biological sleep memory replay).
        """
        cycle_start = datetime.now(timezone.utc)
        logger.info(f"[{cycle_start.isoformat()}] Starting SCONES L3 sleep consolidation cycle...")
        consolidated_users = 0
        total_distilled_facts = 0

        # 1. PostgreSQL DB path if pool available
        if self.pgvector and hasattr(self.pgvector, "pool") and self.pgvector.pool:
            try:
                async with self.pgvector.pool.acquire() as conn:
                    users = await conn.fetch(
                        """
                        SELECT DISTINCT user_id, workspace_id
                        FROM scones_memories
                        WHERE archived = false
                          AND created_at < NOW() - INTERVAL '7 days'
                        """
                    )
                    for user_record in users:
                        user_id = str(user_record["user_id"])
                        workspace_id = str(user_record["workspace_id"])
                        try:
                            distilled = await self.scones_l3.consolidate_memories(
                                user_id=user_id,
                                workspace_id=workspace_id,
                            )
                            consolidated_users += 1
                            total_distilled_facts += len(distilled)
                        except Exception as e:
                            logger.error(f"Error consolidating for user {user_id}: {e}")
            except Exception as e:
                logger.warning(f"PostgreSQL connection error during consolidation cycle: {e}")

        # 2. In-memory / Fallback path
        distinct_pairs = set(
            (str(m.get("user_id")), str(m.get("workspace_id")))
            for m in self.scones_l3._in_memory_l2_store
            if not m.get("archived", False)
        )
        for u_id, ws_id in distinct_pairs:
            distilled = await self.scones_l3.consolidate_memories(user_id=u_id, workspace_id=ws_id)
            if distilled:
                consolidated_users += 1
                total_distilled_facts += len(distilled)

        # 3. Apply temporal decay to all L3 memories
        decay_updates = await self.scones_l3.apply_temporal_decay()

        cycle_end = datetime.now(timezone.utc)
        duration_sec = (cycle_end - cycle_start).total_seconds()
        logger.info(f"[{cycle_end.isoformat()}] Consolidation complete in {duration_sec:.2f}s.")

        return {
            "status": "completed",
            "consolidated_users": consolidated_users,
            "distilled_facts": total_distilled_facts,
            "decay_updates": decay_updates,
            "duration_sec": duration_sec,
        }

    async def start(self, interval_hours: float = 24.0, max_cycles: Optional[int] = None):
        """
        Run continuous daemon worker loop with interval.
        """
        cycles_run = 0
        while True:
            await self.run_consolidation_cycle()
            cycles_run += 1
            if max_cycles and cycles_run >= max_cycles:
                break
            await asyncio.sleep(interval_hours * 3600)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    worker = SleepConsolidationWorker()
    asyncio.run(worker.start(interval_hours=24.0))
