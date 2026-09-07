---
id: flower_dnk_canvas_003_research_workflow_mvp
title: "🌸 Квітка: DNK-CANVAS-003 Research Workflow MVP"
type: task_flower
plant_scale: flower
parent_id: bush_5_atom_canvas_Molecules
status: completed
verification_status: verified
tags:
  - dnk-task-forest
  - dnk-task-flower
  - canvas
  - research-workflow
---

# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tasks/05_Flowers/Flower_DNK_CANVAS_003_Research_Workflow_MVP.md"
# purpose: "Task Flower tracking DNK-CANVAS-003 Research Workflow MVP (Competitor -> Evidence -> Canvas Element -> Insight -> Flower Draft)."
# canonical_source: true
# alters_files:
#   - "services/dnk_canvas_api/main.py"
#   - "services/dnk_canvas_api/alembic/versions/3c4d5e6f7a8b_canvas_research_workflow.py"
#   - "visual_shell/open_design/apps/web/src/features/canvas/ResearchSidebar.tsx"
#   - "visual_shell/open_design/apps/web/src/features/canvas/canvas.types.ts"
#   - "visual_shell/open_design/apps/web/src/features/canvas/index.ts"
#   - "tests/verification/test_canvas_research_workflow_e2e.py"
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-22"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# plant_scale: "flower"
# --- END DNK-MRH-HEADER ---

# 🌸 Квітка: DNK-CANVAS-003 Research Workflow MVP

## Task Overview
Implement the end-to-end research workflow from competitor profile creation, evidence screenshot metadata registration, element-level asset linking, proposed insight creation, to Task Flower drafting.

## Scope & Implementation Details
1. **Competitor Models & REST Endpoints**: `CanvasCompetitor` ORM model & API routes in `main.py`.
2. **Evidence Screenshot Metadata**: `CanvasEvidence` ORM model & SHA-256 deduplication.
3. **Asset Linking**: `POST /api/v1/canvases/{canvas_id}/elements/{element_id}/evidence`.
4. **Insight & Flower Generation**: `CanvasInsight` (status `proposed`), `FlowerDraft` (status `draft`).
5. **Agent Self-Approval Prevention**: 403 Forbidden on `X-Actor-Type: agent`.
6. **Frontend UI**: `ResearchSidebar.tsx` Next.js component.
7. **Automated E2E Verification**: `tests/verification/test_canvas_research_workflow_e2e.py`.
