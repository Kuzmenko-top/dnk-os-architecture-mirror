# DNK OS — Public Read-Only Architecture Mirror

> **IMPORTANT ARCHITECTURAL NOTICE:**  
> This repository is a sanitized, read-only architectural mirror of **DNK OS** created specifically for external architectural review, peer audit, and technical analysis.  
> **This repository is NOT intended for production deployment, live hosting, or execution with real credentials.**

---

## 🧬 What is DNK OS?

**DNK OS** is an autonomous multi-agent operating system and intelligence hub built for enterprise e-commerce, content synthesis, cognitive task execution, and adaptive workflows. It integrates:
- **Autonomous Swarm Intelligence**: A 14-agent specialized swarm hierarchy orchestrated by Gerych Prime (Hermes Prime).
- **Core Cognitive Architecture**: Multi-tier episodic & semantic memory (SCONES Engine), TaskDNA evolutionary dependency trees, and Optimistic Concurrency Control (OCC) graph merging.
- **Enterprise Integrations**: Shopify OS 2.0 theme AST mutations, headless API gateways, real-time analytics streaming (ClickHouse/Redis), and programmatic video synthesis (Remotion).
- **Adversarial Resilience**: Fail-closed Master Quality Gates, red-team/blue-team pre-commit audits, and error distillation self-healing.

---

## 🏛️ Public Read-Only Mirror Purpose

This public mirror provides open visibility into:
1. The structural patterns, domain boundaries, and abstractions of DNK OS.
2. The core Python and TypeScript modules, service definitions, and test suites.
3. The architectural blueprints, specifications, ADRs, and capability baseline documentation.

All internal credentials, live API keys, customer data, local databases, and production secrets have been strictly purged per the pre-publication sanitization protocol.

---

## 🧪 Verified Components vs. Experimental Status

Based on the verified audit baseline (`docs/audit/DNK_OS_CAPABILITY_BASELINE_v0.1.md`) and comprehensive test collection (2,197 tests collected across 393 test files):

| Component / Layer | Status | Verification Evidence |
| :--- | :--- | :--- |
| **Swarm Orchestration Core** (`core/`) | ✅ Verified Green | 52 passing tests (`tests/core/test_task_triage.py`, `test_task_forest.py`, `test_occ_merge.py`, etc.) |
| **Agent-to-Agent (A2A) Protocols** | ✅ Verified Green | 52 passing tests (`tests/a2a/`) |
| **Canvas & Mindmap Engine** | ✅ Verified Green | 87 passing tests (`tests/canvas/`) |
| **Security & Auth Gates** | ✅ Verified Green | 78 passing tests (`tests/auth/`, `tests/security/`) |
| **Shopify OS 2.0 AST Engine** | ✅ Verified Green | 153 passing tests (`tests/shopify/`) |
| **Analytics & Telemetry** | ✅ Verified Green | 115 passing tests (`tests/analytics/`, `tests/monitoring/`) |
| **Deployment & Rollout Gates** | ✅ Verified Green | 45 passing tests (`tests/deployment/`) |
| **FastAPI Backend Gateway** (`apps/api`) | ⚠️ Partial / In Review | 30+ mounted routers, requires router deduplication and load testing |
| **Visual Shell & Web Studio** (`apps/web`) | ⚠️ Incomplete / In-Progress | Next.js canvas UI undergoing active integration; heavy vendor artifacts excluded |
| **Video AI Creator** (`services/dnk_video_ai_creator`) | 🔬 Experimental | Remotion composition templates verified; generative diffusion pipelines in R&D |
| **Cognitive L3 Long-Term Recall** | 🔬 Experimental | SQLite local episodic memory verified; vector embeddings undergoing scale tests |

---

## 🛡️ Safe Read-Only Verification (Local Recipe)

To safely inspect and verify the repository locally without invoking any live services or external APIs:

```bash
# 1. Clone the mirror
git clone https://github.com/Kuzmenko-top/dnk-os-architecture-mirror.git
cd dnk-os-architecture-mirror

# 2. Inspect dependency manifests
cat pyproject.toml
cat requirements.txt

# 3. Read-only syntax & test collection check (requires python 3.12+ and pytest)
python3 -m venv .venv_audit
source .venv_audit/bin/activate
pip install pytest
pytest --collect-only -q tests/
```

*Note: Running pytest in `--collect-only` mode safely indexes test signatures and test classes without executing live database queries or network sockets.*

---

## 🔒 Security Disclosure & Reporting

We maintain a strict zero-leakage security posture. If you believe you have discovered a security vulnerability, unintended artifact, or data privacy concern in this architecture mirror:
- **DO NOT open a public GitHub issue.**
- Review our full disclosure guidelines in [`SECURITY_DISCLOSURE.md`](SECURITY_DISCLOSURE.md).
- Contact our security team privately via email: **`security@dnk-e.com`**.
