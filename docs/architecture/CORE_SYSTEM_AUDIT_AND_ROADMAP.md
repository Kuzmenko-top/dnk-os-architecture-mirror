# --- DNK-MRH-HEADER ---
# mrh_id: "docs/architecture/CORE_SYSTEM_AUDIT_AND_ROADMAP.md"
# purpose: "Comprehensive Architectural Audit, Subsystem Topology & Strategic Refactoring Roadmap for DNK_HUB/core."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-04"
# author: "DNK-e.com Maksym & Gerych"
# --- END DNK-MRH-HEADER ---

# 🏛️ Comprehensive Architectural Audit & Refactoring Roadmap: DNK_HUB/core

**Date**: 2026-09-04  
**Auditor**: Gerych (Hermes Prime)  
**Target Scope**: `/core` (Full Recursion & All Nested Subsystems)  
**System Base**: DNK OS MVP (`DNK_HUB`)

---

## 📊 1. Executive Summary & Core Metrics

The `/core` directory constitutes the central intelligence, memory, coordination, and execution kernel of DNK OS. However, progressive scaling and multiple version iterations have introduced severe technical debt, untracked duplicate frameworks, runtime state leakage, and structural fragmentation.

### Key Quantitative Findings:
- **Total Physical Subdirectories**: `14,838`
- **Total Files in `/core`**: `108,034` files
- **Total Disk Space**: `3,053.86 MB (~3.05 GB)`
- **True Production Code (excl. Hermes Agent & Caches)**: `~22,000 LOC (~3.2 MB)`
- **Untracked Duplicate Hermes Runtimes**: `77,248 files | 1,357.6 MB (~1.36 GB)`
- **Leaked Runtime Databases & Caches in Agent Cards**: `1,164 MB (~1.16 GB)`
- **Dead / Orphaned Directories**: `core/workers`, `core/media`, `core/core`
- **Collection Failures in `core/tests/`**: Missing `langfuse` fallback blocking test discovery.

```
+-----------------------------------------------------------------------------------------+
|                                    CORE DISK FOOTPRINT                                  |
+-----------------------------------------------------------------------------------------+
| [■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■] Hermes Duplicates (Backup/Staging/Versions): 1.36 GB   |
| [■■■■■■■■■■■■■■■■■■■■■■■■■]     Agent Runtime States & Cache (DBs, LSP, Bin): 1.16 GB   |
| [■■■■■■■■■■]                    Active Hermes Runtime (core/hermes_agent): 0.48 GB      |
| [■]                             Actual DNK OS Core Logic & Bricks: ~0.05 GB (50 MB)     |
+-----------------------------------------------------------------------------------------+
```

---

## 🗺️ 2. Architectural Topology & Subsystem Categorization

The active code in `core` logically maps into **6 Core Functional Domains**:

```
                                  +------------------------------------+
                                  |         DNK OS CORE KERNEL         |
                                  |    FastMCP / OmniRouter / Events   |
                                  +-----------------+------------------+
                                                    |
         +--------------------+---------------------+--------------------+---------------------+
         |                    |                     |                    |                     |
+--------v-------+   +--------v-------+    +--------v-------+   +--------v-------+    +--------v-------+
|   1. RUNTIME   |   |   2. MEMORY    |    |   3. SWARM     |   |  4. RESILIENCE |    |   5. BRICKS    |
|   & TELEMETRY  |   |    (SCONES)    |    | & ORCHESTRATION|   |   & SECURITY   |    |  & ACCELERATORS|
+----------------+   +----------------+    +----------------+   +----------------+    +----------------+
| kernel.py      |   | scones_memory  |    | swarm_engine   |   | error_distill  |    | bricks/ 01-06  |
| hermes_runtime |   | scones_l3      |    | swarm_orch.    |   | model_proxy    |    | canvas_engine  |
| omni_router    |   | visual_context |    | task_engine    |   | patent_shield  |    | dna_assimilate |
| local_telemetry|   | core/memory/   |    | orchestrator/  |   | security/      |    | pattern_synth  |
| service_reg.   |   | stores/        |    | agent_factory/ |   | decorators/    |    | video/         |
+----------------+   +----------------+    +----------------+   +----------------+    +----------------+
```

