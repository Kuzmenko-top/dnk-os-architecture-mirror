# --- DNK-MRH-HEADER ---
# mrh_id: "docs/guides/CANVAS_STUDIO_DEVELOPER_GUIDE.md"
# purpose: "Developer Architecture & API Guide for DNK OS Canvas Studio"
# author: "DNK-e.com Maksym"
# license: "MIT"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# --- END DNK-MRH-HEADER ---

# 💻 DNK OS Canvas Studio — Developer Guide

## 1. Codebase Structure

- `apps/web/src/canvas/`:
  - `ai/`: AI adapters (`AIActions`), HTTP clients (`AIClient`, `CanvasAIClient`), and TypeScript DTOs.
  - `history/`: Command pattern (`AddNodeCommand`, `UpdateNodeCommand`, `DeleteNodeCommand`, `BatchCommand`) and `UndoRedoStack` Ring Buffer.
  - `storage/`: Local and IndexedDB persistence engine.
- `apps/web/src/components/canvas/`:
  - `store.ts`: Zustand store managing viewport, layers, selection, and reactive `aiState`.
  - `CanvasToolbar.tsx`: Top bar triggers for generative AI, selection, and canvas manipulation.
  - `AIPromptModal.tsx`: Generative modal with style pills and format presets.
  - `AIProgressToast.tsx`: Progress bar overlay (0-100%).
  - `CanvasStudioLayout.tsx`: Master layout component.
- `services/dnk_canvas_api/`:
  - `main.py`: FastAPI endpoints for Canvas AI (`/api/v1/canvas/ai/*`), WebSocket collaboration.
  - `ai_models.py`: Client classes and DTOs for BiRefNet, IC-Light, and FLUX.1.
- `tests/canvas/`:
  - 74+ pytest unit and integration tests for Canvas API, models, and execution DAGs.

---

## 2. Running Tests

```bash
# Frontend Unit & E2E Tests (25 tests)
cd apps/web && npx tsx --test src/canvas/history/history.test.ts src/canvas/ai/ai-actions.test.ts src/components/canvas/canvas-ui.test.ts src/components/canvas/canvas-e2e.test.ts

# Backend API & AI Integration Tests (74 tests)
.venv/bin/pytest tests/canvas/ -v

# Docker Deployment Verification Tests (2 tests)
.venv/bin/pytest tests/deployment/test_canvas_deployment.py -v
```
