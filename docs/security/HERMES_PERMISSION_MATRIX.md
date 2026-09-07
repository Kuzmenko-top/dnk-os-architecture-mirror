# --- DNK-MRH-HEADER ---
# mrh_id: "docs_security_hermes_permission_matrix"
# purpose: "Permission matrix and tool access controls for the 14 DNK OS swarm profiles running on Hermes runtime."
# canonical_source: true
# alters_files: []
# triggers_tasks: ["DNK-HUB-ARCH-002"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "Gerych (Hermes Prime) & Maksym"
# --- END DNK-MRH-HEADER ---

# 🛡️ Hermes Swarm Profiles Permission Matrix

The 14 DNK OS swarm profiles operate under strict least-privilege scoping. They are NOT 14 equal supervisors; they represent specialized roles governed by Gerych Prime and the DNK Control Plane.

---

## 1. Role Classification

```text
Supervisor:
  • gerych_prime        (Root Orchestration, Quality Gates & Maxim Interface)

Research & Memory:
  • gerych_researcher   (AST Code Mining, GitHub SOTA Scouting, Benchmarks)
  • herich_librarian    (Repo Knowledge Assimilation, Architecture RFCs)
  • dnk_scones_memory   (Vector Embeddings, Cognitive Memory L1/L2 Management)

Builders:
  • gerych_builder      (Fullstack UI, React, Vite, Fast Prototyping)
  • dnk_dev_fullstack   (FastAPI, Backend Microservices, DB Models, OCC)
  • dnk_shopify         (Liquid AST, OS 2.0 Themes, Dev Store Sandbox Preview)
  • dnk_video_ai_creator(Remotion Compositions, Media Assets, Audio Pipelines)

Verification & Security:
  • gerych_auditor      (Quality Gates, Adversarial Pre-Commit Review, Test Suites)
  • dnk_security_guard  (Firewall, Token Scans, Dependency Vulnerability Audits)

Operations & Finance:
  • dnk_finance_cfo     (Token Cost Accounting, Unit Economics, Workspace Spend)
  • dnk_analytics       (Traffic, Event Funnels, System Performance Metrics)
  • dnk_erp_supply      (Catalog Sync, Inventory Feeds, Supplier API Bridges)
```

---

## 2. Capability & Permission Matrix

| Profile | File System Access | Shell / Execution | Web / Network | Peer DMs | Instruction File Write | Production Deploy |
|---|---|---|---|---|---|---|
| `gerych_prime` | Full Hub | Full terminal | Full external | Any Profile | Approval Required | Approval Required |
| `gerych_researcher` | Read-only | Read-only tools | Web extract / GH API | `herich_librarian`, `builder` | ⛔ FORBIDDEN | ⛔ FORBIDDEN |
| `herich_librarian` | Read-only + `docs/` write | Read-only tools | GitHub API | `researcher`, `prime` | ⛔ FORBIDDEN | ⛔ FORBIDDEN |
| `dnk_scones_memory` | `memory/` scoped | Python embedded | Internal network only | `prime`, `auditor` | ⛔ FORBIDDEN | ⛔ FORBIDDEN |
| `gerych_builder` | `apps/web/` scoped | Node/Vite build | Localhost only | `prime`, `auditor` | ⛔ FORBIDDEN | ⛔ FORBIDDEN |
| `dnk_dev_fullstack` | `apps/api/`, `core/` | Pytest, Python | Localhost / DB only | `prime`, `auditor` | ⛔ FORBIDDEN | ⛔ FORBIDDEN |
| `dnk_shopify` | `services/shopify/` | Theme CLI (Dev Store) | Dev Store Sandbox ONLY | `prime`, `auditor` | ⛔ FORBIDDEN | ⛔ STRICT APPROVAL |
| `dnk_video_ai_creator` | `services/video/` | Ffmpeg, Remotion | Asset CDN only | `prime`, `builder` | ⛔ FORBIDDEN | ⛔ FORBIDDEN |
| `gerych_auditor` | Full Hub (Read) | Pytest, linters, verify scripts | Local test harness | `prime`, all builders | ⛔ FORBIDDEN | ⛔ FORBIDDEN |
| `dnk_security_guard` | Full Hub (Read) | Security linters | Local checks only | `prime`, `auditor` | ⛔ FORBIDDEN | ⛔ FORBIDDEN |
| `dnk_finance_cfo` | Accounting DB (Read) | Calculation tools | Local only | `prime` | ⛔ FORBIDDEN | ⛔ FORBIDDEN |
| `dnk_analytics` | Telemetry logs (Read) | Metrics scripts | Analytics endpoints | `prime` | ⛔ FORBIDDEN | ⛔ FORBIDDEN |
| `dnk_erp_supply` | Inventory DB scoped | Sync scripts | Supplier Sandbox APIs | `prime`, `dev_fullstack` | ⛔ FORBIDDEN | ⛔ FORBIDDEN |

---

## 3. Strict Boundary Invariants

1. **Self-Modification Block**: No agent profile (including `gerych_prime`) may alter `AGENTS.md`, system prompt headers, or security matrix files without explicit user approval.
2. **Production Store Isolation**: `dnk_shopify` is strictly barred from modifying live production store themes or checkout functions. All work must target development stores (`*.myshopify.com/preview`).
3. **SCONES L3 Quarantine**: Unaudited subagent output is never committed directly to long-term L3 memory. It must pass through Gerych Prime's verification gate.
