# --- DNK-MRH-HEADER ---
# mrh_id: "skills/autonomous-ai-agents/dnk-swarm-orchestration/references/dnk_os_infinite_canvas_and_swarm_blueprint.md"
# purpose: "Reference architecture for DNK OS Infinite Node-Based Canvas combining Google Stitch and CapCut AI Design."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-04"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 🌌 DNK OS: Infinite Node-Based Canvas & Swarm System Architecture

## 1. Executive Summary & Aesthetic Reference Benchmarks
DNK OS is designed as a next-generation agentic project management and creation operating system for users, powered by an Infinite Node-Based Canvas that unites two primary design references:
- **Google Stitch (`stitch.withgoogle.com`)**: Interactive spatial design canvas, reactive web component generation, live sandbox preview nodes, dynamic AI prompt bar, and node-to-node topological data propagation.
- **CapCut AI Design (`capcut.com/ai-design`)**: High-velocity visual media factory, multi-modal asset timeline/canvas, real-time video audit/transcription, hook scoring, Remotion programmatic video synthesis, and marketing template generation.

## 2. 11-Pillar Monorepo Asset Mapping

| Pillar | Capability Domain | DNK_HUB Production Assets | Key Protocols & Contracts |
|---|---|---|---|
| 1 | **User Cabinet & Soul** | `core/user_soul.py`, `core/scones_memory.py`, `apps/web/components/cabinet/` | Tone-of-Voice extraction, Brand Kit (hex, typography, logo), L1/L2/L3 SCONES profile |
| 2 | **Projects & Memory** | `apps/api/routers/workspace`, `core/workspace/`, `.dnk_active_project.env` | Project-scoped memory isolation, automated CSS variables / Tailwind design tokens |
| 3 | **14-Agent Swarm** | `core/swarm_engine.py`, `core/swarm_orchestrator.py`, `dnk_swarm_*` | 14 specialized worker agents dynamically dispatched via TaskDNA DAGs |
| 4 | **Web & Media Generation** | `apps/web/components/canvas/LiveWebPreviewNode.tsx`, `packages/video-audit-core/`, `RemotionPlayer.tsx` | AST React/Tailwind preview sandbox + programmatic Remotion video generator |
| 5 | **Contextual Task Injection** | `core/dna_assimilation.py`, `core/task_engine.py`, `apps/web/components/taskdna/` | Bounded context diet (80-120 lines), scoped active node subgraph inheritance |
| 6 | **Continuous Learning & Hierarchy** | `core/scones_memory.py`, `core/error_distillation/`, Obsidian Vault sync | SCONES L1/L2/L3 memory tiering, error distillation, bidirectional Obsidian sync |
| 7 | **Video & Social Media Audit** | `packages/video-audit-core/` | Sidecar caching, frame deduplication, hook/retention scoring, ASR transcription |
| 8 | **Web Research & Reverse-Eng** | `services/dnk_web_research/`, `services/dnk_git_research/`, Browser Use | DOM/AST component extraction, competitor design system assimilation |
| 9 | **Shopify & E-Com Engine** | `services/dnk_shopify/`, `services/dnk_shopify_builder/`, `ShopifyCanvasSyncBar.tsx` | Liquid AST engineering, Shopify OS 2.0 theme sections, Checkout UI extensions |
| 10 | **Business Analytics & CRM** | `apps/web/components/analytics/`, `apps/api/routers/analytics`, `accounting_engine.py` | Attribution funnels, conversion telemetry, lightweight agentic CRM connected to nodes |
| 11 | **Mind Mapping & Task Forest** | `apps/web/components/canvas/` (`CanvasEngine.tsx`, `ConnectedCanvasEngine.tsx`, `StitchSpatialToolbar.tsx`) | Infinite canvas, Task Forest DAG clustering, Obsidian bidirectional graph sync |

## 3. UI/UX Spatial Topology
- **Top Bar (`StitchTopNav.tsx`)**: Workspace selector, active project switcher, global model indicator, and Master Quality Gate status.
- **Left Chat/Intelligence Panel (`StitchLeftChatPanel.tsx`)**: Conversational co-pilot, TaskDNA status, and agent turn transcriptions.
- **Floating Spatial Docks (`StitchFloatingDock.tsx`, `StitchSpatialToolbar.tsx`)**: Contextual node creation (`+ Swarm Agent`, `+ Web Preview`, `+ Remotion Video`, `+ Shopify Theme`, `+ Note`).
- **Prompt Dock (`StitchPromptDock.tsx`)**: Natural language command center (Cmd+K) generating dynamic subgraphs on the canvas.
- **Spatial Canvas Surface (`CanvasEngine.tsx`)**: High-performance React Flow / `@xyflow/react` viewport with dark luxury glassmorphism (`#060913`).

## 4. Architectural Canonical Record
The complete architectural specification is cataloged in the Obsidian Knowledge Base:
`~/Documents/DNK_HUB My Notes/DNK_HUB My Notes/002 DNK OS - Master System Architecture & Implementation Blueprint.md`
