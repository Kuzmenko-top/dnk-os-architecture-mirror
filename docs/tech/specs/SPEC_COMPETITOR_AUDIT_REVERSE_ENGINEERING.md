# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/specs/SPEC_COMPETITOR_AUDIT_REVERSE_ENGINEERING.md"
# purpose: "System specification and architectural design blueprint for Competitor Audit and Reverse Engineering Service"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Draft"
# version: "1.0.0"
# updated_at: "2026-08-10"
# author: "Maxim"
# license: "DNK-INTERNAL"
# --- END DNK-MRH-HEADER ---

# 🧬 System Specification: DNK OS Competitor Audit & Reverse Engineering Service (`dnk-audit-rev-eng`)

## 1. Context & Motivation
Competitor benchmarking and layout curation is highly repetitive and manual. To build state-of-the-art experiences in DNK OS, we need an autonomous visual-technical workbench. Instead of isolated screens on static boards like Miro, we require an **interactive, infinite design sandbox** integrated with automated crawlers, vision-to-code synthesis engines, and structural code extraction mechanisms.

---

## 2. Comparison of Visual Canvas Engines

| Criteria | Excalidraw | tldraw (SOTA Choice) | ReactFlow / XYFlow (Active) | Obsidian Canvas |
| :--- | :--- | :--- | :--- | :--- |
| **Drawing & Sketching** | Excellent (Hand-drawn) | Very Good (Vector-precise) | Not supported out of the box | Good |
| **Node Customizability**| Medium (static assets/SVG) | Outstanding (Arbitrary React UI)| Outstanding (Fully Custom Nodes)| Low (Markdown-based blocks) |
| **Automated Layouts**   | Hard to layout programmatically| Built-in shapes graph + SDK | Excellent (dagre/elk graphs) | Manual |
| **Rich HTML Sandbox**   | No (strictly canvas/images) | Yes (custom HTML iFrame shapes)| Yes (sandboxed iframe nodes) | Limited |
| **AI Integration API**  | Poor (JSON export exists but limited)| Perfect (JSON state tree, SDK) | Perfect (React state binding) | Easy JSON but no runtime API |
| **Use-Case in DNK OS**  | Good for rough wireframes | **Primary Visual Brain for Ideas**| **System DAGs & Component Editor**| Local knowledge map |

### Why `tldraw` is the Ultimate Audit Canvas
`tldraw` provides a highly extensible React SDK where every element is represented as a structured node inside an Abstract Document Tree (ADT). We can easily implement the **"Make Real" pattern**:
1. Drag a screenshot of a competitor's button, checkout, or bento grid onto the tldraw canvas.
2. The AI uses multimodal OCR and layout analysis to detect visual components.
3. Clicking "Synthesize" invokes the custom AI agent to convert the screenshot bounding box into Tailwind, React, or Shopify Liquid code.
4. The synthesized code renders as a live `IFrame` shape right next to the original screenshot on the same infinite canvas.

---

## 3. Core Architectural Blueprint (`dnk-audit-rev-eng`)

We define a 3-Tier architecture running strictly inside Docker and bridging to our Next.js visual shell.

```
       +-------------------------------------------------------+
       |             TIER 1: MULTIMODAL AUDIT CANVAS            |
       |  (tldraw Canvas Viewport + ReactFlow Engine + UI)     |
       +----------------------------+--------------------------+
                                    |
                  Pushes drag-and-drop screenshots, URLs,
                  and selected DOM nodes to backend
                                    |
                                    v
       +-------------------------------------------------------+
       |             TIER 2: REVERSE ENGINEERING AGENT         |
       |  (dnk_koder AI Router + headless crawler + CSS parser)|
       +----------------------------+--------------------------+
                                    |
                  Extracts raw styles, parses color weights,
                  synthesizes structure using vision models
                                    |
                                    v
       +-------------------------------------------------------+
       |             TIER 3: MOLECULAR CODE CONVERTER           |
       |  (Compiles into Liquid Blocks / React Canvas Nodes)   |
       +-------------------------------------------------------+
```

### Tier 1: Multimodal Audit Canvas (Frontend)
- **Unified Visual Workbench**: Seamless toggle between ReactFlow (for complex system DAGs, AST, logic execution) and tldraw (for screenshots, curation, wireframes, and make-real canvas).
- **Interactive Visual Dropzone**: Supports pasting images, drawing bounding boxes, and adding labels/descriptions.
- **Sidecar Site Inspector**: An iframe side-panel rendering target sites with a CSS selector click listener, pushing the clicked element's selector and outerHTML to Tier 2.

### Tier 2: Reverse Engineering Engine & Crawler (Backend Core)
- **Heuristics Crawler**: A python backend service under `services/dnk_audit/` using `urllib`/`ssl` or headless `Playwright` to extract components.
- **CSS Palette & Vibe Extractor**:
  - Automatically extracts typography (`font-family`, sizes).
  - Normalizes color codes to 6-character hex values and aggregates them into a weighted design token.
- **Vision-to-Code Pipeline**:
  - Offloads screenshots to specialized multimodal vision models (`gemini-2.5-flash` or `gpt-4o`).
  - Infuses prompt templates with our **Molecular Catalog Rules** so that the model automatically structures its output into compliant modular sections.

### Tier 3: Molecular Generator & Sandbox Integrator
- **Molecule Compiler**: Takes the generated code and maps it directly to the structured taxonomy files inside `DNK_HUB/` or `services/dnk_shopify/section_library/molecular_catalog.json`.
- **Live Sync Hook**: Feeds generated modules into the active PostgreSQL/Redis store, triggering immediate refresh in the frontend using the `/ws/canvas_sync` WebSocket.

---

## 4. Immediate Execution Milestones
1. **Milestone 1**: Create the backend folder structure `services/dnk_audit_engine/`.
2. **Milestone 2**: Build an extraction utility `crawler.py` that downloads elements and compiles CSS tokens.
3. **Milestone 3**: Mount tldraw inside the Next.js visual shell as a dedicated visual brainstorming canvas.
4. **Milestone 4**: Integrate the Make Real agent workflow.
