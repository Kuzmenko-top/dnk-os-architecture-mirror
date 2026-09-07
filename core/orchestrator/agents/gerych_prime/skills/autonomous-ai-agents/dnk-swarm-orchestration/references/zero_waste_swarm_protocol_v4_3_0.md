# Zero-Waste Swarm Protocol v4.3.0 Reference

## Core Invariant Summary
Zero-Waste Swarm Protocol (ZWSP v4.3.0) enforces five strict invariants to achieve 10x engineering velocity without token, compute, or cognitive waste:

1. **TaskDNA First Invariant**:
   - Multi-step tasks must be decomposed via `dnk_decompose_task_dna(goal)` into a directed acyclic graph (DAG) of interface contracts before writing implementation code.
2. **SCONES Memory Retrieval First Invariant**:
   - Before researching or writing boilerplate from scratch, query `scones_get_memories(query=topic)` to pull existing verified solutions, architecture patterns, and domain rules.
3. **Instant Self-Healing Distillation (Zero-Guessing Invariant)**:
   - When a test or build fails, DO NOT iteratively guess. Immediately query `dnk_query_error_solutions(error_text)` to find the distilled fix. Once verified, record the solution with `dnk_record_error_solution`.
4. **Context Diet & Circuit Breakers**:
   - Limit file inspection to targeted slices (80–120 lines) or interface declarations.
   - Circuit breakers in `core/hermes_pre_tool_hook.py` intercept repeated read loops or consecutive file modifications without intermediate test verification.
5. **Fail-Closed Verification & Signed Evidence**:
   - Completion requires 100% green test execution (`bash scripts/verify_all.sh`).
   - Deliverables must include signed evidence artifacts via `python3 scripts/system/generate_evidence.py --task <TASK_ID> --title "<TITLE>" --components <FILES...>`.

## Waste Classification & Prevention Matrix
| Waste Category | Typical Symptom | Prevention Mechanism |
| :--- | :--- | :--- |
| **Token Waste** | Dumping 1k+ line files into LLM context | Context Diet (80-120 lines), AST extraction |
| **Cycle Waste** | Blind trial-and-error patches in loops | Instant Distillation (`dnk_query_error_solutions`) |
| **Drift Waste** | Re-implementing existing modules | SCONES RAG (<0.05s retrieval) |
| **Orphan Waste** | Zombie background processes, DB locks | Process Guard (`process_guard.py --check-lock`) |
| **Fabrication Waste** | Verbal claims of working fixes without tests | Strict gate: `verify_all.sh` + Evidence JSON |

## Swarm Role Matrix
- **Decider / Orchestrator**: `gerych_prime` / `antigravity` (TaskDNA DAG, budget, dispatch)
- **Implementers**: `gerych_builder` (UI/Canvas), `dnk_dev_fullstack` (FastAPI/ORM), `dnk_shopify` (Liquid/Checkout), `dnk_video_ai_creator` (Media/Remotion)
- **Researcher**: `gerych_researcher` (AST, license audit, repo mapping)
- **Verifier / Gatekeeper**: `gerych_auditor` (Adversarial review, test failure stress testing)
- **Security**: `dnk_security_guard` (5-Sink Leak Prevention Rule, SSRF, secret containment)
- **Accounting**: `dnk_finance_cfo` / `core/accounting_engine.py` (Tokens, cost telemetry, SpendGuard)
- **Librarian**: `herich_librarian` / `dnk_scones_memory` (MRH validation, ADR cataloging, SCONES sync)
