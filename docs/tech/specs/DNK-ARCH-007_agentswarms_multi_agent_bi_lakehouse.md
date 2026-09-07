# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/specs/DNK-ARCH-007_agentswarms_multi_agent_bi_lakehouse.md"
# purpose: "Technical Specification & Architecture Blueprint for DNK Swarm Workflow DAG, Agentic BI & DuckDB Lakehouse (AgentSwarms SOTA Assimilation)."
# canonical_source: true
# alters_files: ["core/adapters/dnk_agentswarms_adapter.py"]
# triggers_tasks: ["TASK-SWARM-BI-001"]
# status: "Approved"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "Antigravity (Mentor) & Gerych Prime"
# --- END DNK-MRH-HEADER ---

# 🏗️ DNK-ARCH-007: DNK Multi-Agent Swarm DAG & Lakehouse BI Specification

## 📌 1. Scope & System Goals
This specification formalizes the assimilation of **AgentSwarms** into DNK OS, establishing:
1. **6-Node Visual Swarm Graph DAG**: Clean-room implementation of Agent, Router, Condition, Loop, Human Approval, and Tool Call nodes.
2. **Embedded DuckDB Lakehouse Engine**: Columnar data processing for commerce, video rendering telemetry, and agent spend metrics.
3. **AI Analyst Reasoning & NL2SQL Pipeline**: Multi-step query planner with automatic schema exploration and metric ontology governance.
4. **FastAPI Adapter & WebSocket Streamer**: Integration into `apps/api` and Gerych Swarm CLI.

---

## 🏛️ 2. Component Topology

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       DNK SWARM WORKFLOW & BI ENGINE                        │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. VISUAL SWARM GRAPH DAG (Zustand + XYFlow / Konva Overlay)                │
│    - Node Registry: AgentNode, RouterNode, ConditionNode, LoopNode,         │
│      ApprovalNode, ToolCallNode                                             │
│    - Execution Engine: Asynchronous Topological Sort + State Keyframes       │
├─────────────────────────────────────────────────────────────────────────────┤
│ 2. EMBEDDED DUCKDB LAKEHOUSE & SEMANTIC LAYER                               │
│    - DuckDB In-Memory & Parquet Storage (`data/lakehouse/*.parquet`)         │
│    - Semantic Catalog: Metrics, Dimensions, Filters, Column Masks           │
├─────────────────────────────────────────────────────────────────────────────┤
│ 3. AI ANALYST & NL2SQL REASONING PIPELINE                                   │
│    - NL2SQL Translator with Schema Injection & Security Bounds              │
│    - Step-by-Step Reasoner & Dynamic Chart Generator (Line, Bar, Metric)    │
│    - PDF / Markdown Branded Audit Exporter                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│ 4. FASTAPI & FAST-MCP BRIDGE (`core/adapters/dnk_agentswarms_adapter.py`)   │
│    - Endpoints for Swarm DAG Execution, Lakehouse Queries, and NL2SQL       │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📐 3. Data Contracts & Pydantic DTOs

```python
from enum import Enum
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field

class SwarmNodeType(str, Enum):
    AGENT = "agent"
    ROUTER = "router"
    CONDITION = "condition"
    LOOP = "loop"
    APPROVAL = "approval"
    TOOL = "tool"

class SwarmWorkflowNode(BaseModel):
    id: str
    node_type: SwarmNodeType
    name: str
    config: Dict[str, Any] = Field(default_factory=dict)
    position: Dict[str, float] = Field(default_factory=lambda: {"x": 0.0, "y": 0.0})

class SwarmWorkflowEdge(BaseModel):
    id: str
    source_node_id: str
    target_node_id: str
    condition_expression: Optional[str] = None
    label: Optional[str] = None

class SwarmWorkflowDAG(BaseModel):
    workflow_id: str
    title: str
    nodes: List[SwarmWorkflowNode] = Field(default_factory=list)
    edges: List[SwarmWorkflowEdge] = Field(default_factory=list)
    status: str = "draft"
    version: int = 1

class SemanticMetricSpec(BaseModel):
    name: str
    description: str
    sql_formula: str
    dimensions: List[str] = Field(default_factory=list)
    unit: str = "number"

class LakehouseQueryRequest(BaseModel):
    sql_query: str
    parameters: Dict[str, Any] = Field(default_factory=dict)

class LakehouseQueryResponse(BaseModel):
    columns: List[str]
    rows: List[List[Any]]
    execution_time_ms: float
    row_count: int
```
