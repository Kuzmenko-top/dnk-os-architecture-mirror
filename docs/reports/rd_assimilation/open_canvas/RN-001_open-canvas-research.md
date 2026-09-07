# --- DNK-MRH-HEADER ---
# mrh_id: "docs/reports/rd_assimilation/open_canvas/RN-001_open-canvas-research.md"
# purpose: "SOTA Research & Evidence Trail on open-canvas"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "2.0.0"
# updated_at: "2026-08-10"
# author: "Maxim"
# license: "MIT"
# --- END DNK-MRH-HEADER ---

# 🔍 RESEARCH REPORT: OPEN-CANVAS ABSTRACTIONS & EVIDENCE

## 🚀 Executive Summary
This report analyzes open-canvas's SOTA reactive workspace architecture. It compiles direct code evidence supporting the main structural decisions in DNK OS.

## 🧱 Key Abstractions
- **Artifact (ArtifactV3)**: Versioned collection of contents (either code or markdown). Enables time-travel and editing.
- **Thread Context**: Scopes user-assistant dialog, mapping specific messages to corresponding artifact versions.
- **Graph State**: Stateful context orchestrating agent steps, memory annotations, and active UI views.

## 📋 Evidence Trail: Statement ➔ Verification
| Claim / Hypothesis | File in open-canvas | Support & Implementation Details |
| :--- | :--- | :--- |
| **ArtifactV3 Structure** | `packages/shared/src/types.ts` | **Confirmed**. Defines `currentIndex` and `contents: ArtifactContentV3[]` supporting multi-version rollbacks. |
| **State Coordinator** | `apps/web/src/contexts/GraphContext.tsx` | **Confirmed**. Exposes `useGraphContext`, managing states like `artifact`, `isStreaming`, and updating via `setArtifact`. |
| **React Flow & Canvas UI** | `apps/web/src/components/canvas/canvas.tsx` | **Confirmed**. Maps nodes representing active editors or content blocks into a single React Flow UI view. |
| **Agents Integration** | `apps/agents/src/open-canvas/state.ts` | **Confirmed**. Uses LangGraph-like state annotations `artifact: Annotation<ArtifactV3>` to pass data directly to generation/rewriting nodes. |

No raw code is included in this research record to prevent monolithic bloating.
