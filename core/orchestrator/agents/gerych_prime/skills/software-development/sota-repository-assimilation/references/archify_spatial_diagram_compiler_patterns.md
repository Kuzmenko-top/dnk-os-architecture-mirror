# --- DNK-MRH-HEADER ---
# mrh_id: "core/orchestrator/agents/gerych_prime/skills/software-development/sota-repository-assimilation/references/archify_spatial_diagram_compiler_patterns.md"
# purpose: "Patterns, layout constraints, and hexagonal adaptation for Archify spatial diagram compiler in DNK OS."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-04"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

# 📐 Archify Spatial Diagram Compiler & Hexagonal Assimilation Patterns

## 🎯 Architectural Context
When assimilating spatial/visual compilers like `tt-a1i/archify` that transform declarative Typed JSON IR into self-contained HTML/SVG artifacts:
- **Zero Runtime Dependencies**: The compiler output must remain fully standalone (single HTML with inlined CSS, SVG symbols, and vanilla JS pan/zoom/view controllers), requiring zero external CDNs or network fetches.
- **Hexagonal Isolation**: Always wrap the underlying compiler CLI (`bin/archify.mjs`) in a typed Python adapter (`core/adapters/dnk_archify_adapter.py`) utilizing Pydantic v2 schemas and subprocess execution sandboxing.

---

## ⚠️ Pitfall: Geometric Typography & Layout Validation (`diagnostics.mjs`)

Spatial diagram compilers enforce strict pixel layout constraints to prevent visual clipping:
```
Error: Workflow layout validation failed:
- Label "Task DNA Triage" (~102px) is wider than node "triage" (92px) — shorten the label or increase node.width.
- Label "dnk_dev_fullstack" (~116px) is wider than node "dev_fullstack" (92px) — shorten the label or increase node.width.
- Label "Master Quality Gate" (~129px) is wider than node "verify_gate" (92px) — shorten the label or increase node.width.
```

### Mitigation Pattern:
1. **Dynamic Node Width Allocation**: Calculate approximate label width in the Python adapter (`max(default_width, len(label) * char_px_multiplier + padding)`) or enforce minimum safe default node widths (e.g. `width: 140` to `160px` for multi-word or snake_case agent IDs).
2. **Pre-Render Schema Diagnostics**: Validate node bounds prior to invoking CLI rendering to prevent unhandled compiler exits.

---

## 🛠️ Multi-Domain Mapping for DNK Swarm

| Diagram Domain | Primary DNK OS Application | Key Entities |
| :--- | :--- | :--- |
| **`workflow`** | 14-Agent Swarm execution phases and handoffs | Lanes (`agent_id`), Phases (`triage`, `execution`, `audit`), Status routes |
| **`architecture`** | System topology and microservices mapping | Nodes (`frontend`, `backend`, `database`, `event_bus`), Layer boundaries |
| **`sequence`** | Agent-to-Agent (A2A) Mesh message exchanges | Lifelines, synchronous/asynchronous calls, retry/alt blocks |
| **`dataflow`** | Video, Liquid AST, or Vector ingestion pipelines | Sources, Transformations, Sinks, Tenant Scopes |
| **`lifecycle`** | Task DNA & Artifact states (Draft -> Verified -> Promoted) | States, Transitions, Guard Conditions |
