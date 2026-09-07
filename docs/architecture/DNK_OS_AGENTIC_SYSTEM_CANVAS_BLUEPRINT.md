# --- DNK-MRH-HEADER ---
# mrh_id: "docs/architecture/DNK_OS_AGENTIC_SYSTEM_CANVAS_BLUEPRINT.md"
# purpose: "Master Architectural Blueprint: Agentic Infinite Node-Based Canvas System for DNK OS (CapCut AI + Google Stitch Paradigm)."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "Gerych Prime & Maxim Kuzmenko"
# --- END DNK-MRH-HEADER ---

# 🌐 DNK OS Agentic Canvas & Project Operating System: Master Blueprint

## 📌 1. Executive Summary & Vision

This blueprint establishes the unified architecture for the **DNK OS Agentic Project System** — an infinite, node-based workspace pairing the precision visual engineering of **CapCut AI Design** with the minimalist, multi-variant generative aesthetics of **Google Stitch** (`stitch.withgoogle.com`).

The system serves as the single pane of glass for business project creation, operational steering, media production, and competitive social intelligence. It leverages the complete engineering capacity of the **DNK_HUB** headquarters:
- **Infinite Spatial Workspace**: Built on `@xyflow/react`, `JSON Canvas 1.0` (`.canvas`), and `Flowgram.ai` reactive data-flow mechanics.
- **SCONES Project & Brand Memory**: L1–L3 cognitive memory vault retaining Brand DNA, Tone of Voice (ToV), visual palettes, audience ICPs, and historical decisions.
- **14-Agent Swarm Orchestration**: Integrated via Gerych Prime and FastMCPKernel, delegating specialized roles (frontend, backend, Shopify Liquid, video generation, security, auditing).
- **Generative Media & Video Intelligence Factory**: Coupling BiRefNet/FLUX.1/IC-Light image manipulation with Remotion video generation and the `@dnk/video-audit-core` multimodal social video audit engine.
- **Shopify & Business Execution Engine**: Direct bidirectional synchronization of Liquid AST, UI slices, CRM funnels, and Telegram mobile approval gates.

---

## 🏛️ 2. Core Pillars & Benchmark Synthesis

### 🎯 Pillar 1: Visual Paradigm — CapCut AI Design + Google Stitch
1. **Google Stitch Generative Workflow (`stitch.withgoogle.com`)**:
   - **Variant Exploration**: Instant generation of multiple layout and copy alternatives side-by-side.
   - **Adaptive Themes & Tokens**: Clean Obsidian Dark and Crisp Light modes, synchronized across typography, colors, and border geometries.
   - **Micro-Slice Preview**: Fast visual cards representing interactive components before committing to production.
2. **CapCut AI Design Interaction (`capcut.com/ai-design`)**:
   - **Point-and-Click LUI (Language User Interface)**: Contextual prompt bar accessible directly on any node, canvas coordinate, or media asset.
   - **One-Click Graphic Actions**: Immediate background cutout (BiRefNet), relighting (IC-Light), upscaling, and smart style transfers.
   - **Asset & Project Drawer**: Centralized sidebar tracking generated media assets, reference videos, brand kits, and export bundles.

### 🧠 Pillar 2: SCONES Brand & Project Memory Engine
- **Workspace Isolation**: Multi-tenant partitioning (`workspaceId: "ws-alpha-001"`), preventing cross-brand prompt and asset bleeding.
- **Brand DNA Extraction**: Automated synthesis of:
  - Visual Tokens (Primary, Secondary, Surface, Text, Accent colors; Headings and Body typography).
  - Tone of Voice (Bold, Technical, Premium, Disruptive, Casual).
  - Target ICP Matrix and Unique Selling Propositions (USPs).
- **Prompt Co-Pilot**: Transparent enrichment layer transforming casual user prompts into high-precision, brand-aligned generation prompts for LLMs and diffusion models.

### 🐝 Pillar 3: Swarm Collaboration & Task Forest
- **Topology**: Directed Acyclic Graphs (DAGs) and hierarchical Task Forests representing business stages:
  `Strategy ➔ Research ➔ Brand Design ➔ Web Components (Liquid/React) ➔ Media Factory (Photo/Video) ➔ Social Audit ➔ Execution Kanban`.
