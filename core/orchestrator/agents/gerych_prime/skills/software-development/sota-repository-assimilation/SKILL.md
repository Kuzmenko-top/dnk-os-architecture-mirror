---
name: sota-repository-assimilation
description: Audit and assimilate open-source repos into DNK OS.
category: software-development
version: "1.0.0"
author: "DNK-e.com Maksym"
license: "MIT"
metadata:
  hermes:
    tags: ["assimilation", "reverse-engineering", "architecture", "dnk-os", "sota"]
    related_skills: ["codebase-inspection", "hermes-agent-skill-authoring"]
---

# 🧬 SOTA Repository Assimilation Pipeline (Two-Track Protocol)

## ## When to Use
Use when auditing, reverse-engineering, or integrating open-source repositories, libraries, or frameworks into DNK OS.

## 🎯 5-Level Assimilation Protocol

### 1. Discovery & License Audit
- **Zero-Clone Fast-Path Inspection**: Use GitHub MCP (`mcp__github__get_file_contents`) or `DNAAssimilationEngine.fast_license_probe(repo_url)` (or `gh api repos/:owner/:repo/contents/LICENSE`) to inspect license files, README, and manifests in <2s without cloning entire repositories.
- **SOTA Scout Background Queue & Engine**: Use `core/orchestrator/sota_scout.py` and `scripts/system/sota_scout_runner.py` for automated priority-queued assimilation (`--repo <org/repo> --enqueue`, `--process-queue`, `--assimilate-now`).
- Check repository license:
  - **Track 1 (Permissive: MIT / Apache 2.0 / BSD / ISC)**: Direct template, component, and architectural pattern assimilation into `core/` or `apps/`.
  - **Track 2 (Restrictive / Copyleft: GPL / AGPL / Proprietary)**: Clean-Room reverse engineering and architectural synthesis without direct code copying. All generated code is marked with `CLEAN-ROOM REVERSE-ENGINEERING INVARIANT`.
- **Model vs Code Split Audit**: Explicitly verify weights/dataset licenses (e.g. CC-BY-NC, OpenRAIL, custom research-only) separately from code licenses (MIT/Apache 2.0). Many repos have permissive code wrappers around non-commercial model weights.

### 2. Architecture & Packaging Deconstruction
- Audit installation paths (GUI Launchers, manual pip/uv, Docker containers, cloud workers).
- Extract core architectural components: DAG execution engines, state machines, API routes, canvas/UI bridges, model managers, and event streams.

### 3. Canonical Artifact Generation (DNK-TASK-STD-001)
Generate standard artifacts in `DNK_HUB/`:
1. **Research Digest (`RN-xxx`)**: `docs/reports/rd_assimilation/<name>/RN-xxx_<name>-research.md` (License, installation audit, technical breakdown).
2. **Architecture Specification (`DNK-ARCH-xxx`)**: `docs/tech/specs/DNK-ARCH-xxx_<name>-patterns.md` (Topologies, execution flow, component DAGs).
3. **Component Contracts (`DNK-COMP-xxx`)**: `docs/tech/specs/DNK-COMP-xxx_<name>-contracts.md` (Pydantic DTOs and abstract Python Ports).
4. **Security Standards (`DNK-SEC-xxx`)**: `docs/tech/standards/DNK-SEC-xxx_<name>-execution-sandbox.md` (Sandboxing, deserialization blocks, hardware guardrails).
5. **Assimilated Skill**: `skills/<name>_assimilated/SKILL.md` (Usage recipes and patterns for Swarm agents).
6. **Obsidian ADR & Assimilation Note (`docs/notes/xxx_<name>_sota_assimilation_audit.md`)**:
   - **Frontmatter & MRH Invariant**: Follow `docs/notes/001 Obsidian & DNK OS Documentation Standard.md` strictly. Place standard YAML frontmatter on line 1 (`--- ... ---`) with properties (`title`, `tags`, `date`, `status`, `version`), followed immediately by the muted HTML comment block `<!-- --- DNK-MRH-HEADER --- ... --- END DNK-MRH-HEADER -->`. NEVER use `# --- DNK-MRH-HEADER ---` in notes as it renders as an oversized H1 header in Obsidian instead of being dimmed/muted.
   - **Swarm Capability Routing Invariant**: Route components strictly to domain workers matching the technology (e.g. LLM fine-tuning/runtimes to `dnk_dev_fullstack` or `gerych_prime`, e-commerce to `dnk_shopify`, media only to `dnk_video_ai_creator`). Never leave template default video agents on non-media repositories.

