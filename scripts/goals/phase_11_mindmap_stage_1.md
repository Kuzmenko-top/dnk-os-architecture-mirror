<!-- --- DNK-MRH-HEADER ---
mrh_id: "scripts/goals/phase_11_mindmap_stage_1.md"
purpose: "Execution Plan v1.1 for Phase 11 Stage 1 (Mind Map Base Node, 5 Wrappers, Edges & Contract Test)"
canonical_source: true
alters_files: []
triggers_tasks: []
status: "Active"
version: "1.1.0"
updated_at: "2026-09-04"
author: "DNK-e.com Maksym, Antigravity Mentor & Perplexity Mentor"
--- END DNK-MRH-HEADER --- -->

# ЕТАП 11.1: Просторова Карта Думок (Mind Map BaseNode, 5 Wrappers & Edges)

## МЕТА
Впровадити архітектуру просторової карти думок у React Flow Canvas Engine (`apps/web`): базовий компонент `BaseMindMapNode`, 5 спеціалізованих обгорток нод, 3 кастомні зв'язки та контрактну валідацію.

---

# 🎯 СЛАЙС 1.1: Базовий компонент `BaseMindMapNode` та 5 нод Mind Map

## 📌 DIRECTIVE
Створити уніфікований базовий компонент `BaseMindMapNode.tsx`, 5 тонких обгорток нод для карти думок та зареєструвати їх у `apps/web/components/canvas/NodeRegistry.ts`. ВИКОНУЙ НЕГАЙНО.

## 🔒 PRECONDITIONS
- Repository root: `./`
- Branch: `feature/dnk-studio-arch-001`
- Existing store API: використовувати виключно `useCanvasStore.getState().updateNodeData(id, patch)`
- Allowed scope: перелічені нижче 7 файлів
- Forbidden: git commit, push, зміни файлів поза scope
- Execution Budget: 25 tool calls (read: 6, write: 8, verif: 3)

## 📁 TARGET FILES
- [NEW] `apps/web/components/canvas/nodes/BaseMindMapNode.tsx`
- [NEW] `apps/web/components/canvas/nodes/MindMapIdeaNode.tsx`
- [NEW] `apps/web/components/canvas/nodes/MindMapGoalNode.tsx`
- [NEW] `apps/web/components/canvas/nodes/MindMapTaskNode.tsx`
- [NEW] `apps/web/components/canvas/nodes/MindMapAgentNode.tsx`
- [NEW] `apps/web/components/canvas/nodes/MindMapEvidenceNode.tsx`
- [MODIFY] `apps/web/components/canvas/NodeRegistry.ts`

## 📋 REQUIREMENTS
1. **`BaseMindMapNode.tsx`**:
   - 4-Way Handles (`Top`, `Bottom`, `Left`, `Right`) зі свіченням і підтримкою підключення.
   - Шаблон Glassmorphism-картки з підтримкою колірних тем (`amber`, `emerald`, `blue`, `orange`, `purple`).
   - Клас `nodrag` на всіх полях вводу, кнопках і чекбоксах.
   - Inline Title & Description редагування з авто-збереженням через `useCanvasStore.getState().updateNodeData(id, patch)`.
2. **5 тонких обгорток нод**:
   - `MindMapIdeaNode`: теги, рейтинг впевненості (зірочки 1-5).
   - `MindMapGoalNode`: дедлайн, прогрес виконання, KPIs.
   - `MindMapTaskNode`: статус (todo/in_progress/done), виконавець, пріоритет.
   - `MindMapAgentNode`: вибір агента, живий статус, кнопка Run (виклик `triggerNodeAgent`).
   - `MindMapEvidenceNode`: тип артефакту, посилання, кнопка відкриття.
3. **`NodeRegistry.ts`**: експорт метаданих для нових нод.

## 🧪 VERIFICATION
```bash
npx --prefix apps/web tsc --project apps/web/tsconfig.json --noEmit
```

## ✅ DoD (Критерії успіху)
- ✅ `BaseMindMapNode.tsx` та всі 5 нод створено без дублювання коду
- ✅ `NodeRegistry.ts` експортує метадані для всіх 5 нод
- ✅ `npx --prefix apps/web tsc --noEmit` повертає exit code 0
- ✅ Відсутні mock-заглушки чи TODO

## 🛑 BLOCKED RULE
Якщо вимога суперечить існуючому коду `canvasStore.ts`, зупинись і поверни `BLOCKED` з доказом.

