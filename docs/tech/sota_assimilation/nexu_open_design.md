# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/sota_assimilation/nexu_open_design.md"
# purpose: "SOTA Research Digest & Assimilation Strategy for nexu-io/open-design integration with Gerych Core"
# canonical_source: true
# alters_files: ["projects/open_design_lab/*", "adapters/dnk_open_design_adapter.py"]
# triggers_tasks: ["DNK-OPEN-DESIGN-001"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-01"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 🎨 SOTA Assimilation Digest: Open Design (nexu-io/open-design) ⇄ Gerych

## 1. Overview & License Audit
- **Source Repository**: `https://github.com/nexu-io/open-design`
- **Track Classification**: **Track 1 (Permissive / Clean-Architecture Integration)**
- **Purpose**: Open-source visual design canvas and generative UI editor with structured AST nodes (Figma-compatible semantics).

## 2. Decoupled Integration Topology
Rather than embedding a bloated copy of Hermes inside the frontend canvas runtime, Gerych operates as the centralized intelligence and execution server via **JSON-RPC over WebSocket / SSE / HTTP Gateway**:

```
 ┌─────────────────────────────────────────────────────────────┐
 │               Open Design Frontend (Canvas UI)              │
 │  - Interactive Fabric/Konva/DOM Nodes                       │
 │  - Vector Paths & Style Properties                          │
 │  - useGerychBridge Hook / Protocol Adapter                  │
 └──────────────────────────────┬──────────────────────────────┘
                                │ JSON-RPC / WebSocket
 ┌──────────────────────────────▼──────────────────────────────┐
 │         DNK Open Design Adapter (Hexagonal Bridge)          │
 │  - Canvas AST Node Serializer / Deserializer                │
 │  - TaskDNA Intent Parser & Element Mutation Streamer        │
 │  - SCONES Memory Cache (Design Systems & Components)        │
 └──────────────────────────────┬──────────────────────────────┘
                                │ Agent Invocations
 ┌──────────────────────────────▼──────────────────────────────┐
 │                 Gerych Core (Hermes Prime)                  │
 │  - Swarm Orchestration (dnk_builder, dnk_shopify)           │
 │  - Multi-Model LLM Execution (Vertex AI / Claude / Gemini)  │
 └─────────────────────────────────────────────────────────────┘
```

## 3. Core Protocol Data Contracts
- `CanvasNode`: Abstract node representation (`id`, `type`, `bounds`, `styles`, `children`, `metadata`).
- `CanvasMutation`: Atomic operations (`create_node`, `update_style`, `transform`, `delete_node`, `batch_mutations`).
- `DesignIntent`: High-level natural language instructions from user translated to TaskDNA DAG.
- `GerychDesignSession`: Session context holding active selection, history stack, and design tokens.
