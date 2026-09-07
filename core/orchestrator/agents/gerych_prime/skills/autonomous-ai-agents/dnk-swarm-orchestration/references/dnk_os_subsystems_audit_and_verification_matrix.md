# --- DNK-MRH-HEADER ---
# mrh_id: "skills/autonomous-ai-agents/dnk-swarm-orchestration/references/dnk_os_subsystems_audit_and_verification_matrix.md"
# purpose: "Technical audit findings, verified codebase realities, and DoD verification matrix for DNK OS 11 subsystems."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-04"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 🔍 DNK OS 11 Subsystems Audit & Technical Verification Matrix

## 1. Executive Summary & Verification Method
During system architectural reviews, verify code state directly against real AST, package manifests, and test suites rather than relying on design intent or narrative summaries.

## 2. Fact-Checked Audit Findings (Subsystem Invariants)

### Q1. Orchestrator Engine (`swarm_orchestrator.py` vs LangGraph)
- **Current Runtime**: Custom high-velocity Supervisor-Worker engine (`core/swarm_orchestrator.py`, `core/swarm_engine.py`) optimized for sub-0.05s dispatch and memory isolation (`tenant_id`, `workspace_id`).
- **Telemetry**: Integrated with **Langfuse** via `core/accounting_engine.py` for token, latency, and cost telemetry.
- **Architectural Policy**: Keep custom engine for sub-50ms canvas micro-tasks; encapsulate long-running multi-turn human-in-the-loop flows with a LangGraph stategraph adapter when PostgreSQL time-travel checkpointing is required.

### Q2. 14 Swarm Agents & Test Coverage
- **Monorepo Test Count**: >305 unit and integration test files (275 in `tests/`, 30 in `core/tests/`).
- **Live vs Mock Policy**: In CI/CD, external paid APIs (Shopify Admin GraphQL, Vertex AI, Gemini) are mocked via fixtures to ensure zero token leakage and deterministic execution. Real execution suites are segregated (e.g. `npm run test:live` in `@dnk/video-audit-core`).

### Q3. React Flow Canvas Implementation
- **Package Version**: Modern `@xyflow/react: ^12.11.2` (React Flow v12).
- **Core Canvas Engine**: `apps/web/components/canvas/CanvasEngine.tsx` with `<Background variant={BackgroundVariant.Dots} />`, `<Controls />`, and `<MiniMap />`.
- **Custom Nodes**: 25 specialized node types in `apps/web/components/canvas/nodes/` (Strategy, Shopify theme, Storyboard, Remotion, Live Web Preview, Whiteboard).
- **Interactivity**: HTML5 Drag-and-Drop spawning with `screenToFlowPosition`, Undo/Redo state management, and Obsidian `.canvas` JSON compliance.

### Q4. SCONES Memory Tiering
- **L1 (Fast Context)**: In-memory Inverted Index (<5ms) for token filtering and active agent context.
- **L2 (Vector Store)**: PostgreSQL `pgvector` store (`core/memory/pgvector_store.py`) with HNSW indexing and cosine similarity.
- **L3 (Cognitive Consolidation)**: `core/scones_l3_memory.py` utilizing:
  - **RRF (Reciprocal Rank Fusion)**: Hybrid search combining dense embeddings and BM25 sparse lexical tokens.
  - **Temporal Decay**: Exponential recency decay ($\lambda = 0.1$, half-life ~7 days).
  - **Sleep Consolidation**: Agentic background distillation from L2 logs into durable long-term heuristics.

### Q5. Two-Track Knowledge Assimilation
- **Automated Pipeline**: `core/dna_assimilation.py` executes 4 steps: Search SOTA → License Compliance (Track 1 MIT/Apache vs Track 2 GPL clean-room) → AST Pattern Extraction → Knowledge Ingestion.
- **Obsidian Task Forest**: Tested via `services/dnk_obsidian_task_forest/tests/` to reflect execution DAGs directly in the user vault.

### Q6. Social Media Video Audit Engine
- **Engine Core**: `@dnk/video-audit-core` with dedicated Vitest suites.
- **Frame Deduplication**: Hash and keyframe dedup reduces visual LLM frames by 5-10x, bringing hook analysis (0-3s) latency to 2-4 seconds.
- **Speech Benchmark**: WhisperX adapter verified on Ukrainian terminology (>= 80% niche recall).

### Q7. Programmatic Video (Remotion)
- **Player Component**: `apps/web/components/canvas/RemotionPlayer.tsx` providing 30 fps timeline scrubbing and 9:16 Shorts preview.
- **Storyboard Node**: `VideoStoryboardNoteNode.tsx` managing scene script generation, audio prompts, and rendering dispatch.

### Q8. Shopify Canvas Synchronization
- **Client & AST**: `apps/web/lib/api/shopify_canvas_client.ts` parsing theme structures (layout, templates, sections, snippets) into canvas nodes.
- **Safety**: Guarded by `dnk_shopify_validate_liquid` to prevent theme corruption.

### Q9. Accounting & CRM Integration
- **Accounting Engine**: `core/accounting_engine.py` tracks AI model costs, token usage, and Langfuse tracing.
- **CRM Invariant**: API-level analytics routers exist (`capacity_analytics_router.py`), but visual CRM deal/customer nodes on the canvas are designated for Phase 3.

## 3. Master Subsystem Verification Matrix (DoD)

| Subsystem | Verified Asset | Pass Criteria | Verification Command / Target |
|---|---|---|---|
| **Swarm Orchestrator** | `core/swarm_orchestrator.py` | Sub-0.05s dispatch, Langfuse tracing | `pytest tests/test_swarm_parallel_and_adversarial.py` |
| **Swarm Agents** | `core/orchestrator/agents/` | 100% green unit suites | `pytest tests/test_swarm_resilience.py` |
| **Canvas Engine** | `apps/web/components/canvas/` | `@xyflow/react` v12, 25 nodes, Drag-n-drop | `apps/web/package.json` |
| **SCONES Memory** | `core/scones_l3_memory.py` | pgvector, RRF, Temporal Decay | `pytest core/tests/test_scones_memory.py` |
| **Two-Track Assimilation**| `core/dna_assimilation.py` | AST parsing, License segregation | `pytest tests/test_dna_assimilation.py` |
| **Video Audit** | `packages/video-audit-core` | Frame dedup, Ukrainian speech benchmark | `npm test` inside `packages/video-audit-core` |
| **Remotion Video** | `apps/web/components/canvas/nodes/VideoStoryboardNoteNode.tsx` | 30fps scrub, aspect ratio switcher | TypeScript verification |
| **Shopify Theme Sync** | `apps/web/lib/api/shopify_canvas_client.ts` | Theme section AST parsing | `apps/web/` build verification |
| **Obsidian Knowledge Sync**| `services/dnk_obsidian_task_forest` | MRH headers, YAML frontmatter, [[links]] | `pytest services/dnk_obsidian_task_forest/tests/` |