## 📤 REQUIRED REPORT
Поверни YAML-звіт із полями: `status`, `files_changed`, `verification`, `tests`, `assumptions`, `remaining_risks`.

---

# 🎯 СЛАЙС 1.2: Кастомні зв'язки (Custom React Flow Edges) та реєстрація

## 📌 DIRECTIVE
Створити 3 кастомні компоненти ребер зв'язку та зареєструвати ноди й еджі у `apps/web/components/canvas/CanvasEngine.tsx`. ВИКОНУЙ НЕГАЙНО.

## 🔒 PRECONDITIONS
- Слайс 1.1 успішно верифіковано
- Allowed scope: перелічені 4 файли
- Execution Budget: 20 tool calls (read: 4, write: 5, verif: 3)

## 📁 TARGET FILES
- [NEW] `apps/web/components/canvas/edges/DependencyEdge.tsx`
- [NEW] `apps/web/components/canvas/edges/RelationEdge.tsx`
- [NEW] `apps/web/components/canvas/edges/MilestoneEdge.tsx`
- [MODIFY] `apps/web/components/canvas/CanvasEngine.tsx`

## 📋 REQUIREMENTS
1. **`DependencyEdge.tsx`**: червона лінія `#ef4444`, `markerEnd: MarkerType.ArrowClosed`, пунктир для заблокованих зв'язків.
2. **`RelationEdge.tsx`**: плавна крива Безьє (`getBezierPath`), лазурний колір `#06b6d4`, товщина 2px.
3. **`MilestoneEdge.tsx`**: фіолетова лінія `#a855f7` з відцентрованим бейджем віхи через `EdgeLabelRenderer`.
4. **`CanvasEngine.tsx`**: імпортувати й зареєструвати у `nodeTypes` 5 нод та у `edgeTypes` 3 еджі.

## 🧪 VERIFICATION
```bash
npx --prefix apps/web tsc --project apps/web/tsconfig.json --noEmit
```

## ✅ DoD (Критерії успіху)
- ✅ 3 файли еджів створено
- ✅ `nodeTypes` та `edgeTypes` оновлено в `CanvasEngine.tsx`
- ✅ `npx --prefix apps/web tsc --noEmit` повертає exit code 0

## 🛑 BLOCKED RULE
Якщо виникає конфлікт версій React Flow або імпортів, зупинись і поверни `BLOCKED`.

## 📤 REQUIRED REPORT
Поверни YAML-звіт із полями: `status`, `files_changed`, `verification`, `tests`, `assumptions`, `remaining_risks`.

---

# 🎯 СЛАЙС 1.3: Швидкий тулбар спавну та Contract/Integration Тести

## 📌 DIRECTIVE
Додати кнопки швидкого спавну Mind Map нод у `StitchSpatialToolbar.tsx`, створити контрактний тест `test_mindmap_nodes_edges_contract.py` та верифікувати якість системи.

## 🔒 PRECONDITIONS
- Слайси 1.1 та 1.2 успішно верифіковано
- Execution Budget: 20 tool calls
- Allowed scope: перелічені 2 файли

## 📁 TARGET FILES
- [MODIFY] `apps/web/components/canvas/StitchSpatialToolbar.tsx`
- [NEW] `tests/canvas/test_mindmap_nodes_edges_contract.py`

## 📋 REQUIREMENTS
1. **`StitchSpatialToolbar.tsx`**: додати кнопки додавання Mind Map нод (💡 Ідея, 🎯 Ціль, ✅ Задача, 🤖 Агент, 📎 Ресурс) з викликом `addNode`.
2. **`test_mindmap_nodes_edges_contract.py`**: перевірити наявність усіх нових файлів, коректність експортів, реєстрацію в `NodeRegistry` та `CanvasEngine`.
3. Запустити `scripts/verify_all.sh` для підтвердження цілісності репозиторію.

## 🧪 VERIFICATION
```bash
uv run pytest tests/canvas/test_mindmap_nodes_edges_contract.py && bash scripts/verify_all.sh
```

## ✅ DoD (Критерії успіху)
- ✅ Тулбар підтримує додавання нових нод
- ✅ Контрактні тести проходять (100% Green)
- ✅ Master Quality Gate зелений

## 📤 REQUIRED REPORT
Поверни YAML-звіт із полями: `status`, `files_changed`, `verification`, `tests`, `assumptions`, `remaining_risks`.
