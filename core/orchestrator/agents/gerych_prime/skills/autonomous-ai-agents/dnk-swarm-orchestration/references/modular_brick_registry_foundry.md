# --- DNK-MRH-HEADER ---
# mrh_id: "skills/autonomous-ai-agents/dnk-swarm-orchestration/references/modular_brick_registry_foundry.md"
# purpose: "Reference architecture for DNK Modular Brick Registry & Standalone App Assembly Engine."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym & Gerych (Hermes Prime)"
# --- END DNK-MRH-HEADER ---

# 🧱 DNK Modular Brick Registry & AI Product Foundry

## 1. 6 Universal Core Bricks Matrix
Each brick lives under `core/bricks/<brick_id>/` with its own `brick.manifest.yaml` and `contracts/schemas.py`:

| Brick ID | Name | Category | Internal Dependencies | Core Capabilities |
| :--- | :--- | :--- | :--- | :--- |
| `brick_01_agentic_brain` | Agentic Brain & Swarm Core | `agentic_core` | *(none)* | TaskDNA, Subagent Dispatch, Tool Calling, Circuit Breakers |
| `brick_02_scones_memory` | SCONES Memory & Knowledge Hub | `knowledge_memory` | *(none)* | Cognitive vector memory, Task Forest, Error Distillation |
| `brick_03_spatial_canvas` | Spatial Canvas V3 Engine | `spatial_ui` | `brick_02_scones_memory` | Realtime CRDT, Node Graph AST, WS Streaming |
| `brick_04_shopify_engine` | Shopify 3.0 Engine & Liquid AST | `ecommerce_engine` | `brick_02_scones_memory` | Liquid AST parsing, Section schemas, Vite theme packaging |
| `brick_05_video_ai` | Video AI UGC Pipeline | `video_generation` | `brick_02_scones_memory` | Remotion renderer, UGC reel templates, FFmpeg composition |
| `brick_06_web_api_shell` | Web UI & API Gateway Shell | `gateway_shell` | `brick_01_agentic_brain`, `brick_02_scones_memory` | Next.js 14 Cockpit, Dynamic FastAPI router, WS Bridge |

---

## 2. Dynamic DAG Dependency Resolution
`DNKBrickRegistry` (`core/bricks/registry.py`) dynamically computes the topological dependency order (dependencies first) using DFS with cycle detection:

```python
from core.bricks.registry import DNKBrickRegistry

registry = DNKBrickRegistry()
resolved = registry.resolve_dependencies(["brick_04_shopify_engine", "brick_05_video_ai"])
# Returns: ['brick_02_scones_memory', 'brick_04_shopify_engine', 'brick_05_video_ai']
```

---

## 3. Autonomous Tier-2 App Export Command
To export any combination of bricks into an isolated standalone client application:

```bash
python3 scripts/export_standalone_app.py \
  --app-id "ai_shopify_growth_studio" \
  --bricks brick_04_shopify_engine brick_05_video_ai brick_06_web_api_shell \
  --target-dir "../dist/ai_shopify_growth_studio"
```

The script:
1. Resolves transitive DAG dependencies.
2. Copies target brick paths while excluding cache/transient files (`node_modules`, `.venv`, `.next`, `__pycache__`, `*.db`).
3. Emits deployment manifests (`Dockerfile`, `docker-compose.yml`, `.env.example`).
4. Initializes clean Git repo on branch `main`.

---

## 4. Verification Suite
Always verify registry integrity via:
```bash
.venv/bin/pytest tests/bricks/test_brick_registry.py -v
```
Ensures 100% valid manifest schemas, cycle-free DAGs, and contract imports.
