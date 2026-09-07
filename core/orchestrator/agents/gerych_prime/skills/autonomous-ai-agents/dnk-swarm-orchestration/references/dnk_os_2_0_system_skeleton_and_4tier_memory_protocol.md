# DNK OS 2.0 System Skeleton, 4-Tier Memory & SOTA Technology Matrix Protocol (SKELETON-4TIER-001)

## 🎯 Architectural Intent
This protocol codifies the canonical DNK OS 2.0 system topology designed by Founder Maksym and ratified by Chief Architect Gerych Prime. It establishes the clean separation between Platform Kernels, Domain Services, Marketing Studio, and Sales Engine, while formalizing the 4-tier memory architecture and SOTA open-source synthesis stack.

---

## 🏛️ 1. Canonical System Skeleton Topology

```
                                  [ DNK OS ]
                                       │
        ┌───────────────────┬──────────┴──────────┬───────────────────┐
        ▼                   ▼                     ▼                   ▼
    [ 1. ЯДРО ]       [ 2. СЕРВІСИ ]       [ 3. МАРКЕТИНГ ]     [ 4. ПРОДАЖІ ]
        │
   ┌────┴───────────────────────────┬─────────────────────┬─────────────────────┐
   ▼                                ▼                     ▼                     ▼
[ Герич - Головний Агент ]     [ Фронт-Енд ]         [ Бек-Енд ]           [ Пам'ять ]
 • Розробка Ядра                • Next.js 14/15       • FastAPI Gateway     • Довготривала
 • Розробка Сервісів            • Open Canvas         • WebSocket Bus       • Сервісна
 • Створення Агентів            • Archify Spatial     • OCC Resolver        • Проєктна
 • Навчання бібліотеки          • 5-Scale LOD         • Alembic DB          • Сесійна
                                                                                │
                                                                           [ Агенти ]
                                                                            • Навички
                                                                            • Зони відповідальності
```

---

## 👑 2. Gerych Prime - Chief Agent 4-Pillar Responsibilities

1. **System Core Engineering (`Робота з розробки Ядра системи`)**:
   - Maintains the physical plant of the monorepo.
   - Enforces Subtraction Rebuild (13 Laws) and prevents code bloat using the BloatBot/BuildBot dyad patterns.
2. **Services Development (`Розробка Сервісів`)**:
   - Generates standardized microservices adhering to `DNK-SRV-STD-001` (`service_manifest.yaml`, API routes, Canvas node components).
3. **Agent Factory (`Створення Агентів`)**:
   - Scaffolds and refines domain workers using the 4-part Chair Anatomy: `Skill.md` (instructions) + `Source.md` (state) + `Parts/` (tools) + `Archive/` (logs).
4. **Knowledge Harvesting (`Навчання та наповнення бібліотеки`)**:
   - Runs the Two-Track SOTA Repository Assimilation Pipeline (`core/dna_assimilation.py`).
   - Translates GitHub breakthroughs into verified ADRs, Obsidian notes (`docs/notes/`), and skills.

---

## 🧠 3. 4-Tier Memory Topology

| Memory Tier | Primary Storage Engine | SOTA Reference Repo | Invariants & Guarantees |
|-------------|------------------------|---------------------|--------------------------|
| **1. Довготривала (Long-Term)** | SQLite + FTS5 Bitemporal Store + SCONES L3 | `jdpolasky/ai-chief-of-staff-engine` | Bi-temporal tracking (`valid_time` vs `tx_time`). Immutable historical audit trail. Zero hallucinated overwrites. |
| **2. Сервісна (Service Memory)** | `core/registry/registry.json` + Pydantic | DNK Capability Registry | Declarative JSON Schemas, lazy tool activation ("Born Lazy"), rate limits. |
| **3. Проєктна (Project Memory)** | `products/<slug>/` + Tenant Vector Store | DNK Tenant Isolation Pattern | Brand assets, `PRODUCT_DNA.md`, client pricing matrices, isolated context. |
| **4. Сесійна (Session Memory)** | SQLite FTS5 Session DB + LangGraph | `langchain-ai/langgraph` | Ephemeral chat messages, TaskDNA DAG state checkpoints, time-travel rollback. |

---

## 🛠️ 4. SOTA Open-Source Synthesis Matrix

| Component | Technology / Repository | License | Purpose in DNK OS 2.0 |
|-----------|-------------------------|---------|------------------------|
| **Agent Runtime** | `nousresearch/hermes-agent` | MIT | High-velocity agent harness, tool calling, local loop. |
| **Operating Laws** | `jdpolasky/chief-of-staff-2` | MIT | 13 System Laws, Chair architecture, Subtraction principle. |
| **Canvas Studio** | `xyflow/xyflow` (React Flow) | MIT | Infinite spatial canvas, node/edge graph engine. |
| **Artifact Editing** | `langchain-ai/open-canvas` | MIT | Real-time artifact generation, branching, visual co-piloting. |
| **Diagram Compiler** | `archify/archify` | MIT | Spatial diagrams, sequence flows, dynamic architecture mapping. |
| **Backend Gateway** | `tiangolo/fastapi` + Starlette | MIT | Low-latency async REST, WebSocket bus, telemetry. |
| **Video AI Studio** | `remotion-dev/remotion` | Custom | Programmatic React-based video generation (Reels, TikTok). |
| **Interactive Avatars** | `GVCLab/PersonaLive` | Apache 2.0 | Real-time audio/motion avatar synthesis. |
| **E-Commerce Engine** | `shopify/theme-tools` + Liquid AST | MIT | Storefront AST parsing, section generation, checkout flows. |

---

## 🔒 5. Verification & Quality Gates
- **Zero-Waste Monorepo Root**: Exactly 7 first-class directories (`apps/`, `core/`, `services/`, `products/`, `docs/`, `infra/`, `scripts/`).
- **Pre-Commit Gate**: `bash scripts/verify_all.sh` must remain 100% green before any architectural mutation is accepted.
