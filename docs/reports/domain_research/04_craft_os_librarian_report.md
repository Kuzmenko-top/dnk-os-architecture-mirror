# --- DNK-MRH-HEADER ---
# mrh_id: "docs/reports/domain_research/04_craft_os_librarian_report.md"
# purpose: "Canonical documentation and task tracking note"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-09"
# --- END DNK-MRH-HEADER ---

<!-- --- DNK-MRH-HEADER ---
mrh_id: "projects/04_Craft_OS/tech/research/LIBRARIAN_REPORT.md"
purpose: "Canonical file for LIBRARIAN_REPORT.md"
canonical_source: true
alters_files: []
triggers_tasks: []
status: "Active"
version: "1.0.0"
updated_at: "2026-07-25"
--- END DNK-MRH-HEADER --- -->

# 📚 Librarian Report: Craft OS / Reburn Assistant

**Agent**: Gerych (Librarian & Orchestrator)
**Status**: Research Complete (Phase 1)

## 🔍 Task Breakdown

The objective is to build a complex agentic system for craftsmen (smokers). 
Key components identified:

1. **Business Dashboard (TMA)**: Frontend for accounting, orders, and finance.
2. **Technical Knowledge Base (RAG)**: Processing scientific books, research, and technical conditions.
3. **Domain Experts**: Agents specialized in smoking technology and business management.

## 🛠 Selected OSS Solutions (Library Matches)

### 1. UI: [SOCKETSOMEONE/NEXTJS-TELEGRAM-MINI-APP-TEMPLATE](https://github.com/SocketSomeone/nextjs-telegram-mini-app-template)

- **Fit**: 7.0/10
- **Rationale**: Clean Next.js structure optimized for TMA. Supports Telegram WebApp SDK out of the box.
- **Reverse Engineering Target**: Layout and SDK initialization.
- **Portability**: High. Can be placed in `external/tma/`.

### 2. Knowledge: [arulkumarann/legalRAG](https://github.com/arulkumarann/legalRAG)

- **Fit**: 9.3/10
- **Rationale**: Highly efficient RAG pipeline for complex legal (and by extension, scientific) documents. Uses FastAPI.
- **Reverse Engineering Target**: Ingestion logic and vector search optimization.
- **Adaptation**: Replace legal prompts with "Smoking Expert" prompts.

### 3. Orchestration: [ULTRAWORKERS/CLAW-CODE](https://github.com/ultraworkers/claw-code)

- **Fit**: 10.0/10
- **Rationale**: Our primary engine. Use for the core agentic loop and MCP integrations.
- **Status**: Already integrated into DNK_HUB core.

### 4. Monitoring: [AgentOps-AI/agentops](https://github.com/AgentOps-AI/agentops)

- **Fit**: 3.0 (Experimental)
- **Rationale**: Need to monitor agent performance and token costs for commercial viability.

## 🏗 Proposed Implementation Architecture

1. **Storage Hygiene**:
   - `external/` will contain submodules or cloned copies of the above repos.
   - `core/` will contain `recipes.json`, `business_logic.py`, and `tma_theme.css`.

2. **Data Pipeline**:
   - **Gerych** triggers the RAG ingestion of the "Smoking Library" stored in `data/library/`.
   - Resulting vectors are stored in a local project-specific collection in Qdrant.

3. **Delegation Flow**:
   - User asks TMA: "How do I smoke salmon at 60°C?"
   - **Gerych** identifies the project as `05-craft-os`.
   - **Gerych** delegates to `SmokingExpert` agent.
   - `SmokingExpert` queries the project-specific RAG.
   - Result is formatted for TMA and returned.