### Domain 1: Microkernel, Runtime & Event Mesh
- **`kernel.py`**: The `FastMCPKernel` foundational runtime providing MCP server endpoints, event pub/sub, and task execution lifecycle.
- **`hermes_runtime.py`**: Subprocess supervisor managing Hermes CLI background processes, health monitoring, and IPC.
- **`runtime_events.py`**: Strongly typed event contracts (`SystemEvent`, `TaskEvent`, `AgentErrorEvent`) for cross-service hooks.
- **`omni_router.py`**: Unified routing layer for dynamic request dispatch across toolchains and LLM models.
- **`service_registry.py`**: In-memory registry tracking available services, status, and health checks.
- **`local_telemetry.py`**: Tracing, span collection, and latency metrics without external telemetry dependencies.
- **`accounting_engine.py`**: Cost accounting and token attribution. *(Issue: Hard import of `langfuse` fails if not installed).*

### Domain 2: Cognitive Memory & Perception Engine (SCONES)
- **`scones_memory.py`**: L1/L2 short-term cognitive memory, sliding context windows, and tenant isolation (`ws-alpha-001`).
- **`scones_l3_memory.py`**: L3 long-term persistent deep knowledge repository with hybrid semantic search.
- **`core/memory/`**: Provider implementations (`memory_manager.py`, `scones_provider.py`, `tencent_memory_provider.py`, `pgvector_store.py`).
- **`visual_context.py`**: Multi-modal visual analysis, screenshot comprehension, and layout recognition.
- **`core/stores/`**: `knowledge_store.py` interface.

### Domain 3: Swarm Intelligence & Multi-Agent Orchestration
- **`swarm_engine.py` & `swarm_orchestrator.py`**: Multi-agent coordination, lifecycle management, and DAG dependency graph execution.
- **`core/orchestrator/`**:
  - `swarm_coordinator.py`: High-level dispatching to specialized agents.
  - `agents/`: 14 defined agent profiles (`gerych_prime`, `herich_librarian`, `gerych_builder`, `gerych_researcher`, `dnk_shopify`, `dnk_dev_fullstack`, `dnk_security_guard`, `dnk_scones_memory`, `dnk_video_ai_creator`, `dnk_finance_cfo`, `dnk_marketing_cmo`, `dnk_erp_supply`, `dnk_analytics`, `gerych_auditor`).
- **`core/agent_factory/`**: Factory generating agent templates, assimilating GitHub repos (`github_assimilator.py`), and managing agent lifecycle.
- **`core/swarm/`**: Subagents execution harness and `quantum_engine.py`.
- **`core/coordinators/` & `core/queues/`**: `agent_coordinator.py` and `task_queue.py`.
- **`core/workflows/` & `core/flows/`**: Workflow composition models (`product_launch_flow.py`, `research_write_validate.py`).

### Domain 4: Self-Healing, Resilience & Defensive Security
- **`core/error_distillation/`**: Automated error categorization, AST fingerprinting (`fingerprint.py`), root-cause classifier (`classifier.py`), and instant self-healing distillation (`distiller.py`).
- **`core/model_proxy/`**: `universal_model_proxy.py` and `self_healing_router.py` providing circuit-breaker fallbacks between Vertex AI, Anthropic, OpenAI, and Ollama.
- **`core/security/`**: Adversarial review gate (`adversarial_review.py`), probe library (`adversarial_probe_library.py`), cryptographic identity (`crypto_identity.py`), and audit chaining.
- **`core/patent_shield/`**: IP protection suite (`patent_client.py`, `patent_parser.py`, `similarity_engine.py`, `risk_evaluator.py`) to prevent patent contamination during SOTA assimilation.

