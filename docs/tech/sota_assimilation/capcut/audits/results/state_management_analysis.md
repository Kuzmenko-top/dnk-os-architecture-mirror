<!-- --- DNK-MRH-HEADER ---
mrh_id: "docs/tech/sota_assimilation/capcut/audits/results/state_management_analysis.md"
purpose: "Reverse Engineering Analysis of CapCut AI Design State Management, DI, and Telemetry."
canonical_source: true
alters_files: []
triggers_tasks: []
status: "Completed"
version: "1.0.0"
updated_at: "2026-09-02"
author: "DNK-e.com Maksym (Gerych Prime)"
--- END DNK-MRH-HEADER --->

# 🧠 CapCut AI Design: State Management & Service Architecture

## 1. Executive Summary
The state management of CapCut AI Design does not rely on simple Redux or Pinia stores. Instead, it employs a sophisticated **Dependency Injection (DI) Service Container Architecture** (similar to VS Code / Monaco Editor architecture) embedded within a **React Fiber** component tree and backed by ByteDance's proprietary **TEA (Telemetry & Event Architecture) Visual Editor SDK**.

---

## 2. Core State & Dependency Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 React 18 Component Tree                     │
│               (#csr-root -> #ai-design)                     │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│              InstantiationService / DI Container             │
│   (Service Locator Pattern: EditorService, ToolService...)   │
└──────────────┬──────────────────────────────┬───────────────┘
               │                              │
               ▼                              ▼
┌──────────────────────────────┐ ┌────────────────────────────┐
│      Konva Stage State       │ │    ByteDance TEA SDK       │
│  (Scene Graph Nodes & Attrs) │ │ (Event Tracking & Analytics│
└──────────────────────────────┘ └────────────────────────────┘
```

### Key Components:
1. **`instantiationService`**:
   - Injected into top-level editor components via React Context.
   - Instantiates domain services on-demand: SelectionService, History/UndoRedoService, LayerService, InpaintService, ExportService.
2. **`TEAVisualEditor` & Slardar APM**:
   - `window.TEAVisualEditor`: Centralized event emitter and command dispatcher.
   - `window.ccWebSlardar`: Real-time performance metrics and crash telemetry (`mon-sg.capcutapi.com`).
3. **Workspace & Session Sync**:
   - Multi-tenant space management synced with backend via `https://edit-api-sg.capcut.com/cc/v1/workspace/mget_workspace_info`.

---

## 3. Network Endpoint Schema & API Contracts

| Endpoint Pattern | Method | Purpose |
|------------------|--------|---------|
| `/cc/v1/workspace/mget_workspace_info` | POST | Workspace metadata, user permissions, project index |
| `/cc/v1/workspace/get_all_everphoto_user` | POST | Cloud asset library & user media storage sync |
| `/commerce/v1/subscription/user_info` | GET | User credit balance & tier features validation |
| `/commerce/v1/subscription/workspace/space_list` | GET | Active workspaces, team collaboration quotas |
| `/commerce/v1/resource_position` | GET | AI template categorization & positioning slots |
| `/monitor_web/settings/browser-settings` | GET | Telemetry collector configuration |

---

## 4. Recommendations for DNK OS Architecture

1. **Adopt Service-Oriented DI for Canvas Core**:
   - Structure `CanvasStateEngine` with decoupled services (`SelectionService`, `HistoryService`, `TransformService`, `AISmartToolService`) to prevent monolithic store bloat.
2. **Standardize JSON Scene DTO**:
   - Maintain compatibility between UI canvas nodes and backend Python Pydantic DTOs for AI generative tasks.
