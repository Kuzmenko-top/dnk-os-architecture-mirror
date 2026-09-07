# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/specs/DNK-ARCH-009_archify_spatial_diagram_engine.md"
# purpose: "Architecture Specification for Archify Spatial Diagram Engine Assimilation in DNK OS."
# canonical_source: true
# alters_files: []
# triggers_tasks: ["TASK-ARCHIFY-ASSIMILATION-001"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-04"
# author: "Gerych (Hermes Prime) & Maxim Kuzmenko"
# --- END DNK-MRH-HEADER ---

# DNK-ARCH-009: Архітектурна специфікація просторового рушія діаграм Archify

## 1. Контекст та архітектурне призначення
Для візуалізації складних багатоагентних взаємодій (14 агентів Swarm), потоків даних між мікросервісами, топологій баз даних (Postgres, Qdrant) та життєвих циклів тасок DNK OS потрібен автономний, надійний і неперевантажений рушій генерації діаграм.
Асимільований рушій `Archify` вирішує це завдання шляхом трансляції типізованого JSON Intermediate Representation (IR) у самодостатній автономний HTML/SVG артефакт.

## 2. Гексагональна топологія системи (Hexagonal Architecture)

```
[DNK Swarm Agents / APIs] 
            │
            ▼
    [Archify Port / DTOs]  (Pydantic Models: Node, Edge, Lane, Phase)
            │
            ▼
  [DNKArchifyAdapter]     (Python Hexagonal Adapter: core/adapters/dnk_archify_adapter.py)
            │
            ▼ (Subprocess / CLI JSON Bridge)
    [packages/archify]    (Node.js Standalone Compiler: bin/archify.mjs)
            │
            ▼
  [Self-Contained HTML]   (docs/diagrams/*.html - Interactive SVG with Pan/Zoom/Views)
```

## 3. Топологія діаграмних доменів
1. **Architecture Engine**: Побудова карт фізичної та логічної архітектури DNK OS (сервіси, бази, фронтенд, API шлюзи).
2. **Workflow Engine**: Візуалізація паралельного виконання агентів Swarm (`MASE`, `A2A Mesh`, `Evidence Gates`).
3. **Sequence Engine**: Візуалізація протоколів взаємодії між агентами через черги або gRPC/REST.
4. **Dataflow Engine**: Карти переміщення даних між SCONES, Qdrant, PostgreSQL та кешем.
5. **Lifecycle Engine**: Моделювання станів життєвого циклу завдань (Pending -> Triage -> Execution -> Audit -> Certified).

## 4. Нефункціональні вимоги та гарантії
- **Zero-Network Dependency**: Жоден згенерований файл не робить запитів до зовнішніх CDN або API.
- **Deterministic Rendering**: Однаковий JSON завжди дає ідентичний піксельний SVG/HTML.
- **High Performance**: Рендеринг складної діаграми займає менше 100 мс.
