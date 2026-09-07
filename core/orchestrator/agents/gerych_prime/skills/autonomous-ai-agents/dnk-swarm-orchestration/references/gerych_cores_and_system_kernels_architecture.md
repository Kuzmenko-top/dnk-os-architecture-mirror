# 🧠 Gerych Active Core & DNK OS System Kernels Architecture

## 1. Active Working Core of Gerych
- **AI Intelligence Model**: `gemini-3.8-flash`
  * Provider: Google Cloud Vertex AI (`vertex`), region `global`.
  * Context Window: Up to 1,000,000 tokens with `reasoning_effort: high`.
  * Auth Lifecycle: Auto-proactive OAuth2 ADC injection (`scripts/system/gerych.sh`) checking token freshness against `$HOME/.hermes/vertex_token.txt` and GCP project `project-930a8ed3-3e40-4f43-9d4`.
- **Fallbacks**: `gemini-3.5-flash`, `gemini-3.5-flash-lite`, external NIM (`nvidia`), and OpenRouter (`openrouter`).
- **Runtime Core**: `Hermes Agent` v2.1.0 (`core/hermes_agent`) under profile `gerych_prime` (`core/orchestrator/agents/gerych_prime`), secured by single-instance Process Guard locks.

## 2. DNK OS System Engines & Unified FastMCP Kernel
Centralized entrypoint: `FastMCPKernel` (`core/kernel.py`), coordinating 5 core V2 engines:
1. `MaksymAuthEngine` (`core/auth_engine.py`): Creator authorization, secret phrase validation, and session store.
2. `CanvasEngine` (`core/canvas_engine.py`): Spatial visual graph management, node registry, and state serialization.
3. `HermesRuntime` (`core/hermes_runtime.py`): Dry-run planning, execution sandboxing, safe rollback.
4. `SwarmOrchestrator` / `SwarmEngine` (`core/swarm_orchestrator.py`, `core/swarm_engine.py`): Multi-agent task planning and parallel execution.
5. `AccountingEngine` (`core/accounting_engine.py`): Token accounting, financial metrics, and technical telemetry.

Subordinate Specialized Engines:
- `TaskEngine` & `TaskGraphManager`: TaskDNA evolutionary DAG decomposition and dependency scheduling.
- `SconesMemory` & `SconesL3Memory`: Cognitive tiering (L1 fast memory, L2 domain rules, L3 vector store).
- `DNAAssimilationEngine`: 5-level repository assimilation (Track 1 Permissive vs Track 2 Clean-room).
- `ErrorDistillationEngine`: Failure pattern capture and instant self-healing distillation without iterative guessing.
- `PatternSynthesizer` & `VisualContextEngine`: Architectural template generation and UI/UX spatial synthesis.

## 3. Swarm Agent Profiles Topology (`core/orchestrator/agents/`)
- **Orchestration & Knowledge**:
  * `gerych_prime`: Active Swarm Manager & Chief Builder.
  * `herich_librarian`: SCONES Knowledge Base & Documentation Keeper.
- **Engineering Workers**:
  * `gerych_builder`: UI/Code generator.
  * `gerych_researcher`: AST/Repo-Map & open-source research.
  * `gerych_auditor`: Fail-closed security audits & Master Quality Gate.
  * `dnk_dev_fullstack`: FastAPI, Pydantic schemas, SQLAlchemy models.
  * `dnk_shopify`: Liquid AST, Shopify Functions, Checkout UI.
  * `dnk_video_ai_creator`: Remotion compositions, animations, audio-visual sync.
  * `dnk_scones_memory`: Vector memory storage and query handler.
  * `dnk_security_guard`: Secret hygiene, token leakage scanner, firewall.
- **Business Operations**:
  * `dnk_analytics`, `dnk_marketing_cmo`, `dnk_finance_cfo`, `dnk_erp_supply`.
