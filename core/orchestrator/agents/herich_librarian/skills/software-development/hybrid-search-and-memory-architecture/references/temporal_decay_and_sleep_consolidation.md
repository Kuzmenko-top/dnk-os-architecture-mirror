# Temporal Recency Decay & Agentic Sleep Consolidation Architecture

## Overview
In high-velocity multi-agent systems, long-term memory retrieval suffers from two failure modes:
1. **Stale Memory Dominance**: Older memories with high semantic similarity overpower newer, updated user preferences.
2. **Memory Bloat & Noise**: Accumulating raw episodic logs directly into long-term stores results in duplicate facts and degraded retrieval precision.

To solve this without external SaaS dependencies, the unified PostgreSQL memory architecture incorporates **Temporal Recency Decay**, **Agentic Sleep Consolidation**, and **FastAPI / Generative UI integration**.

---

## 1. Temporal Recency Decay Model

### Mathematical Formulation
$$\text{FinalScore}(d) = \text{RRF}(d) \times e^{-\lambda \cdot \Delta t}$$

Where:
- $\text{RRF}(d) = \sum \frac{1}{k + r_j(d)}$ is the hybrid rank fusion score.
- $\lambda > 0$ is the decay constant (e.g., $\lambda = 0.1$ produces a half-life of $\approx 6.93$ days).
- $\Delta t = \frac{t_{\text{current}} - t_{\text{created}}}{86400}$ is the age of the memory in days.

### PostgreSQL Batch Temporal Decay Update
```sql
UPDATE scones_longterm_memories
SET recency_score = exp(-%(decay_lambda)s * EXTRACT(EPOCH FROM (NOW() - created_at)) / 86400.0),
    updated_at = NOW()
WHERE retention_policy = 'forever';
```

---

## 2. Agentic Sleep Consolidation (L2 $\rightarrow$ L3 Semantic Distillation)

Instead of a destructive `DELETE FROM L2 WHERE created_at < 7 days`, sleep consolidation operates in four non-destructive phases:

1. **Selection**: Identify unarchived episodic / working memories older than the consolidation threshold ($T > 7\text{ days}$).
2. **Semantic Clustering & Topic Distillation**: Group memories by semantic topic (e.g., UI preferences, infrastructure constraints, coding conventions).
3. **Structured Fact Extraction**: Use LLM / heuristic distillation to extract persistent, deduplicated declarative facts and entities.
4. **L3 Ingestion & L2 Archival**: Insert distilled facts into `scones_longterm_memories` with `consolidated_from = 'L2'`, and flag source L2 records as `archived = true`.

### Ingestion Flow Diagram
```
[L0: Working Context] 
        ↓ (session end)
[L2: Episodic Memories / Error Solutions]
        ↓ (background sleep cycle / cron consolidation > 7 days)
[LLM Semantic Distillation & Deduplication]
        ↓
[L3: Long-Term Personalized Knowledge (PostgreSQL RRF + Temporal Decay)]
```

---

## 3. Autonomous Sleep Consolidation Worker Implementation

```python
# apps/api/workers/sleep_consolidation_worker.py
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List
from core.scones_l3_memory import SCONESL3Memory

logger = logging.getLogger("scones.sleep_worker")

class SleepConsolidationWorker:
    def __init__(self, scones_l3: SCONESL3Memory | None = None):
        self.scones_l3 = scones_l3 or SCONESL3Memory()
        self.is_running = False

    async def run_consolidation_cycle(self, older_than_days: int = 7) -> Dict[str, Any]:
        """Runs a single consolidation cycle across all active tenants/workspaces."""
        logger.info("Starting Sleep Consolidation Cycle...")
        # 1. Fetch active (user_id, workspace_id) pairs
        # 2. Run consolidate_memories per user with per-user error isolation
        # 3. Apply global temporal decay updates
        await self.scones_l3.apply_temporal_decay()
        return {"status": "completed", "timestamp": datetime.now(timezone.utc).isoformat()}

    async def start(self, interval_hours: int = 24):
        self.is_running = True
        while self.is_running:
            try:
                await self.run_consolidation_cycle()
            except Exception as e:
                logger.error(f"Sleep consolidation error: {e}")
            await asyncio.sleep(interval_hours * 3600)
```

---

## 4. FastAPI REST Router & Generative UI Integration

### REST Endpoints Contract
- `POST /api/v1/memory/l3/store`: Store explicit or extracted long-term memory fact.
- `GET /api/v1/memory/l3/memories`: Hybrid RRF search with Recency Decay weighting.
- `POST /api/v1/memory/l3/consolidate`: On-demand manual or cron trigger for sleep consolidation.
- `GET /api/v1/memory/l3/stats`: Real-time dashboard telemetry (total facts, memory types, avg recency score).

### React Hook Integration Pattern (`useSCONESL3Memory`)
```typescript
import { useSCONESL3Memory } from '@/ui/hooks/useSCONESL3Memory';

export function MemoryManager() {
  const { memories, stats, loading, consolidating, consolidate } = useSCONESL3Memory();
  return (
    <div>
      <button onClick={() => consolidate(7)} disabled={consolidating}>
        🌙 Run Sleep Consolidation
      </button>
      {/* Visual render of memories and recency scores */}
    </div>
  );
}
```