### 4. Hexagonal Adapter Implementation
- Create the core adapter in `adapters/dnk_<name>_adapter.py` (or `core/adapters/`).
- Implement topological sort DAG execution, intermediate caching, error handling, and event streaming.
- **Decoupled Bridge Invariant**: When assimilating external UI/Canvas engines (e.g. Open Design, Figma-like tools, web dashboards), NEVER copy the agent runtime (Hermes/Gerych) into the external app. Keep Gerych as the single SSOT in DNK_HUB, and connect via a thin adapter (WebSocket / JSON-RPC / MCP bridge).

### 5. Test Suite & Verification Gate
- Write comprehensive unit & integration tests in `core/tests/test_<name>_assimilation.py`.
- Run pytest and verify 100% green status before handoff.

### 6. Embedded Runtime Assimilation & Zero-Rsync Rule
- **Execution Layer Boundary**: External runtimes (e.g. Hermes Agent) serve strictly as execution/tool engines under DNK Control Plane. Upstream capabilities do NOT grant automatic DNK OS permissions.
- **Strict Prohibition of Blind Rsync**: Never use blind `rsync` or direct directory overwrites into embedded unmanaged forks containing local patches (`run_agent.py`, `toolsets.py`, custom tools, MRH scripts).
- **Staged Assimilation**: Follow the 6-Phase Staged Upgrade Protocol (Freeze -> Baseline -> Staging Runtime -> Compatibility Audit -> Canary -> Promotion -> Rollback).