- **Reactive Data-Flow (Flowgram.ai Pattern)**: Upstream parameter changes (e.g. updating a primary brand color in `DesignGalleryNode`) automatically propagate through connected handles to downstream nodes (`ShopifyBuilderNode`, `VideoCreatorNode`, `SprintKanbanNode`) without full canvas re-renders.
- **Human-in-the-Loop & Budget Guard**: Real-time credit and token calculation prior to high-cost generation runs (video rendering, heavy diffusion, bulk audits), requiring explicit user sign-off.

---

## 🏗️ 3. End-to-End System Architecture & DNK_HUB Mapping

```
+----------------------------------------------------------------------------------------------------+
|                                    DNK OS SPATIAL CLIENT (Next.js 14 / Vite)                      |
|                                                                                                    |
|  +---------------------------+  +---------------------------------------------------------------+  |
|  |     LAUNCHPAD & DRAWER    |  |               INFINITE NODE-BASED CANVAS                      |  |
|  | - Business Project Index  |  | - @xyflow/react (60 FPS Engine + RBush Spatial Culling)       |  |
|  | - 4-Step Onboarding       |  | - JSON Canvas 1.0 (.canvas) Import/Export                     |  |
|  | - Brand Memory (SCONES)   |  | - 12+ Custom Domain Nodes (CapCut / Stitch Style)             |  |
|  | - Asset & Video Vault     |  | - CopilotToolbar (Cmd+K In-Place AI Prompting)                |  |
|  +-------------+-------------+  +-------------------------------+-------------------------------+  |
+----------------|------------------------------------------------|----------------------------------+
                 | WebSocket / REST                               | WebSocket / REST
+----------------v------------------------------------------------v----------------------------------+
|                                  DNK KERNEL & BACKEND SERVICES                                     |
|                                                                                                    |
|  +---------------------------+  +---------------------------+  +--------------------------------+  |
|  |    dnk_canvas_api (8000)  |  |   SWARM ORCHESTRATOR      |  |    packages/video-audit-core   |  |
|  | - Canvas State Sessions   |  | - Gerych Prime (Nous)     |  | - Social Video Ingestion       |  |
|  | - Live WebSocket Bridge   |  | - gerych_builder (UI)     |  | - WhisperX Ukrainian ASR       |  |
|  | - Fast-JSON-Patch Undo    |  | - dnk_shopify (Liquid)    |  | - OCR & Scene Extraction       |  |
|  | - PostgreSQL / IndexedDB  |  | - dnk_dev_fullstack (API) |  | - Multimodal Claim Audit       |  |
|  +-------------+-------------+  +-------------+-------------+  +---------------+----------------+  |
|                |                              |                                |                   |
|  +-------------v-------------+  +-------------v-------------+  +---------------v----------------+  |
|  |   dnk_canvas_worker (GPU) |  |   dnk_video_ai_creator    |  |    packages/teleprompter-core  |  |
|  | - BiRefNet (Cutout)       |  | - Remotion Video Engine   |  | - Word State Machine FSM       |  |
|  | - IC-Light (Relighting)   |  | - Automated Voiceover     |  | - Real-time Audio Sync         |  |
|  | - FLUX.1 + LayerDiffuse   |  | - 9:16 Shorts Generation  |  | - Dynamic WPM Pacing           |  |
|  +---------------------------+  +---------------------------+  +--------------------------------+  |
+----------------------------------------------------------------------------------------------------+
```

---

## 🧩 4. Key Subsystems & Domain Modules

