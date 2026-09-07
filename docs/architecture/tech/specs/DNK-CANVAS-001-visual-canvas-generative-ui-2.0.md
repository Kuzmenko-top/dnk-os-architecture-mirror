# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/specs/DNK-CANVAS-001-visual-canvas-generative-ui-2.0.md"
# purpose: "Technical Specification & TaskDNA Architecture for Visual Canvas & Generative UI 2.0 (Interactive Infinite Workspace, Node Component Registry, A2A Collaboration & SCONES L3 Integration)"
# canonical_source: true
# alters_files: []
# triggers_tasks: ["DNK-CANVAS-001"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 🎨 DNK-CANVAS-001: Visual Canvas & Generative UI 2.0 MVP

## 1. Executive Summary & Vision
Visual Canvas & Generative UI 2.0 перетворює робочий простір DNK OS на нескінченне інтерактивне середовище (Infinite Canvas) для прямого візуального керування 14 ройовими агентами, динамічними документами, кодом, чатами та аналітичними потоками даних у реальному часі.

Система поєднує:
1. **Infinite Canvas Engine**: Високопродуктивний рушій нескінченного полотна (Pan/Zoom, Viewport culling, OCC).
2. **Node Component Registry**: Модульний реєстр нод (`agent`, `document`, `code`, `chat`, `data`).
3. **Edge Flow Engine**: Рендеринг типізованих зв'язків (`data_flow`, `control_flow`, `reference`) з анімацією передачі сигналів.
4. **Real-Time Collaboration Engine**: Синхронізація курсорів, виділень та стану через WebSockets/A2A Protocol.
5. **SCONES L3 Memory Persistence**: Збереження snapshot'ів полотна та автоматичне відновлення структури через семантичні вектори.

---

## 2. Core Data Contracts (TypeScript & Python)

### 2.1. Canvas Node & Edge Specification
```typescript
export type NodeType = 'agent' | 'document' | 'code' | 'chat' | 'data';
export type EdgeType = 'data_flow' | 'control_flow' | 'reference';

export interface CanvasNodeData {
  title: string;
  type: NodeType;
  content?: any;
  status?: 'idle' | 'running' | 'error' | 'success';
  agent_id?: string;
  file_path?: string;
  metadata?: Record<string, any>;
}

export interface CanvasNode {
  id: string;
  type: NodeType;
  position: { x: number; y: number };
  size?: { width: number; height: number };
  data: CanvasNodeData;
}

export interface CanvasEdge {
  id: string;
  source: string;
  target: string;
  type: EdgeType;
  animated?: boolean;
  label?: string;
  metadata?: Record<string, any>;
}

export interface VisualCanvasState {
  workspace_id: string;
  canvas_id: string;
  nodes: CanvasNode[];
  edges: CanvasEdge[];
  viewport: { x: number; y: number; zoom: number };
  updated_at: string;
}
```

---

## 3. 4-Week Implementation Breakdown

### 🗓️ Тиждень 1: Infinite Canvas Engine & State Management
- Інтеграція Canvas Engine у Next.js (`apps/web/components/canvas/`).
- Реалізація Pan/Zoom, Grid, MiniMap та панелі керування інструментами.
- Тестування рендерингу базових нод та переміщення.

### 🗓️ Тиждень 2: Node Component Registry & Edge Flow Engine
- Розробка кастомних карток нод:
  - `AgentNode`: Індикатор статусу агента, поточні задачі, A2A комунікації.
  - `DocumentNode` / `CodeNode`: Синтаксичний рендеринг, inline-редактор.
  - `DataNode`: Метрики, графіки, потокові дані.
- Custom Animated Edges з візуалізацією потоків даних між агентами.

### 🗓️ Тиждень 3: Real-Time Collaboration & WebSocket Sync
- Інтеграція WebSocket роутера (`apps/api/routers/canvas_ws.py`).
- Оптимістичне блокування (OCC) та розв'язання конфліктів одночасного редагування.
- Відображення мульти-юзер курсорів і статусів активності.

### 🗓️ Тиждень 4: SCONES L3 Memory Persistence & Generative UI 2.0
- Експорт/імпорт стану канвасу у PostgreSQL/SCONES L3 (`scones_canvas_snapshots`).
- AI Auto-Layout: Автоматичне генерування графу нод на основі запиту користувача через Generative UI Engine.
- Фінальний аудит через Master Quality Gate (100% Green, ASR 0.0%).

---

## 4. Verification & Quality Invariants
1. **0 Absolute Paths** (використання виключно відносних шляхів).
2. **0 Dependency Bloat**: Чиста архітектура компонентів.
3. **100% Test Pass Rate** на кожному етапі.
