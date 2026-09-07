---
name: "archify_assimilated"
description: "SOTA indices and recipes for Archify spatial diagram compiler: architecture, workflow, sequence, dataflow, lifecycle."
---

# 📐 Archify Spatial Diagram Engine Assimilation Index

Meta-index tracking self-contained interactive diagram generation, SVG animation, and spatial layouts for DNK OS.

## 📁 Core Specifications

1. **[Research & Evidence Trail](../../docs/reports/rd_assimilation/archify/RN-009_archify_diagram_engine_audit_and_assimilation.md)**
   - Technical analysis of `tt-a1i/archify` (Track 1 Permissive MIT, zero-runtime dependencies).

2. **[Spatial Architecture Patterns](../../docs/tech/specs/DNK-ARCH-009_archify_spatial_diagram_engine.md)**
   - Hexagonal diagram compiler topology, lanes/phases coordination, and self-contained HTML compilation.

3. **[Component State Contracts](../../docs/tech/specs/DNK-COMP-009_archify_diagram_contracts.md)**
   - Python Pydantic DTO interfaces (`DNKArchifyAdapter`, `ArchifyNode`, `ArchifyEdge`, `ArchifyDiagramPayload`).

4. **[Sandbox Execution Security](../../docs/tech/standards/DNK-SEC-009_archify_execution_sandbox.md)**
   - Subprocess containment, strict timeout boundaries, and offline zero-network verification.

## 📁 Structure

- `packages/archify/` — повнофункціональний автономний компілятор діаграм Node.js (CLI: `bin/archify.mjs`).
- `core/adapters/dnk_archify_adapter.py` — типізований адаптер Python / Pydantic v2 для генерації діаграм.
- `docs/diagrams/` — скомпільовані інтерактивні HTML-артефакти.

## 🧪 Quick Recipes

### Recipe A: Generating an Interactive Swarm Workflow
```python
from core.adapters.dnk_archify_adapter import DNKArchifyAdapter, ArchifyDiagramType

adapter = DNKArchifyAdapter()
preset = adapter.build_swarm_workflow_preset(output_path="docs/diagrams/swarm_workflow.html")
rendered_path = adapter.render_diagram(
    diagram_type=ArchifyDiagramType.WORKFLOW,
    payload=preset,
    output_html_path="docs/diagrams/swarm_workflow.html"
)
print(f"Interactive workflow diagram generated at: {rendered_path}")
```

### Recipe B: Compiling Custom Architecture or Dataflow
```python
from core.adapters.dnk_archify_adapter import DNKArchifyAdapter, ArchifyDiagramType

adapter = DNKArchifyAdapter()
payload = {
    "schema_version": 2,
    "diagram_type": "architecture",
    "meta": {
        "title": "DNK OS Core Topology",
        "visual_preset": "signal-flow",
        "quality_profile": "showcase",
    },
    "nodes": [
        {"id": "web", "type": "frontend", "label": "apps/web (Next.js)", "col": 0, "row": 0, "width": 160},
        {"id": "api", "type": "backend", "label": "apps/api (FastAPI)", "col": 1, "row": 0, "width": 160},
        {"id": "db", "type": "database", "label": "PostgreSQL & Qdrant", "col": 2, "row": 0, "width": 180},
    ],
    "edges": [
        {"id": "e1", "from": "web", "to": "api", "label": "REST / JSON"},
        {"id": "e2", "from": "api", "to": "db", "label": "SQLAlchemy / Vectors"},
    ]
}
adapter.render_diagram(ArchifyDiagramType.ARCHITECTURE, payload, "docs/diagrams/core_topology.html")
```
