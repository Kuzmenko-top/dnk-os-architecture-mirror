# --- DNK-MRH-HEADER ---
# mrh_id: "docs/reports/rd_assimilation/agentswarms/RN-007_agentswarms_architecture_and_lakehouse_audit.md"
# purpose: "Comprehensive Research Digest & Technical Reverse-Engineering Audit of AgentSwarms (AgentSwarms-fyi/agentswarms)."
# canonical_source: true
# alters_files: []
# triggers_tasks: ["TASK-SWARM-BI-ASSIMILATION"]
# status: "Approved"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "Antigravity (Mentor) & Gerych Prime"
# --- END DNK-MRH-HEADER ---

# 🔬 RN-007: AgentSwarms Architecture, Multi-Agent Swarms & Lakehouse BI Audit

## 📋 1. Executive Summary & Repository Metadata
- **Source Repository**: [`AgentSwarms-fyi/agentswarms`](https://github.com/AgentSwarms-fyi/agentswarms)
- **Stars / Forks**: 229 ⭐ / 57 🍴
- **License**: **Elastic License 2.0 (ELv2)** — Source Available
- **DNK OS License Classification**: **Track 2: Clean-Room Pattern Adaptation (`R3_pattern_adaptation`)**
- **Core Value Proposition**: A unified platform uniting visual multi-agent swarms with an embedded lakehouse (DuckDB over zstd Parquet), an AI Analyst (NL2SQL reasoning engine with dynamic charting), and a visual ETL pipeline editor.

---

## 🏛️ 2. Architectural Decomposition of AgentSwarms

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                AGENTSWARMS PLATFORM ARCHITECTURE                                │
├─────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 1. VISUAL SWARM WORKFLOW ENGINE (XYFlow / React 19 / TanStack Start)                            │
│    - Node Types: AgentNode, RouterNode, ConditionNode, LoopNode, ApprovalNode, ToolNode         │
│    - Version Control: Draft vs. Published execution snapshots                                   │
│    - Execution Traces: Real-time event streaming with token spend calculation                   │
├─────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 2. AGENTIC BI & AI ANALYST (DuckDB / NL2SQL Reasoning Engine)                                   │
│    - Step-by-Step Analytical Planner (Breaks business questions into sequential steps)          │
│    - In-Memory DuckDB-Wasm & Node DuckDB Engine for columnar scans                              │
│    - Dynamic Visualizer: Auto-selects Line, Bar, Scatter, GeoMap, or Metric Tiles               │
│    - Branded PDF & Deck Generator: Exports analytical traces with step-level citations          │
├─────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 3. LAKEHOUSE & SEMANTIC GOVERNANCE LAYER                                                        │
│    - Storage: DuckDB over zstd Parquet in local/S3 buckets                                      │
│    - Semantic Layer: Shared metric definitions, column masks, row filters, and ontology graphs  │
│    - Data Lineage: Traces generated answers back to source tables & pipelines                   │
├─────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 4. VISUAL ETL PIPELINE ENGINE                                                                   │
│    - Drag-and-drop source-to-target reconciliation graph                                        │
│    - Python transpiler: Compiles visual graph to executable Python scripts                      │
│    - Sandboxed execution: Zero credential leakage into user script environments                 │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## ⚖️ 3. License Audit & Clean-Room Firewall (ELv2 Compliance)

| Dimension | Upstream (AgentSwarms) | DNK OS Clean-Room Policy |
| :--- | :--- | :--- |
| **License Type** | Elastic License 2.0 (ELv2) | Proprietary / Internal Dual Licensing |
| **Direct Code Copying** | ❌ FORBIDDEN (Protects commercial SaaS boundary) | Clean-Room Structural Transpilation into Python/FastAPI/Konva |
| **Architectural Patterns** | Permitted for study & integration | ✅ Extracted: Node DAG semantics, DuckDB Lakehouse, Semantic Metrics |
| **Persistence Integration** | Supabase Backend | SQLite / PostgreSQL + Redis + SCONES Vector DB in DNK OS |

---

## 🧬 4. Key Patterns Adopted into DNK OS MVP

### 4.1 Swarm DAG Node Model
We adapt AgentSwarms' 6 core node types into our `TaskDNA` & Gerych Swarm coordinator:
1. `AgentNode`: Autonomous execution unit (Gemini 3.7 / Claude / Vertex AI).
2. `RouterNode`: Semantic intent router delegating tasks to domain agents (`dnk_shopify`, `dnk_video_ai_creator`).
3. `ConditionNode`: Rule evaluation gate (e.g. WCAG AA score >= 4.5).
4. `LoopNode`: Iterative self-healing until tests/lints pass.
5. `ApprovalNode`: Human-in-the-loop gate for dangerous or commercial mutations.
6. `ToolNode`: Direct MCP / FastMCP function invocation.

### 4.2 In-Memory DuckDB Lakehouse for Shopify & Marketing Analytics
- Replaces heavy SQL databases for local reporting.
- Enables instant multi-table joins over Shopify orders, marketing metrics, and media rendering logs without external database overhead.

### 4.3 Semantic Ontology Layer
- Standardizes metrics across agents: `gross_revenue`, `roas`, `render_fps`, `wcag_contrast_ratio`.
