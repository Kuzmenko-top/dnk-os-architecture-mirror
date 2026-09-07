---
name: "agno_assimilated"
description: "Assimilated patterns, workflows, and multi-agent execution primitives from agno-agi/agno"
version: "1.0.0"
category: "research"
assimilated_at: "2026-09-02"
---

# 🦅 Agno Framework Assimilation Index

Meta-index for Agno architecture, component contracts, security standards, and Infinite Canvas integration recipes.

## 📁 Core Specifications

1. **[Research & Evidence Trail](../../docs/reports/rd_assimilation/agno/RN-043_agno_architecture_and_infinite_canvas_audit.md)**
   - Complete architectural audit, Star/License metrics, subsystem mapping, and reverse-engineering findings.

2. **[Architecture Specification](../../docs/tech/specs/DNK-ARCH-043_agno_infinite_canvas_patterns.md)**
   - Infinite Canvas spatial execution topology, DAG node graph compilation, asynchronous checkpointing, and HITL lifecycle.

3. **[Component Interfaces & Contracts](../../docs/tech/specs/DNK-COMP-043_agno_canvas_contracts.md)**
   - Pydantic DTOs for `CanvasNodeConfig`, `CanvasEdge`, `HITLCheckpoint`, and the abstract `IAgnoCanvasAdapter` interface.

4. **[Security & Egress Standards](../../docs/tech/standards/DNK-SEC-043_agno_execution_sandbox.md)**
   - Tool execution sandboxing, dangerous action classification, HITL gates, and credential sanitization.

---

## 🧪 Quick Recipes (How to Use This Skill)

### Recipe A: Executing a Multi-Agent Canvas Graph
```python
from adapters.dnk_agno_canvas_adapter import DnkAgnoCanvasAdapter
from pydantic import BaseModel

adapter = DnkAgnoCanvasAdapter()

graph = {
    "graph_id": "graph-001",
    "workspace_id": "ws-alpha-001",
    "nodes": [
        {
            "node_id": "agent-research",
            "node_type": "agent",
            "title": "Research Agent",
            "agent_name": "researcher",
            "instructions": "Extract key technical points.",
        },
        {
            "node_id": "team-review",
            "node_type": "team",
            "title": "Review Team",
            "team_mode": "route",
            "member_agents": ["builder", "auditor"],
        }
    ],
    "edges": [
        {"edge_id": "e1", "source_node_id": "agent-research", "target_node_id": "team-review"}
    ],
    "initial_inputs": {"prompt": "Analyze Shopify Liquid AST performance."}
}

results = adapter.execute_graph_stepwise(graph)
```

### Recipe B: Handling Asynchronous HITL Approvals
```python
# When a node attempts a dangerous action or exceeds quota:
checkpoint = adapter.create_hitl_checkpoint(
    node_id="node-deploy-01",
    reason="Deploying Liquid theme to live production store",
    pending_action="deploy_shopify_theme",
    parameters={"theme_id": "prod_12345"}
)

# ... User reviews on Infinite Canvas and clicks 'Approve' ...
resolution = {
    "checkpoint_id": checkpoint["checkpoint_id"],
    "decision": "approve",
    "user_comment": "Verified by Maxim"
}

resume_result = adapter.resume_hitl_checkpoint(resolution)
```