### Domain 5: Domain Accelerators & Modular Bricks
- **`core/bricks/`**: Standardized modular subsystem specifications (Brick 01: Agentic Brain, Brick 02: SCONES Memory, Brick 03: Spatial Canvas, Brick 04: Shopify Engine, Brick 05: Video AI, Brick 06: Web API Shell).
- **`canvas_engine.py` & `core/canvas/`**: 5-atomic visual graph node engine and whiteboard synchronization.
- **`dna_assimilation.py` & `pattern_synthesizer.py`**: 5-Level SOTA knowledge assimilation pipeline, clean-room reverse engineering, and AST pattern extraction.
- **`core/video/`**: Automated kinetic video generation (`timeline_engine.py`, `kinetic_templates.py`, `remotion_renderer.py`).
- **`core/supervisor/`**: Shopify theme sync and bi-directional AST diffing supervisor.
- **`core/plugins/` & `core/adapters/`**: Internal plugin infrastructure and backend adapters (Redis, Postgres, LangGraph, InvokeAI, Stitch).

---

## 🚨 3. Critical Issues & Technical Debt Inventory

### 🔴 Severity 1: Critical Bloat & Test Suite Timeouts
1. **Untracked Duplicate Hermes Directories (1.36 GB / 77,248 Files)**:
   - `core/hermes_agent.backup.pre-0.21.0/` (480.55 MB, 26,552 files)
   - `core/hermes_agent_staging/` (396.97 MB, 24,142 files)
   - `core/hermes_versions/` (480.59 MB, 26,554 files)
   - *Impact*: `scripts/system/fast_compile_check.py` and `scripts/verify_all.sh` scan every single Python file. Compiling over 100,000 files causes `verify_all.sh` to exceed the 180s timeout.

2. **Agent Profile Runtime State Leakage (1.16 GB)**:
   - `core/orchestrator/agents/gerych_prime/` and `core/orchestrator/agents/herich_librarian/` are functioning as live runtime workdirs rather than static configuration cards.
   - They contain:
     - `state.db`: 365 MB + 258 MB = **623 MB** SQLite databases.
     - `checkpoints/`: **196 MB**.
     - `lsp/`: **168 MB** language server binaries and caches.
     - `bin/`: **62 MB** binaries.
     - `cache/`: **48 MB**.
     - `models_dev_cache.json`: **8.8 MB**.
   - *Impact*: Git status overhead, potential secret/token leakage in history, and confusion between agent specification vs runtime execution state.

### 🟠 Severity 2: Dead Code & Accidental Nesting
1. **Accidental Nested Directory `core/core`**:
   - Contains only `core/core/tests/scones_storage.json`. This was clearly created by an erroneous relative path command (`mkdir -p core/...` from inside `core`).
2. **Empty Orphan Directories**:
   - `core/workers/` (0 files)
   - `core/media/` (0 files)
3. **Broken Imports in `core/tests/`**:
   - `core/tests/test_accounting_langfuse.py`, `test_organic_synthesis.py`, and `test_phase1_core.py` directly import `from langfuse import Langfuse`. Since `langfuse` is not declared in `pyproject.toml`, executing pytest on `core/tests` immediately halts on `ModuleNotFoundError`.
   - Furthermore, `scripts/verify_all.sh` only discovers tests in `$HUB_ROOT/tests`, completely bypassing `core/tests/`.

### 🟡 Severity 3: Architectural Fragmentation & Duplicate Layers
1. **Fragmented Swarm Layer**:
   - Swarm logic is spread across **6 separate locations**:
     - `core/swarm_engine.py` (top-level)
     - `core/swarm_orchestrator.py` (top-level)
     - `core/workflow_orchestrator.py` (top-level)
     - `core/swarm/` (package with `quantum_engine.py` & `subagents.py`)
     - `core/orchestrator/` (package with `swarm_coordinator.py`)
     - `core/coordinators/` (package with `agent_coordinator.py`)
2. **Split Memory Abstraction**:
   - Cognitive memory is split between top-level modules (`core/scones_memory.py`, `core/scones_l3_memory.py`) and sub-packages (`core/memory/`, `core/stores/`).
3. **Canvas Engine Divergence**:
   - `core/canvas_engine.py` (369 LOC) vs `core/canvas/whiteboard_service.py` vs root `services/dnk_canvas_api`.
