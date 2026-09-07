<!--
# --- DNK-MRH-HEADER ---
# mrh_id: "docs/plans/PLAN-20260903-001_canvas_live_compiler.plan.md"
# purpose: "Self-Contained Execution Plan for Gerych Swarm: Canvas Live Visual-to-Code Synthesizer."
# canonical_source: true
# alters_files: [
#   "services/dnk_canvas_api/compiler/visual_to_code_synthesizer.py",
#   "services/dnk_canvas_api/main.py",
#   "services/dnk_canvas_api/tests/test_visual_to_code.py",
#   "visual_shell/open_design/apps/web/src/components/stitch/StitchSmartInspector.tsx"
# ]
# triggers_tasks: ["TASK-CANVAS-LIVE-COMPILER"]
# status: "Approved"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "Antigravity (Mentor & Chief Architect)"
# --- END DNK-MRH-HEADER ---
-->

# 📋 Gerych Swarm Mission Order: Live Visual-to-Code Synthesizer

> **Target Worktree**: `.worktrees/task-canvas-live-compiler`  
> **Primary Worker**: `gerych_builder` (Chief Builder)  
> **Supporting Workers**: `dnk_dev_fullstack`, `gerych_auditor`  
> **Invariant**: Relative paths only (`./`, `../`). Anti-Tamper Guard is active (do not modify existing tests).

---

## 🎯 Objective
Implement the bidirectional **Visual-to-Code Synthesizer** in `services/dnk_canvas_api` and connect it to the Live Code tab in `StitchSmartInspector.tsx` within Visual Shell.

---

## 🛠️ Step-by-Step Task DAG

### Step 1: Implement the Synthesizer Engine
**File**: `services/dnk_canvas_api/compiler/visual_to_code_synthesizer.py`
- Implement class `VisualToCodeSynthesizer`.
- Method `synthesize_react(elements: List[Dict[str, Any]], component_name: str = "DnkCanvasComponent") -> str`.
- Support element types:
  - `container` / `rectangle` / `frame` ➔ semantic `<div>` or `<section>` with Tailwind styling.
  - `text` / `heading` ➔ `<h1>`, `<h2>`, `<p>` with appropriate fonts, weights, and colors.
  - `button` / `action` ➔ `<button>` with hover effects and transitions.
  - `image` / `media` ➔ `<img>` or responsive media placeholder.
- Return clean, unescaped React functional component string formatted with JSX.

### Step 2: Implement Unit Tests
**File**: `services/dnk_canvas_api/tests/test_visual_to_code.py`
- Write comprehensive tests:
  - `test_synthesize_empty_scene()`
  - `test_synthesize_hero_section()`
  - `test_synthesize_button_and_cards()`
  - `test_synthesizer_latency_under_threshold()`
- Execute: `pytest services/dnk_canvas_api/tests/test_visual_to_code.py`

### Step 3: Register API Route in FastAPI
**File**: `services/dnk_canvas_api/main.py`
- Add router or endpoint:
  ```python
  @app.post("/api/v1/canvas/synthesize", response_model=CanvasSynthesizeResponse)
  async def synthesize_canvas_to_code(payload: CanvasSynthesizeRequest): ...
  ```
- Calculate execution duration in milliseconds.
- Return synthesized code.

### Step 4: Add Live Code Tab to Visual Shell Inspector
**File**: `visual_shell/open_design/apps/web/src/components/stitch/StitchSmartInspector.tsx`
- Add tab `'code'` to navigation (`tokens | wcag | stitch_dag | code | export`).
- When `'code'` tab is active, trigger fetch to `/api/v1/canvas/synthesize` with current element/scene.
- Render syntax-highlighted code block with line numbers.
- Add "📋 Copy TSX" button with copy feedback toast.

### Step 5: Verification & Gate Audit
- Run unit tests: `pytest services/dnk_canvas_api/tests/test_visual_to_code.py`.
- Run adversarial review check: `scripts/system/gerych_swarm.sh --adversarial-review`.
- Report evidence to Antigravity.
