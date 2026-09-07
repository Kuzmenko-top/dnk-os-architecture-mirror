<!--
# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/specs/DNK-SPEC-CANVAS-001_live_visual_to_code_compiler.md"
# purpose: "Architecture Specification & API Contract for Canvas Live Visual-to-Code Synthesizer."
# canonical_source: true
# alters_files: [
#   "services/dnk_canvas_api/compiler/visual_to_code_synthesizer.py",
#   "services/dnk_canvas_api/main.py",
#   "visual_shell/open_design/apps/web/src/components/stitch/StitchSmartInspector.tsx"
# ]
# triggers_tasks: ["TASK-CANVAS-LIVE-COMPILER"]
# status: "Approved"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "Antigravity (Mentor & Chief Architect)"
# --- END DNK-MRH-HEADER ---
-->

# 🏛️ DNK-SPEC-CANVAS-001: Live Visual-to-Code Synthesizer Specification

## 1. Executive Architecture
The **Visual-to-Code Synthesizer** is a deterministic, AST-driven compiler inside `services/dnk_canvas_api` that ingests a visual scene AST (nodes, coordinates, labels, styles, dimensions) and maps it into clean, idiomatic, semantic React TSX with Tailwind CSS v4 styling.

```
┌─────────────────────────────────┐
│ Visual Shell / Stitch Canvas    │
│ (React Zustand State / Scene)   │
└───────────────┬─────────────────┘
                │ HTTP POST /api/v1/canvas/synthesize
                ▼
┌─────────────────────────────────┐
│ services/dnk_canvas_api         │
│ ┌─────────────────────────────┐ │
│ │ VisualToCodeSynthesizer     │ │
│ │ - Node AST Tokenizer        │ │
│ │ - Semantic Layout Mapper    │ │
│ │ - TSX Code Generator        │ │
│ └─────────────────────────────┘ │
└───────────────┬─────────────────┘
                │ Returns: { code, component_name, duration_ms }
                ▼
┌─────────────────────────────────┐
│ StitchSmartInspector.tsx        │
│ Live Code Tab & One-Click Copy  │
└─────────────────────────────────┘
```

---

## 2. Data Contracts & Schemas

### 2.1. Request Schema (Pydantic)
```python
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class CanvasElementDTO(BaseModel):
    id: str
    type: str = Field(default="rectangle", description="rectangle | text | container | button | frame")
    label: Optional[str] = Field(default="Component", description="Human-readable label or content")
    x: float = 0.0
    y: float = 0.0
    width: float = 200.0
    height: float = 100.0
    background_color: Optional[str] = "#0f172a"
    text_color: Optional[str] = "#f8fafc"
    border_color: Optional[str] = "#334155"
    border_radius: Optional[float] = 8.0
    children: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class CanvasSynthesizeRequest(BaseModel):
    project_id: str = "default_project"
    component_name: str = "DnkCanvasGeneratedComponent"
    target_framework: str = Field(default="react_tailwind", description="react_tailwind | shopify_liquid")
    elements: List[CanvasElementDTO] = Field(default_factory=list)
```

### 2.2. Response Schema
```python
class CanvasSynthesizeResponse(BaseModel):
    status: str = "success"
    component_name: str
    target_framework: str
    code: str
    element_count: int
    duration_ms: float
    error: Optional[str] = None
```

---

## 3. Component Hierarchy & Synthesizer Rules
The synthesizer sorts elements spatially (top-to-bottom, left-to-right) and maps them into semantic JSX tags:
1. **Container / Screen Elements**: Mapped to `<section className="relative w-full max-w-7xl mx-auto p-6 ...">`.
2. **Hero / Title Elements**: Mapped to `<h1 className="text-3xl font-bold tracking-tight text-white ...">` with sub-paragraphs.
3. **Action / Button Elements**: Mapped to `<button className="px-5 py-2.5 rounded-lg font-medium bg-cyan-500 hover:bg-cyan-400 text-slate-950 transition-all ...">`.
4. **Card / Grid Elements**: Mapped to `<div className="grid grid-cols-1 md:grid-cols-3 gap-6 ...">`.

---

## 4. Frontend Integration (`StitchSmartInspector.tsx`)
1. Add `'code'` to `activeTab` state:
   ```typescript
   const [activeTab, setActiveTab] = useState<'tokens' | 'wcag' | 'stitch_dag' | 'export' | 'code'>('tokens');
   ```
2. Fetch synthesized code whenever the `'code'` tab is selected or when `selectedElement` changes:
   - Call `POST /api/v1/canvas/synthesize` with the active scene or selected node.
   - Render code inside a dark terminal container with syntax highlighting and a "📋 Copy TSX" button.