### 1. Spatial Canvas Engine (`apps/web/components/canvas/`)
- **Node Matrix**:
  - `StrategyMarkdownNode`: Goals, business model, ICP definition.
  - `MarketResearchNode`: Competitor breakdown, social hooks, audience desires.
  - `ConceptMindmapNode`: Idea synthesis, feature branches.
  - `DesignGalleryNode`: Brand colors, typography, UI moodboards, logo assets.
  - `PhotoStudioNode`: In-canvas image generation, cutout, relighting, asset cropping.
  - `VideoCreatorNode`: Storyboard frames, caption timing, Remotion composition controls.
  - `LiveWebPreviewNode` & `ShopifyBuilderNode`: Interactive Liquid AST and React component rendering with live code view.
  - `VideoAuditReportNode`: Multimodal social video intelligence output, hook retention curves, and claim verification.
  - `SprintKanbanNode`: Actionable tasks, agent delegation status, verification checklist.
- **Spatial Mechanics**:
  - **Level-of-Detail (LOD)**: Light WebP/SVG proxy rendering when zoomed out `< 0.6x`; full interactive mounts at `>= 0.6x`.
  - **Transaction Integrity**: Inverse RFC 6902 JSON patch stack with 100-operation ring buffer and IndexedDB offline persistence.

### 2. Multimedia & Social Video Intelligence Pipeline (`packages/video-audit-core`)
- **Multi-Platform Ingestion**: Safe SSRF-isolated downloading of TikTok, Instagram Reels, YouTube Shorts, and Telegram video assets.
- **Multimodal Decomposition**:
  - `TranscriptionAdapter`: WhisperX with calibrated Ukrainian vocabulary (e.g. specialized e-commerce and equipment terminology).
  - `SceneExtractionWorker`: Shot-boundary detection and keyframe timestamp mapping.
  - `OCRWorker`: Normalized bounding box (`[0.0, 1.0]`) screen text extraction.
  - `AudioFeatureWorker`: Energy, pitch, music detection, pause cadence.
- **Audit & Claim Reasoning**:
  - Verification of claims classified strictly into `observed` (timestamp-grounded), `inferred`, or `hypothesized`.
  - Retention & Hook Analysis (first 3 seconds viral evaluation).
  - Automated derivation of high-converting scripts into `packages/teleprompter-core`.

### 3. Generative Web Component & Liquid Engine (`services/dnk_shopify`)
- **AST Generation**: Deterministic synthesis of Shopify OS 2.0 JSON templates, Liquid sections, schema definitions, and Tailwind/React code.
- **Bi-directional Sync**: Edits on the visual canvas update code ASTs; direct code changes reflect immediately on the canvas canvas cards.
- **Sandboxed Execution**: Isolated iframe runtimes with `postMessage` event interception for interactive prototype testing.

---

## 🗺️ 5. Implementation Roadmap (Phases 3 to 6)

| Phase | Milestone | Key Deliverables | Verification Gate |
|---|---|---|---|
| **Phase 3** | **Swarm Co-Pilot & Reactive Cascade** | • `CopilotToolbar` in all core nodes<br>• Streaming token generation<br>• Topological multi-node propagation (`propagateSwarm`) | `swarm-copilot-phase3.test.ts` (100% Green) |
| **Phase 4** | **CapCut AI Photo Studio & GPU Worker** | • BiRefNet cutout integration<br>• IC-Light relighting API adapter<br>• In-canvas bounding-box selection & replacement | Headless AI Adapter tests (`canvas-worker`) |
| **Phase 5** | **Video Intelligence & Social Audit Node** | • Mounting `@dnk/video-audit-core` into Canvas<br>• Visual Hook & Retention curve chart node<br>• Social video URL ingestion dialog | Vitest pipeline test suite & E2E Node test |
| **Phase 6** | **Remotion Video Factory & Live Shopify Sync** | • In-canvas Remotion player preview<br>• 9:16 Shorts template compilation<br>• Live Store Liquid sync via Shopify Admin API | Docker Compose full stack verification |

---

## 🛡️ 6. Production Quality Invariants

1. **Relative Path Discipline**: All imports, tools, and scripts strictly respect relative repository hygiene (`./`, `../`).
2. **Deterministic Offline-First**: Visual nodes must hydrate from local IndexedDB/fallback DBs before attempting network sync.
3. **Budget Guard Invariant**: Heavy GPU or model inference tasks require explicit cost preview and user approval.
4. **Master Quality Gate**: `bash scripts/verify_all.sh` must remain 100% green before any feature branch merges.
