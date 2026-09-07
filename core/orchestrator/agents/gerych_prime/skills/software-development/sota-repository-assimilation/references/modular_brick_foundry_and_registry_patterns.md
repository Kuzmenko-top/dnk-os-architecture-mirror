# --- DNK-MRH-HEADER ---
# mrh_id: "skills/software-development/sota-repository-assimilation/references/modular_brick_foundry_and_registry_patterns.md"
# purpose: "Architectural reference for SOTA Distribute-as-Code Modular Brick Registry and Blueprint DSL patterns."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 🧱 SOTA Modular Brick Foundry & Distribute-as-Code Patterns

## 1. Core Principles Assimilated from SOTA

### A. Shadcn Registry Pattern (Distribute-as-Code)
- Components/Bricks are not packaged as monolithic black-box npm/pip libraries.
- Instead, they are distributed as raw, type-safe source files accompanied by a declarative manifest (`brick.manifest.yaml`).
- Features:
  - Atomic file maps (`source_paths` to `target_paths`).
  - Strict Pydantic contract definitions (`schemas.py`).
  - Selective dependency injection avoiding monorepo package bloat.

### B. Dify.ai Application DSL (`app.blueprint.yaml`)
- A standalone multi-agent application is defined declaratively rather than imperatively through CLI parameters.
- Blueprints encapsulate:
  1. Selected Brick identifiers.
  2. Brick-specific configurations and feature toggles.
  3. Canvas visual graph presets and initial UI layouts.

### C. FastMCP & Model Context Protocol (Universal Brick Interop)
- Each brick provides a standardized entrypoint for FastMCP (`entrypoints.mcp_server`).
- Enables any swarm agent or external orchestrator to invoke brick actions directly via standard JSON-RPC tools without ad-hoc wrapper glue.

### D. Topological DAG Dependency Resolution
- When a brick is requested, its recursive dependencies (`dependencies.bricks`) are automatically resolved in topological order via DFS.
- Prevents missing runtime modules in exported Tier-2 applications.
