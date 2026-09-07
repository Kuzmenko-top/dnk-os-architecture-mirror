# DNK OS — Architecture Status & Engineering Baseline

**Version:** 0.1.0-mirror  
**Date:** 2026-09-07  
**Status:** Read-Only Architectural Snapshot  
**Reference Document:** `docs/audit/DNK_OS_CAPABILITY_BASELINE_v0.1.md`

---

## 1. System Topology Overview

DNK OS operates on a unified, high-velocity orchestration model structured across four primary tiers:

```
[ Visual Web Studio & Canvas ] (Next.js 14 / React Flow / Tailwind)
             │
             ▼ REST / WebSocket / SSE
[ API Gateway & Ingestion Layer ] (FastAPI / Pydantic v2 / OAuth2 / RateLimiters)
             │
             ▼
[ Core Orchestrator & Swarm Hierarchy ] (Gerych Prime + 14 Domain Swarm Agents)
    ├── TaskDNA Evolutionary DAG
    ├── SCONES L1-L3 Cognitive Episodic & Semantic Memory
    ├── OCC 3-Way Graph Mutation Merger
    └── Step 0 Autonomous Complexity Triage
             │
             ▼
[ Domain Services & Infrastructure ]
    ├── Shopify Liquid & AST Engine (dnk_shopify)
    ├── Analytics & Aggregation (ClickHouse / Redis / Prometheus)
    ├── Video Synthesis Engine (Remotion / FrameCN)
    └── Self-Healing & Distillation (Error Solution Database)
```

---

## 2. Swarm Agents Architecture

DNK OS defines 14 specialized autonomous agent personas configured in `core/orchestrator/agents/`:

1. **`gerych_prime`**: Chief Orchestrator, Swarm Manager, TaskDNA decomposition.
2. **`gerych_builder`**: High-velocity UI, React/Next.js frontend, and Canvas mutations.
3. **`gerych_researcher`**: SOTA repository assimilation, AST extraction, GitHub API research.
4. **`gerych_auditor`**: Adversarial red-team auditor, security verification gates, test suites.
5. **`dnk_shopify`**: E-commerce Liquid AST mutations, Shopify Functions, Checkout UI.
6. **`dnk_dev_fullstack`**: FastAPI backend routers, SQLAlchemy models, migration engines.
7. **`dnk_video_ai_creator`**: Programmatic Remotion video generation, marketing creatives.
8. **`dnk_scones_memory`**: Episodic memory consolidation, cognitive graph indexing.
9. **`dnk_security_guard`**: Token firewall, rate limiting, intrusion isolation.
10. **`dnk_finance_cfo`**: COGS calculation, unit economics, Stripe ledger reconciliation.
11. **`dnk_analytics`**: ClickHouse event ingestion, funnel tracking, performance telemetry.
12. **`herich_librarian`**: Knowledge base synchronization, Obsidian vault indexing, ADR curation.
13. **`dnk_mentor`**: High-level architectural invariants, mentor guidance, design patterns.
14. **`dnk_integrations`**: Third-party webhook handlers, ERP/CRM bridge adapters.

---

## 3. Verified Safety Invariants

- **Relative Paths Only**: All modules operate strictly on relative paths (`./`, `../`), completely preventing local system path leakage.
- **Fail-Closed Master Quality Gate**: Changes require 100% green test passes before integration.
- **Sanitized Configurations**: All environment variables and deployment manifests are template-only (`.env.example`).
- **Isolation of Vendored & Experimental Artifacts**: Upstream runtime checkouts and experimental UI sandbox builds are strictly isolated in quarantine.
