# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/specs/DNK-MEMORY-HUB-001_tencentdb_agent_memory_spec.md"
# purpose: "Technical Specification for Integrating TencentDB Agent Memory Hub (CodeGraph, LLM-Wiki, Layered Memory) into DNK OS Swarm."
# canonical_source: true
# alters_files: []
# triggers_tasks: ["DNK-MEMORY-HUB-001"]
# status: "Draft"
# version: "1.0.0"
# updated_at: "2026-08-26"
# author: "Antigravity (Mentor/Architect) & DNK Architecture Council"
# --- END DNK-MRH-HEADER ---

# 🧠 DNK-MEMORY-HUB-001: TencentDB Agent Memory Hub Integration

## 1. Executive Summary
DNK OS agents (Gerych Chief Orchestrator, dnk_koder, dnk-dev-01) require instant, shared, and pre-indexed codebase understanding to eliminate redundant searches (`grep`/`find` bottlenecks), reduce context compaction churn, and share verified technical knowledge across the swarm.
Integrating **TencentDB-Agent-Memory** provides a centralized, team-level memory hub exposing four primary assets:
1. **CodeGraph**: Pre-indexed AST symbol graph, caller/callee relationships, and impact analysis paths.
2. **LLM-Wiki**: Structured documentation link-graph (Karpathy LLM Knowledge methodology).
3. **Layered Chat Memory**: Distillation pipeline (L0 raw conversation ➔ L1 atomic facts ➔ L2 scenario context ➔ L3 persona).
4. **Skills Hub**: Verified, versioned executable operational skills with team-level access control.

---

## 2. Architectural Blueprint

```text
               ┌────────────────────────────────────────────────────────┐
               │           DNK OS Swarm (Host / CLI / Subagents)        │
               │  ⚡ Gerych (Librarian) │ 💻 dnk_koder │ 🎨 dnk-dev-01  │
               └───────────────────────────┬────────────────────────────┘
                                           │ (OpenAI-compatible /v3/tools or MCP)
                                           ▼
               ┌────────────────────────────────────────────────────────┐
               │         TencentDB Memory Proxy (Port 8126)             │
               │   - Context enrichment & Tool routing                  │
               │   - Dynamic CodeGraph & Wiki retrieval                 │
               └───────────────────────────┬────────────────────────────┘
                                           │
             ┌─────────────────────────────┼────────────────────────────┐
             ▼                             ▼                            ▼
┌───────────────────────────┐┌───────────────────────────┐┌───────────────────────────┐
│       Memory Core         ││     Memory Knowledge      ││       Memory Panel        │
│ (L0→L3 Distillation & ACL)││ (CodeGraph & LLM-Wiki AST)││   (Web Admin UI :8125)    │
└────────────┬──────────────┘└─────────────┬─────────────┘└───────────────────────────┘
             │                             │
             └──────────────────────┬──────┘
                                    │
                                    ▼
               ┌───────────────────────────────────────────┐
               │         DNK OS PostgreSQL + pgvector      │
               │             (Port 5432 / 5433)            │
               └───────────────────────────────────────────┘
```

---

## 3. Core Component Modules

### Module A: CodeGraph Asset Integration
- **Functionality**: Automatically parses `DNK_HUB` and `DNK_HUB` code trees using AST symbol extractors.
- **Agent Value**: Replaces 20–60 second brute-force greps with indexed queries:
  - `codegraph.find_symbol("enforce_workspace_authorization")` ➔ returns declaration file, line, docstring, and all callers in 5ms.
  - `codegraph.impact_analysis("apps/api/routers/taskdna.py")` ➔ returns all dependent frontend files and tests.

### Module B: LLM-Wiki Knowledge Graph
- **Functionality**: Converts all `docs/`, ADRs, and Tech Specs into structured, cross-linked markdown knowledge nodes.
- **Agent Value**: Subagents instantly load domain-specific save files without re-reading 50 markdown files from scratch.

### Module C: Layered Memory Engine (L0 ➔ L3)
- **Distillation Protocol**:
  - `L0`: Ephemeral turn logs.
  - `L1`: Concrete verified facts ("`dnk-220826` uses Vertex global/us-central1 endpoints with Gemini 3.7").
  - `L2`: Active task context ("Refactoring auth bootstrap for Visual OS-003").
  - `L3`: Swarm persona & role boundaries.

---

## 4. Deployment Strategy in Docker Compose

Deploy as a modular add-on service inside `DNK OS/docker-compose.memory.yml`:
```yaml
version: '3.8'

services:
  tencentdb-memory-core:
    image: ccr.ccs.tencentyun.com/tencentdb-agent-memory/memory-core:latest
    container_name: dnk-memory-core
    environment:
      - DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@dnk_hub-pgvector-1:5432/dnk_memory
      - OPENAI_API_BASE=https://aiplatform.googleapis.com/v1/projects/${GOOGLE_CLOUD_PROJECT}/locations/global/publishers/google
      - EMBEDDING_MODEL=gemini-embedding-001
    ports:
      - "8124:8124"
    depends_on:
      - dnk_hub-pgvector-1

  tencentdb-memory-knowledge:
    image: ccr.ccs.tencentyun.com/tencentdb-agent-memory/memory-knowledge:latest
    container_name: dnk-memory-knowledge
    volumes:
      - /Users/<username>/Kuzmenko/MY_LIFE_WORK/DNK_HUB:/workspace:ro
    ports:
      - "8127:8127"

  tencentdb-memory-proxy:
    image: ccr.ccs.tencentyun.com/tencentdb-agent-memory/memory-proxy:latest
    container_name: dnk-memory-proxy
    ports:
      - "8126:8126"

  tencentdb-memory-panel:
    image: ccr.ccs.tencentyun.com/tencentdb-agent-memory/memory-panel:latest
    container_name: dnk-memory-panel
    ports:
      - "8125:8125"
```

---

## 5. Security & Context Isolation Gates
1. **Zero-Secret Exposure**: No API keys logged or committed in memory graphs.
2. **Context Firewall**: Read-only mounts for source directories; mutations only through Git PR workflow.
3. **Multi-Region Quota Alignment**: Uses DNK OS Vertex OAuth2 tokens and regional round-robin routing.
