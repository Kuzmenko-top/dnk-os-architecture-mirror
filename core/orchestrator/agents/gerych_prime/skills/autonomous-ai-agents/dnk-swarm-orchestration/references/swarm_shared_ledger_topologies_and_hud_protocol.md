# --- DNK-MRH-HEADER ---
# mrh_id: "references/swarm_shared_ledger_topologies_and_hud_protocol.md"
# purpose: "Protocol specification for Swarm Shared Memory Ledger, Cognitive Topologies (MoA, Borda Count) and Visual Swarm HUD."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# author: "Gerych Prime & Maksym Kuzmenko"
# --- END DNK-MRH-HEADER ---

# Swarm Shared Memory Ledger, Cognitive Topologies & Visual HUD Protocol

## 1. Swarm Shared Memory Ledger & Artifact Mailbox (`ruflo` Pattern)
- **Module**: `core/orchestrator/swarm_ledger.py`
- **Classes**:
  - `SwarmSharedMemoryLedger`: In-memory thread-safe dictionary cache (`_artifacts`) with JSON persistence to `data/swarm_artifacts/swarm_ledger.json`.
  - `SwarmArtifactMailbox`: Per-agent FIFO mailboxes (`mailboxes/{agent}/`) for asynchronous point-to-point payload passing.
- **Key Features**:
  1. **Deterministic Hashing**: SHA-256 fingerprinting on artifact content (`hashlib.sha256(content.encode()).hexdigest()[:16]`).
  2. **TTL & Expiration**: Automated expiration sweep (`prune_expired()`) preventing stale data accumulation.
  3. **Case-Insensitive Enum Resiliency**: `ArtifactCategory` implements `_missing_` fallback to gracefully handle casing (`LIQUID_SECTION`, `liquid_section`, `schema`, `SCHEMA`) and fallback to `CUSTOM`.

## 2. Cognitive Topologies (`swarms` Pattern)
- **Module**: `core/orchestrator/cognitive_topologies.py`
- **Topologies**:
  1. **Mixture-of-Agents (MoA)**:
     - Multi-layer generation: `proposers` execute concurrently to generate distinct candidate solutions.
     - Aggregator synthesis: An elected lead agent (e.g. `gerych_prime`) synthesizes all candidate outputs into a final coherent artifact.
     - Full provenance: Logs `SWARM_MOA_PROPOSALS_GATHERED` and `SWARM_MOA_SYNTHESIS_COMPLETE` into `audit_trail.ndjson` and saves synthesis in the Ledger.
  2. **Majority Voting & Borda Count**:
     - Deterministic multi-agent ranking of architectural options.
     - Tallying via Borda Count: for $N$ options, rank 1 receives $N$ points, rank 2 receives $N-1$ points, down to 1 point.
     - Deterministic tie-breaking by candidate identifier.
     - Records `SWARM_MAJORITY_VOTING_COMPLETE` with detailed vote distributions in the audit trail.

## 3. Visual Swarm HUD & Live Worktree Inspector
- **Backend API**: `apps/api/routers/swarm_resilience_router.py`
  - `GET /api/v1/swarm/worktrees`: Discovers and returns all active isolated Git worktrees.
  - `GET /api/v1/swarm/audit-trail`: Paginated NDJSON audit event trail with agent/task filtering.
  - `GET /api/v1/swarm/ledger`: Summary of published swarm artifacts.
  - `GET /api/v1/swarm/hud-summary`: High-level aggregated telemetry (worktree counts, Sangha consensus verdicts, circuit breaker health, and ledger volume).
- **Frontend Component**: `apps/web/components/canvas/SwarmHUD.tsx`
  - Floating, collapsable HUD overlay for the Canvas UI.
  - Visual status chips: Sangha Gate (`APPROVED` / `QUARANTINE`), active isolated worktree branches, and live audit event log with timestamps.
