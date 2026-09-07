# --- DNK-MRH-HEADER ---
# mrh_id: "skills/software-development/sota-repository-assimilation/references/github_sota_ingestion_and_swarm_adaptation.md"
# purpose: "Reference Guide: Live GitHub & Web SOTA Ingestion, License Routing, and 14-Agent Swarm Adaptation."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-04"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 🌐 Live GitHub & Web SOTA Ingestion and Swarm Adaptation

## 1. Context & Objectives
When scouting external technologies, open-source libraries, and architectural paradigms from GitHub and the web:
- Rapidly deconstruct technical architectures without context bloat.
- Strictly adhere to intellectual property boundaries (Two-Track Licensing).
- Route adapted capabilities directly to the 14 specialized Swarm agents in DNK OS.

---

## 2. Ingestion Tooling & Protocols

### A. Discovery & Inspection
- **GitHub MCP Tools**: Use `mcp__github__search_repositories`, `mcp__github__get_file_contents`, and `mcp__github__list_commits` for direct, credentialed access.
- **Native `gh` CLI**: Shell commands automatically inherit `$GH_TOKEN`. Never perform manual credential filling or regex token scraping.
- **Context7 Real-Time Docs**: Use `mcp__context7__query_docs` to pull canonical API references for fast-moving libraries before writing code.
- **Web & Headless Research**: Use `web_search`, `web_extract`, or `browser_exec` for documentation sites, academic whitepapers, and interactive demos.

### B. Two-Track License Compliance
- **Track 1 (Permissive: MIT / Apache 2.0 / BSD / ISC)**:
  - Eligible for direct component, template, and architectural pattern adaptation.
  - Maintain attribution in accordance with the upstream license.
- **Track 2 (Copyleft / Restrictive: GPL / AGPL / Proprietary / Closed)**:
  - **Clean-Room Protocol**: Reverse-engineer data flow, protocol contracts, and state machines only.
  - Code must be authored from scratch conforming to DNK OS standards.
  - No direct copy-pasting of source text or derived functions.

---

## 3. Storage & Documentation Hygiene
- **Canonical Blueprint Placement**:
  - Always write architectural specifications, integration blueprints, and digestion reports to `docs/architecture/` or `docs/tech/specs/`.
  - **Safety Invariant**: Do NOT attempt to overwrite or mutate protected agent instruction files (`SOUL.md`) during automated ingestion. Store durable principles in persistent memory (`memory`) and detailed architectures in `docs/architecture/*.md`.
- **Machine-Readable Headers (MRH)**:
  - Every markdown specification, Python adapter, or config file must include a standard `DNK-MRH-HEADER` (`mrh_id`, `purpose`, `version`, `author`).

---

## 4. 14-Agent Swarm Capability Routing
Once extracted and verified, new technical capabilities are assigned to domain workers:

| Extracted Domain | Target Swarm Agent | Typical Responsibility |
|---|---|---|
| Frontend / Canvas / Visual UI | `gerych_builder` | React/Next.js components, scene graphs, interactive canvases |
| Backend / API / Distributed Logic | `dnk_dev_fullstack` | FastAPI endpoints, Pydantic DTOs, async queues, SQLAlchemy/PostgreSQL |
| E-Commerce / Liquid / Storefronts | `dnk_shopify` | Liquid AST compilation, Shopify Functions (Rust/Wasm), Checkout UI |
| Video / Audio / Creative AI | `dnk_video_ai_creator` | Remotion programmatic video, FFmpeg pipelines, generative assets |
| Repo Intel / AST Deconstruction | `gerych_researcher` | Deep code inspection, tree-sitter AST queries, upstream diff tracking |
| Knowledge / Embeddings / Vector Memory | `dnk_scones_memory` | Vector embeddings, SCONES L1-L3 stores, brand voice indexing |
| Security / Quality Gate / Tests | `gerych_auditor` | Fail-closed testing, `verify_all.sh` execution, adversarial review |
| Firewall / Secrets Hygiene | `dnk_security_guard` | Vault token rotation, credential isolation, SSRF prevention |
| Marketing / Copywriting | `dnk_marketing_cmo` | Conversion copy, email flows, positioning frameworks |
| Unit Economics / Token Budgets | `dnk_finance_cfo` | SpendGuard quotas, LLM token unit costs, workspace billing |
| Telemetry / Analytics | `dnk_analytics` | Real-time event streams, cohort models, funnel dashboards |
| Physical Operations / Smokehouse ERP | `dnk_erp_supply` | Production workflows, batch tracking, inventory reconciliation |
| Doc Cataloging / MRH Governance | `herich_librarian` | MRH header validation, ADR indexing, technical documentation hygiene |
| Swarm Leadership & DAG Orchestration | `gerych_prime` | Master task decomposition (`dnk_decompose_task_dna`), execution routing |

---

## 5. Verification Gate
Before declaring any assimilation task complete:
1. Run target unit/integration tests (`pytest core/tests/test_*_assimilation.py`).
2. Run full system quality check: `bash scripts/verify_all.sh`.
3. Generate evidence report:
   ```bash
   python3 scripts/system/generate_evidence.py --task <TASK_ID> --title "<TITLE>" --components <FILES...>
   ```