## 📚 Supporting References
- [SOTA Scout Queue & Two-Track Engine Recipes](references/sota_scout_queue_and_twotrack_engine_recipes.md): Background job queue (`ScoutJobQueue`), Two-Track license compliance, AST secret masking, and CLI runner execution patterns.
- [DNK Task Standard 001](references/dnk_task_std_001.md): Canonical artifact specification.
- [Monorepo Containerization & SSR Patterns](references/monorepo_containerization_patterns.md): Docker context optimization, multi-stage workspace targeting, and Next.js SSR build rules.
- [Visual Canvas & UI Engine Bridge](references/canvas_and_visual_engine_bridge.md): Decoupled Canvas AST, atomic mutations, and memory synchronization patterns for interactive visual tools.
- [Web Canvas & AI Design Engine Audit](references/web_canvas_reverse_engineering_audit.md): Multi-tier Canvas reverse engineering, Konva scene-graph extraction, DI containers, and telemetry capture methodology.
- [Undo/Redo Command Pattern & IndexedDB Persistence Audit](references/undo_redo_command_pattern_and_indexeddb_audit.md): Reverse-engineering invertible commands, continuous coalescing (`pushWithOperateId`), differential snapshots, and multi-store IndexedDB caching.
- [WebAssembly & WebGL Reverse Engineering Patterns](references/wasm_webgl_reverse_engineering_patterns.md): WASM binary interception, wasm-decompile C reconstruction, WebGL shader extraction, and typography offscreen buffer analysis.
- [Audit Exclusion Manifest & Fingerprinting Patterns](references/audit_exclusion_manifest_patterns.md): SSOT exclusion journal, structural SHA-256 fingerprinting, and zero-waste audit traversal for large-scale assimilated repositories.
- [Modular Brick Foundry & Registry Patterns](references/modular_brick_foundry_and_registry_patterns.md): Distribute-as-Code, Application Blueprint DSL, FastMCP brick interop, and topological DAG resolution.
- **Google Stitch & Open Canvas AI Assimilation Patterns**: Google Stitch SDK, MCP JSON-RPC tool contracts, Screen DAG state machine, and DESIGN.md token integration.
- **Google Pics AI Media Engine Assimilation Patterns**: Nano Banana / Gemini Flash Image multimodal ingestion, object segmentation, in-image typography translation, and multi-image prompt grounding.
- [Gemini Agentic Video Understanding Assimilation Patterns](references/gemini_agentic_video_assimilation.md): Agentic timeline navigation (`processing="agentic"`), trace step analysis (`thought`/`processing_call`/`processing_result`), and sub-second moment retrieval.
- [AI-Native SDLC & INTENT.MD Artifact Patterns](references/ai_native_sdlc_and_intent_artifact_patterns.md): Bottleneck inversion, Golden Thread (intent -> spec -> plan -> evidence), Anti-Tampering test hooks, and Git worktree swarm isolation.
- [Gemini Agentic Video Understanding Assimilation Patterns](references/gemini_agentic_video_assimilation.md): Agentic timeline navigation (`processing="agentic"`), trace step analysis (`thought`/`processing_call`/`processing_result`), and sub-second moment retrieval.
- [Custom Tool Signature Hygiene & WCAG AA Linter Pitfalls](references/custom_tool_signature_and_wcag_linter_pitfalls.md): `task_id` kwargs injection patterns, WCAG AA linter findings safety, and two-tier relocation rules.
- [Agno Multi-Agent & Workflow DAG Assimilation](references/agno_multiagent_workflow_and_hitl_assimilation.md): Multi-agent spatial coordination (Route, Broadcast, Tasks, Consensus), serialized HITL checkpoints, and SCONES memory sync.
- [Safe Staged Assimilation of Embedded Runtimes (Zero Blind Rsync)](references/hermes_v0210_monorepo_assimilation.md): Embedded dependencies staged upgrade protocol, strict prohibition of blind rsync overwrites, isolation of staging runtime, compatibility audits, canary gates, and 30-second rollback drill.
- [Beads AI-Native Tracker & Context Engineering](references/beads_ai_native_tracker_and_context_engineering.md): Steve Yegge's AI-Native DAG tracking, context diet, minimal issue compaction, atomic lease claims, and provenance logging.
- [Social Knowledge Base Video RAG Assimilation](references/social_knowledge_base_video_rag_assimilation.md): Multi-modal video ingestion, local GPU/CPU sidecar caching, incremental Map-Reduce indexing, and timestamp click-to-seek UI integration.
- [Post-Assimilation Cleanup & Bloat Audit Protocol](references/post_assimilation_cleanup_and_bloat_audit.md): Decommissioning staging/backup runtimes, preventing compile check timeouts, isolating agent runtime state, and resolving accidental recursion.
- [Upstream Monorepo Assimilation & Cycle Preservation Invariants](references/upstream_monorepo_assimilation_and_cycle_preservation.md): 5-stage controlled ingestion, backup oracle, native C++ ABI rebuild (`better-sqlite3`), circular re-export prevention in provider adapters, and Turbopack dev overlay zero-error verification gates.
- [MCP Video Analyzer RAG Assimilation](references/mcp_video_analyzer_rag_assimilation.md): Loom GraphQL direct metadata/stream scraper, dHash perceptual frame deduplication, OCR preprocessing, and Gemini Agentic Video Exploration Loop.
- [Remotion v5 Clean-Room Media Engine & Timeline Patterns](references/remotion_clean_room_media_engine_patterns.md): Track 2 Clean-Room synthesis, Frame-as-a-Function-of-Time, relative Sequence nesting, spring dynamics, and headless Chromium CDP to FFmpeg stdio pipeline.
- [Archify Spatial Diagram Compiler & Hexagonal Patterns](references/archify_spatial_diagram_compiler_patterns.md): Typed JSON IR compilation to standalone HTML/SVG, typography geometry layout validation, and multi-domain Swarm mapping.
- [Live GitHub SOTA Ingestion & 14-Agent Swarm Adaptation](references/github_sota_ingestion_and_swarm_adaptation.md): Live GitHub/Web innovation scouting (`gh` CLI, GitHub MCP, Context7), Two-Track license routing, and capability distribution across the 14-agent swarm.
- [Plannotator Artifact Server: Visual HITL Review & Agent Dispatch Patterns](references/plannotator_artifact_server_hitl_review_patterns.md): Track 2 AGPL-3.0 clean-room sidecar boundary, in-tree hexagonal port & adapter (`DNKArtifactServerAdapter`), version immutability diffing, HtmlElementAnchor DOM pinning, cross-frame postMessage isolation, and pull-based dispatch_inbox agent mailbox patterns.
- [DeepSeek Harness (dsh) Microkernel, Tool Waterfall & PTC Patterns](references/deepseek_harness_plugin_microkernel_and_ptc_audit.md): Cordis reversible plugin microkernel, 5-stage guarded tool execution pipeline, Programmatic Tool Calling (PTC) dynamic SDK synthesis, OS-level Landlock/Seatbelt sandboxing, and twin in-repo/Obsidian assimilation documentation.
- [PersonaLive & EditaLive Real-Time Avatar & HKM Streaming Patterns](references/personalive_realtime_avatar_and_hkm_streaming_patterns.md): Track 2 Clean-Room synthesis for sub-30ms portrait animation, EditaLive full-body/editing evolution, hybrid motion signals (3D keypoints + implicit patches), 1-4 step DDIM distillation, sliding queue, Blackwell/RTX 50 acceleration quirks, drift-free HKM cache updating, and FastAPI async generator WebSocket streaming invariants.
- [Agentic Habits: Three-Tier Enforcement, Completion Gates & Anti-Habit Auditing](references/agentic_habits_three_tier_enforcement_and_completion_gates.md): Track 1 MIT template assimilation for deterministic behavioral governance: Stated (budget-capped When->Do cards), Gated (fail-open stop hooks for claim vs. execution verification), Judged (read-only habit-judge Evidence Ledgers), and 12 Anti-Habits matrix.
- [Global SOTA Agent Architectures Audit & Ingestion Blueprint](references/global_sota_agent_architectures_audit_and_benchmarks.md): Comparative technical audit against LangGraph (cyclic stategraphs & checkpoints), Letta/MemGPT (OS-style memory hierarchy & self-editing tools), Agno (low-latency core), Aider (Tree-Sitter RepoMap), and MetaGPT (SOP artifact pipelines).
- [SOTA Context Management & Compression Patterns](references/sota_context_management_and_compression_patterns.md): 6-level taxonomy and patterns from Hermes LCM (lossless SQLite FTS5 DAG), Continuous Claude (continuity ledgers & YAML handoffs), MCP Slim Guard (JIT tool schema virtualization), Git Context Controller (branching context), CodeGraph-Rust (in-memory AST GraphRAG), and NeurIPS 2025 deterministic observation masking.
- [Fast MCP License Audit & AST Dependency Call Graph](references/fast_license_audit_and_ast_call_graph.md): Zero-clone license verification via GitHub MCP / REST fallback, and sub-50ms AST symbol dependency and call graph resolution via `repo_map.py --graph`.
- [Patchright Zero-CDP & Anti-Detect Browser Automation Patterns](references/patchright_zero_cdp_stealth_scraping_patterns.md): Undetectable Playwright fork patterns, eliminating `Runtime.enable`/`Console.enable` CDP domains, `ts-morph` AST driver patches, and closed shadow DOM piercing for Cloudflare Turnstile/DataDome evasion.
- [HKUDS/RAG-Anything Multimodal Knowledge Graph Assimilation Patterns](references/rag_anything_multimodal_knowledge_graph_assimilation.md): Multi-stage document decomposition (MinerU, Docling), ModalityProcessors (images, tables, LaTeX equations), LightRAG dual-level entity graphs, cross-workspace multi-knowledge-base retrieval, grounded marketing banner synthesizer (AIDA/PAS/Remotion/SVG/Canvas), FastAPI DI endpoints, Swarm tools (`core/orchestrator/tools/`), and SCONES/Canvas sync.
- [Soup Cognitive Architecture: Tool Compilation, Dual-Leg Gates & Reward Synthesis](references/soup_layer_streaming_and_weight_ci_gate_patterns.md): Frontier Google Gemini logic assimilation: tool schema optimization (`compile-tools`), dual-leg prompt/skill regression gates (`soup ship`), deterministic Python reward synthesis with negative calibration, and drift monitoring.
- [Taskade Architecture Patterns: Unified Tree AST, Delta OT & Memory-as-Projects](references/taskade_unified_tree_ast_and_memory_projects_patterns.md): Unified hierarchical tree AST (multi-view projections for List/Board/MindMap/Canvas), Delta Operational Transformation (OT), Memory as Projects (transparent human-editable agent memory), Workspace DNA bundles (`SpaceBundleData`), and Cortex `ai-elements` UI components.
- [Graphify Architecture & Assimilation Blueprint](references/graphify_ast_knowledge_graph_and_obsidian_canvas_assimilation.md): Deterministic Tree-sitter AST, Leiden clustering, Obsidian Canvas (`.canvas`) layout engine, God Node & 12k-LOC component decomposition, circular import decoupling, and zero-vector code graph traversal.
- [Chief of Staff v2: Obsidian Chair Anatomy & Subtraction Rebuild](references/chief_of_staff_obsidian_chair_anatomy_and_subtraction_rebuild.md): 4-part Chair Anatomy (Skill, Source, Parts, Archive), inward-facing Physical Plant chair, 13 operational laws, Subtraction Rebuild against system bloat, and Morning/End session rhythms.
- [jdpolasky Ecosystem: Bitemporal Memory & BloatBot Dyad](references/jdpolasky_ecosystem_bitemporal_memory_and_bloatbot_dyad.md): Bitemporal SQLite fact store (valid_time vs tx_time), JSON Schema write contracts, BloatBot & BuildBot equilibrium protocol, and 3-tier context retrieval.
