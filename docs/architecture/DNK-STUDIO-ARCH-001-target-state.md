# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-STUDIO-ARCH-001-target-state"
# purpose: "Target Architecture Specification for Unified DNK OS Studio Shell (CapCut + Stitch + Taskade + Open Design)."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-30"
# author: "DNK-e.com Maksym & Antigravity Orchestrator"
# --- END DNK-MRH-HEADER ---

# 🎯 DNK-STUDIO-ARCH-001: Target State Architecture Specification

## 1. Unified Studio Shell Composition (4-Zone Layout)

The DNK OS Studio Shell consolidates all previously fragmented tools into a single, cohesive desktop-grade interface:

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ ☰  DNK STUDIO  [ReBurn E-Com ▾] / [Smoker Launch ▾]  [Canvas | Timeline | Board | Code]  [▶ Run] [Export]│
├─────────────────┬──────────────────────────────────────────────────────────────┬─────────────────────┤
│ 📚 CAPABILITY & │ 🌌 CENTRAL MULTI-MODAL STAGE                                 │ 🔬 CONTEXT          │
│    ASSET DOCK   │                                                              │    INSPECTOR        │
│                 │  [Mode: Spatial Stitch Canvas / Live Preview / Split]        │                     │
│ • Node Palette  │   • Goal Intake Node ──► Task Node ──► Agent Node            │ • Node Properties   │
│ • Open Design   │   • Live Web Sandbox (Interactive Shopify Theme / React UI)  │ • Code Diff Viewer  │
│   Components    │   • Component Slices (Hero, 3D Product, Specs)               │ • PR Inspector      │
│ • Cloud Media   │   • Approval Gate Node (Deploy Authorization)                │ • SCONES L3 Memory  │
│   Vault (4K)    │                                                              │ • Governance Center │
│ • Templates     │                                                              │                     │
│ • 14 Swarm      ├──────────────────────────────────────────────────────────────┴─────────────────────┤
│   Agents        │ ⏱️ BOTTOM EXECUTION TIMELINE & A2A TRACE DRAWER                                    │
│                 │  • 00:00 [Scrubber] ── [Track 1: Video] [Track 2: Voice] [Track 3: Shopify AST]    │
│                 │  • [A2A Telemetry Stream: dnk_shopify (200ms) | gerych_auditor (Passed)]           │
└─────────────────┴────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Component Reuse & Consolidation Matrix

Instead of rewriting existing code, we map existing proven components directly into their target positions:

| Target Studio Zone | Existing Component Source | Integration & Refactoring Action |
| :--- | :--- | :--- |
| **Top Navigation** | `StitchTopNav.tsx` + `HubTopBar.tsx` | Merged into `StudioTopBar.tsx` with workspace breadcrumbs, mode switcher, and preset selector. |
| **Left Library Dock** | `HubSidebar.tsx` + `MediaAssetsVaultSection.tsx` + `OpenDesignCustomizerModal.tsx` | Unified into collapsible `CapabilityDock.tsx` (Nodes, Assets, Open Design, Agents). |
| **Center Infinite Stage** | `StitchCanvas.tsx` + `LiveWebPreviewNode.tsx` + `ComponentSliceNode.tsx` | Core `StudioStage.tsx` with view switching: `canvas`, `preview`, `split`, `timeline`, `board`. |
| **Right Inspector** | `ArtifactPanel.tsx` + `InspectorPanel.tsx` + `CabinetShell.tsx` tabs | Unified tabbed `ContextInspector.tsx` (Properties, Diffs, PR Review, Memory L3, Governance). |
| **Bottom Timeline** | `VideoPreviewModal.tsx` + `timeline.py` + `a2a_monitor.py` | Integrated `ExecutionTimelineDrawer.tsx` (Multitrack media scrubber & live A2A telemetry). |
| **Command Bar** | `CommandBar.tsx` + `StitchPromptDock.tsx` | Global `⌘K` prompt capsule for instant natural language goal composition and UI edits. |

---

## 3. Unified Session State (`StudioSessionStore`)

All UI state is unified into a single React / Zustand store avoiding split-brain desynchronization:

```typescript
export interface StudioSessionState {
  // Context SSOT
  tenantId: string;
  workspaceId: string;
  projectId: string;
  canvasId: string;
  workflowId: string | null;
  activeExecutionId: string | null;

  // Viewport & Layout
  activeStageMode: 'canvas' | 'preview' | 'split' | 'timeline' | 'board' | 'whiteboard';
  isLeftLibraryOpen: boolean;
  isRightInspectorOpen: boolean;
  isBottomTimelineOpen: boolean;

  // Selection & Inspector
  selectedNodeId: string | null;
  selectedArtifactId: string | null;
  activeInspectorTab: 'properties' | 'diff' | 'pr_review' | 'memory_l3' | 'governance';

  // Active Design System (Open Design)
  activeDesignPresetId: string;
  brandAccentColor: string;

  // Realtime Connection State
  wsConnectionState: 'CONNECTED' | 'RECONNECTING' | 'OFFLINE_PREVIEW';
  serverVersion: number;
}
```

---

## 4. Polymorphic Artifact Preview Bus

The central stage routes artifacts dynamically based on their MIME type without hardcoded domain logic:

| Artifact Type | Render Engine | Capabilities |
| :--- | :--- | :--- |
| `shopify_liquid_theme` | Liquid AST Sandbox | Live responsive preview, interactive cart/checkout triggers. |
| `video_composition_9_16` | WebCodecs / HTML5 Video | Safe-zone overlays (TikTok/Reels), audio waveform scrubber. |
| `react_component` | Open Design Sandboxed Iframe | Hot-module reload, Tailwind CSS token injection, DOM inspection. |
| `markdown_specification` | Markdown + Mermaid Renderer | Architecture diagrams, PR review diffs, patent evidence. |
| `taskdna_dag_graph` | React XYFlow | Visual dependency layout, node status pulse, step retry. |

---

## 5. Responsive Strategy

- **Desktop (≥ 1280px)**: Full 4-zone Studio layout with multi-monitor split capabilities.
- **Tablet (768px - 1279px)**: Canvas center stage with floating collapsible drawers and bottom sheet inspector.
- **Mobile (< 768px)**: Compact **Project Control & Approval Mode** (view status, review execution alerts, 1-tap Approve/Reject).