4. **Boundary Confusion between Root and Core**:
   - `adapters/` at root (generic frameworks: CrewAI, AutoGen, LlamaIndex) vs `core/adapters/` (internal infrastructure: Redis, Postgres, Stitch, Canvas).
   - `plugins/` at root (business plugins: Slack, Notion, Shopify Sync) vs `core/plugins/` (plugin runtime loader & manager).
   - `services/` at root (microservices) vs `core/services/` (internal core services: SecurityGate, RAG, TimelineKnowledge).

---

## 🛠️ 4. Strategic Refactoring & Optimization Roadmap

```
PHASE 1: Immediate Sanitization (P0)
 ├── 1. Add backup/staging directories to fast_compile_check.py IGNORE_DIRS
 ├── 2. Quarantine/Remove untracked Hermes duplicates (hermes_agent_staging, backup, versions) -> Free 1.36 GB
 ├── 3. Prune empty dirs (core/workers, core/media) and remove accidental core/core/
 └── 4. Add graceful import fallback in core/accounting_engine.py for langfuse

PHASE 2: Runtime State Isolation (P1)
 ├── 1. Relocate state.db, checkpoints/, lsp/, cache/ from core/orchestrator/agents/* to ~/.hermes/ or artifacts/
 ├── 2. Enforce clean agent profile cards (only config.yaml, SOUL.md, agent_card.yaml, memories/MEMORY.md)
 └── 3. Update .gitignore to strictly reject *.db, lsp/, bin/ in core/orchestrator/agents/

PHASE 3: Architectural Consolidation (P2)
 ├── 1. Unify Swarm Engine: Merge core/coordinators/ and core/swarm/ into core/orchestrator/
 ├── 2. Unify Memory: Consolidate core/scones_*.py and core/memory/ into a single core/memory/ package
 ├── 3. Clarify Framework vs App: Rename core/services -> core/internal_services to prevent clash with root services/
 └── 4. Migrate or bridge core/tests/ into root tests/core/ and ensure 100% Green in verify_all.sh
```

---

## 📋 5. Detailed Directory Audit Table

| Sub-path | Status | Size | File Count | Recommendation |
| :--- | :--- | :--- | :--- | :--- |
| `core/hermes_agent.backup.pre-0.21.0/` | **Zombie** | 480.55 MB | 26,552 | **REMOVE / ARCHIVE OUT OF REPO** |
| `core/hermes_agent_staging/` | **Zombie** | 396.97 MB | 24,142 | **REMOVE / ARCHIVE OUT OF REPO** |
| `core/hermes_versions/` | **Zombie** | 480.59 MB | 26,554 | **REMOVE / ARCHIVE OUT OF REPO** |
| `core/orchestrator/agents/{prime,librarian}` | **Polluted** | 1,164 MB | 23,210 | **PURGE RUNTIME CACHE / KEEP CARDS** |
| `core/core/` | **Buggy** | 0.01 MB | 1 | **REMOVE ACCIDENTAL DIRECTORY** |
| `core/workers/` | **Empty** | 0 MB | 0 | **REMOVE** |
| `core/media/` | **Empty** | 0 MB | 0 | **REMOVE** |
| `core/accounting_engine.py` | **Fragile** | 7.2 KB | 1 | **ADD TRY/EXCEPT FALLBACK FOR LANGFUSE** |
| `core/tests/` | **Orphaned** | 1.16 MB | 127 | **INTEGRATE INTO ROOT `tests/core/`** |
| `core/bricks/` | **Healthy** | 0.15 MB | 50 | **KEEP (Core Brick Architecture)** |
| `core/error_distillation/` | **Healthy** | 0.06 MB | 16 | **KEEP (Self-Healing Engine)** |
| `core/model_proxy/` | **Healthy** | 0.04 MB | 17 | **KEEP (Multi-LLM Fallback)** |
| `core/patent_shield/` | **Healthy** | 0.10 MB | 16 | **KEEP (IP Compliance Guard)** |
| `core/security/` | **Healthy** | 0.18 MB | 20 | **KEEP (Adversarial Gate Engine)** |
| `core/dna_assimilation.py` | **Healthy** | 10.3 KB | 1 | **KEEP (SOTA Ingestion Pipeline)** |
| `core/kernel.py` | **Healthy** | 7.0 KB | 1 | **KEEP (FastMCP Microkernel)** |
