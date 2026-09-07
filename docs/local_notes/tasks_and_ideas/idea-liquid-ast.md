# --- DNK-MRH-HEADER ---
# mrh_id: "docs/notes/tasks_and_ideas/idea-liquid-ast.md"
# purpose: "Task & Idea Node: Real-Time Shopify Liquid AST Live Transpiler"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

---
node_id: idea-liquid-ast
title: "Real-Time Shopify Liquid AST Live Transpiler"
node_type: idea
stage: ideation
status: draft
progress: 35.0
priority: critical
assigned_agent: dnk_shopify
target_module: services/dnk_shopify
is_blocked: false
tags: [shopify, ecommerce, liquid, ast, idea]
---

# Real-Time Shopify Liquid AST Live Transpiler

**Type**: `IDEA` | **Stage**: `ideation` | **Status**: `draft` | **Progress**: `35.0%`

### Description
Bidirectional sync between visual spatial canvas blocks and Shopify OS 2.0 Liquid schema.

### Target Module & Files
**Module**: `services/dnk_shopify`
- `services/dnk_shopify/liquid_ast.py`

### Acceptance Criteria (Definition of Done)
- [ ] Parse Liquid {% schema %} without regex hacks
- [ ] AST mutation round-trip fidelity
- [ ] Preserve comments and liquid tags

### Upstream Dependencies (Prerequisites)
_No upstream dependencies_

### Downstream Dependents
- **spawns_from** to [[epic-canvas-v2]] (Canvas v2 architecture spawned from Liquid AST requirements)

> Node Position on Canvas: `x=60.0, y=340.0`
> Backlink to Master Index: [[000_DNK_TASK_AND_IDEAS_INDEX]]
