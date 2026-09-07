---
title: "023 NodeTask Cabinet Architecture and Improvement Roadmap"
tags:
  - nodetask
  - cabinet
  - architecture
  - roadmap
  - dag
date: 2026-09-05
status: Active
version: 1.1.0
---

<!-- --- DNK-MRH-HEADER ---
mrh_id: "docs/notes/023 NodeTask Cabinet Architecture and Improvement Roadmap.md"
purpose: "Comprehensive Architecture and Improvement Roadmap for DNK OS NodeTask DAG Cabinet"
canonical_source: true
alters_files: []
triggers_tasks: []
status: "Active"
version: "1.1.0"
updated_at: "2026-09-05"
author: "DNK-e.com Maksym & Gerych Prime"
--- END DNK-MRH-HEADER -->

# 🗺️ 023 NodeTask Cabinet Architecture and Improvement Roadmap

## 1. Контекст та Мета
Візуальний кабінет завдань та ідей (`/tasks`) у стилі **CapCut LUI & Google Stitch Minimalist Canvas** реалізує оркестрацію завдань рою DNK OS через граф орієнтованих зв'язків (DAG). Для виходу платформи на промисловий рівень надійності та щоденного комфортного використання реалізовано покроковий план поліпшень відповідно до протоколу **MASE (Mandatory Atomic Slice Execution)**.

---

## 2. Реалізовані Архітектурні Слайси

### ✅ Слайс 1: Інфраструктурна оптимізація кешування Dockerfile.frontend
- **Файл**: `Dockerfile.frontend`
- **Рішення**: Інтегровано Docker BuildKit cache mounts:
  - `--mount=type=cache,target=/root/.npm` на етапі встановлення залежностей `deps`.
  - `--mount=type=cache,target=/app/.next/cache` на етапі збирання додатку `builder`.
- **Результат**: Зниження часу повторних білдів сторінок Next.js з ~90с до 10–15с.

### ✅ Слайс 2: Drag-to-Connect Handles & Cycle Prevention у ReactFlow
- **Файли**: `apps/web/components/node-tasks/NodeTaskGraphCanvas.tsx`, `apps/web/store/nodeTasksStore.ts`, `apps/api/routers/node_tasks_router.py`.
- **Рішення**:
  - Реалізовано клієнтську валідацію `isValidConnection(connection)` у ReactFlow: блокування з'єднання ноди з самою собою (`source === target`) та пре-чек транзитивних циклів (якщо від `target` вже існує шлях до `source`, з'єднання відхиляється до надсилання на сервер).
  - Уніфіковано моделі: `CreateEdgeRequest` тепер приймає як `relation`, так і `dependency_type` через Pydantic validator, запобігаючи скиданню типів зв'язків.
  - Додано неоновий Toast-банер у стилі CapCut/Stitch (зелений з `CheckCircle2` для успіху, червоний з `XCircle` для помилок/циклів) із автоматичним згасанням через 4 секунди.

### ✅ Слайс 3: Автономна декомпозиція Епіків через Герича (AI Epic Decomposition)
- **Файли**:
  - `services/dnk_node_tasks/conversational_intake.py`: метод `ConversationalTaskExtractor.decompose_node(...)`.
  - `apps/api/routers/node_tasks_router.py`: ендпоінт `POST /api/v3/node_tasks/{node_id}/decompose`.
  - `apps/web/store/nodeTasksStore.ts`: дія `decomposeNode(nodeId, instructions)`.
  - `apps/web/components/node-tasks/NodeTaskDetailDrawer.tsx`: кнопка «⚡ Декомпозувати через Герича».
- **Логіка ройового розбиття**:
  - Аналізує контекст ноди (заголовок, опис, теги).
  - Створює 3 спеціалізовані підзадачі:
    1. **Arch & Spec** (архітектура та контракти) ➔ `antigravity_mentor`.
    2. **Build / Implementation** (код та верстка) ➔ `gerych_builder` / `dnk_dev_fullstack` / `dnk_shopify` / `dnk_video_ai_creator`.
    3. **Gate & Audit** (тести та регресії) ➔ `gerych_auditor`.
  - Розставляє ноди на полотні праворуч від батьківської та формує послідовні залежності `depends_on`.
  - Автоматично зберігає граф та оновлює Markdown-файли в Obsidian (`docs/notes/tasks_and_ideas/`).

### ✅ Слайс 4: Тестування та Верифікація 100% Green
- **Бекенд (Pytest)**:
  - Додано тест `test_decompose_node()` у `tests/verification/test_node_tasks_router.py`.
  - Загальний результат: **14 passed in 5.91s** (100% Green).
- **Фронтенд (TypeScript)**:
  - `npx tsc --noEmit` в `apps/web`: 0 помилок.
- **Live Browser (Browser Use)**:
  - Відкрито сторінку `http://localhost:3000/tasks`.
  - Заголовок: `🐴 🧬 DNK OS (v2.0 Agentic Media & E-Com Operating System)`.
  - Консоль чиста, помилки рендеру відсутні.

### ✅ Слайс 5: Топологічний Auto-Layout DAG (Barycenter Tidy & Batch Persistence)
- **Бекенд (FastAPI)**:
  - Додано модель `BatchPositionsRequest` та ендпоінт `POST /api/v3/node_tasks/batch_positions` у `apps/api/routers/node_tasks_router.py`.
  - Зберігає нові координати всіх або вибраних нод у `node_task_graph.json` одним атомарним викликом.
- **Фронтенд (Zustand & ReactFlow)**:
  - `apps/web/store/nodeTasksStore.ts`: оновлено `autoLayoutDAG` на асинхронний метод із впровадженням евристики Барицентру (мінімізація перетинів ребер шляхом сортування підвузлів за середнім Y їхніх батьківських нод).
  - Горизонтальний крок 380px, вертикальний 220px, пріоритетне ранжування кореневих нод за `priority`.
  - `apps/web/components/node-tasks/NodeTaskGraphCanvas.tsx`: інтегровано кнопку `🪄 Auto-Layout` з іконкою `Wand2`, спінером очікування, автоматичним плавним `fitView` та неоновим тостом зворотного зв'язку.
- **Верифікація**:
  - `test_batch_update_positions()` у `tests/verification/test_node_tasks_router.py` (15 passed, 100% Green).
  - `apps/web/node_modules/.bin/tsc --noEmit -p apps/web/tsconfig.json` (0 помилок, Clean).

### ✅ Слайс 6: Live Swarm Execution, Visual Pulse & Log Terminal
- **Бекенд (FastAPI)**:
  - Додано ring-buffer логів виконання `_task_logs` та ендпоінти:
    - `POST /api/v3/node_tasks/{node_id}/execute`: запуск воркера рою з підтримкою режимів `simulation`, `autonomous_subagent`, `auto_complete` (автозавершення після перевірки).
    - `GET /api/v3/node_tasks/{node_id}/logs`: отримання структурованих подій виконання (`timestamp`, `level`, `agent`, `message`).
- **Фронтенд (Zustand & ReactFlow)**:
  - `CustomTaskNode.tsx`: додано неоновий пульс `shadow-[0_0_25px_rgba(52,211,153,0.35)] ring-2 ring-emerald-400/80 animate-pulse` та живий бейдж з анімацією `animate-ping` для нод зі статусом `in_progress`.
  - `NodeTaskDetailDrawer.tsx`: інтегровано Live Swarm Terminal з підтримкою колірних міток рівнів логів (`STEP`, `INFO`, `SUCCESS`, `ERROR`), кнопкою оновлення та вибором режимів запуску (`Simulation`, `Autonomous Worker`, `Fast Finish & Verify`).
  - `nodeTasksStore.ts`: додано стан `nodeLogs` та дію `fetchNodeLogs(nodeId)`.
- **Верифікація**:
  - `test_execute_node_direct_and_logs()` у `tests/verification/test_node_tasks_router.py` (16 passed in 4.94s, 100% Green).
  - `apps/web/node_modules/.bin/tsc --noEmit -p apps/web/tsconfig.json` (0 помилок, Clean).

### ✅ Слайс 7 (CPM): Critical Path Method & Visual Bottleneck Heatmap
- **Бекенд (FastAPI & Graph Engine)**:
  - Реалізовано алгоритм CPM у `NodeTaskGraphEngine.compute_critical_path`:
    - Розрахунок тривалостей на основі пріоритетів та стадій (Completed = 0h, Critical = 8h, High = 5h тощо).
    - Прямий прохід (Forward Pass): обчислення Early Start (ES) та Early Finish (EF).
    - Зворотний прохід (Backward Pass): обчислення Late Start (LS) та Late Finish (LF).
    - Визначення резерву часу (Float / Slack = LS - ES). Вузли зі Slack ≈ 0 позначаються як критичні.
    - Виділення ланцюжка критичних ребер (Critical Edges) та ранжування вузьких місць (Bottlenecks за кількістю заблокованих задач).
  - Додано ендпоінт `GET /api/v3/node_tasks/critical_path` із підтримкою фільтрації за `project_id`.
- **Фронтенд (Zustand & ReactFlow)**:
  - У `nodeTasksStore.ts`: стан `showCriticalPath`, `criticalPathNodeIds`, `criticalEdgeIds`, `criticalPathTotalDuration`, `criticalPathBottlenecks`, `criticalPathMetrics` та дії `setShowCriticalPath`, `fetchCriticalPath`.
  - У `CustomTaskNode.tsx`: неоновий акцентний ореол `ring-2 ring-rose-500 border-rose-500 shadow-[0_0_24px_rgba(244,63,94,0.45)]`, плашка з тривалістю та резервом часу `CPM: Xh (Slack: Yh)`, приглушення некритичних нод для високого контрасту.
  - У `CustomDependencyEdge.tsx`: підсвічування критичних ребер яскраво-рожевим кольором (`#f43f5e`, `strokeWidth: 3`), ефект світіння та маркер `🔥 CPM`.
  - У `NodeTaskGraphCanvas.tsx`: кнопка перемикання `🔥 Критичний шлях` на панелі інструментів та інформаційний банер аналітики CPM (загальний час, кількість критичних задач, головний блокер).
- **Верифікація**:
  - `test_get_critical_path()` у `tests/verification/test_node_tasks_router.py` та `test_compute_critical_path()` у `tests/core/test_node_task_graph_engine.py` (22 passed, 100% Green).
  - `apps/web/node_modules/.bin/tsc --noEmit -p apps/web/tsconfig.json` (0 помилок, Clean).

### ✅ Слайс 7 (Архів): Canvas Multi-Selection & Batch Operations Dock (Слайс 20.4)
- **Бекенд (FastAPI)**:
  - Додано `POST /api/v3/node_tasks/batch_stage_transition` та `POST /api/v3/node_tasks/batch_delete` у `apps/api/routers/node_tasks_router.py`.
  - Каскадне видалення зв'язків та атомарна перевірка блокувальників перед зміною стадії.
- **Фронтенд (Zustand & ReactFlow)**:
  - `NodeTaskCanvasBatchDock.tsx`: плаваюча док-панель із кнопками масового переведення стадій, видалення та скидання вибору.
  - Покриття тестами `tests/verification/test_node_tasks_batch_operations.py` (19 passed, 100% Green).

### ✅ Слайс 8: Drag Physics, Graph Topology & Barycenter Normalization (Слайс 20.5)
- **Фронтенд (Zustand & ReactFlow)**:
  - Виправлено розрахунок координат у `autoLayoutDAG`: підтримка як `relation`, так і `dependency_type`, впроваджено `STAGE_MIN_DEPTH` для запобігання колапсу нод в одну колонку.
  - Оновлено CSS `CustomTaskNode.tsx`: `cursor-grab active:cursor-grabbing` та плавні переходи без затримки координат миші (`transition-[border-color,box-shadow]`).
  - Додано `POST /api/v3/node_tasks/reset_baseline` для скидання графа до канонічного 7-колонного стану.

### ✅ Слайс 9: Live Execution Terminal & Artifact Diff Inspector (Слайс 20.6)
- **Бекенд (FastAPI)**:
  - Додано моделі `ArtifactFileDiff`, `NodeArtifactReport`, `VerificationResult` у `apps/api/routers/node_tasks_router.py`.
  - Реалізовано ендпоінти: `GET /artifacts`, `POST /accept_artifacts`, `POST /reject_artifacts`, `POST /run_verification`, `POST /logs/clear`.
  - Покриття тестами `tests/verification/test_node_tasks_artifacts.py` (7/7 passed, 100% Green).
- **Фронтенд (Zustand & ReactFlow)**:
  - Вкладки в дровері `[📋 Огляд] | [>_ Live Термінал] | [📄 Diff Артефактів]`.
  - Компонент `NodeTaskArtifactDiffViewer.tsx` із кольоровою підсвіткою змін, лічильником (+/-) та діями верифікації.

### ✅ Слайс 10: Multi-Tenant Project / Workspace Switcher for DAG Canvas (Слайс 21.1)
- **Бекенд (FastAPI)**:
  - Створено сутність `ProjectInfo (id, name, slug, description, color, icon, is_active)` та поле `project_id` у `NodeItem`.
  - Ендпоінти `GET /api/v3/node_tasks/projects`, `POST /api/v3/node_tasks/projects`.
  - Підтримка query-параметра `project_id` у `GET /api/v3/node_tasks/graph` із повною ізоляцією вузлів та зв'язків (edges).
  - Покриття тестами `tests/verification/test_node_tasks_projects.py` (3/3 passed).
- **Фронтенд (Zustand & ReactFlow)**:
  - Компонент `ProjectSwitcherDropdown.tsx` у верхній панелі керування (стиль CapCut/Stitch).
  - Миттєве перемикання проектів в 1 клік (`dnk_core`, `m_craft`, `brand_alpha`, `test_ecom_suite`) та модальне вікно створення нового проекту.
  - Реактивний стан у `nodeTasksStore.ts`: `projects`, `activeProjectId`, `fetchProjects()`, `setActiveProject()`.
- **E2E Верифікація**:
  - Live перевірка в Chrome DevTools на `http://localhost:3000/tasks`: перемикання між проектами ізолює граф вузлів (14 у `dnk_core`, 0 у `m_craft`).

---

### ✅ Слайс 11: 1-Click Grounded Marketing & Remotion 9:16 Video Generator (Слайс 22.1)
- **Бекенд (FastAPI)**:
  - Створено синтезатор маркетингового сценарію `services/dnk_video_ai_creator/task_video_synthesizer.py`.
  - Моделі `MarketingVideoScene`, `MarketingVideoPayload` (4-фазний сторіборд: Hook, Problem, Solution, CTA; 480 кадрів = 16с при 30fps).
  - Ендпоінти `POST /api/v3/node_tasks/{node_id}/generate_marketing_video` та `GET /api/v3/node_tasks/{node_id}/marketing_video`.
  - Покриття тестами `tests/verification/test_node_tasks_video_generator.py` (3/3 passed, 100% Green).
- **Фронтенд (Zustand & React)**:
  - Типи `MarketingVideoScene`, `MarketingVideoPayload` у `apps/web/types/nodeTasks.ts`.
  - Реактивний стан у `apps/web/store/nodeTasksStore.ts`: `marketingVideos`, `isGeneratingVideo`, екшени `fetchMarketingVideo`, `generateMarketingVideo`.
  - Компонент `NodeTaskMarketingVideoViewer.tsx` (9:16 vertical smartphone frame, кінетична типографіка, scrubber, копіювання войсоверу, картки сцен, список артефактів).
  - 4-та вкладка `[🎬 Відео 9:16]` у `NodeTaskDetailDrawer.tsx`.
  - 0 помилок у `tsc --noEmit`.
- **E2E Верифікація**:
  - Live перевірка в Chrome DevTools на `http://localhost:3000/tasks`: синтез сторіборду для задачі `#idea-remotion` на базі артефактів коду, інтерактивний рендеринг у Drawer, перевірено відтворення та скрабінг.

---

### ✅ Слайс 12: Deep Dynamic Obsidian Bidirectional Markdown Sync (Слайс 23.1)
- **Бекенд (FastAPI)**:
  - Створено рушій двосторонньої синхронізації `services/dnk_canvas_api/obsidian_sync_engine.py` (парсинг YAML frontmatter, [[wikilinks]], acceptance criteria, оновлення edges).
  - Ендпоінти `POST /api/v3/node_tasks/sync_from_obsidian` та `POST /api/v3/node_tasks/sync_bidirectional`.
  - Покриття тестами `tests/verification/test_node_tasks_obsidian_sync.py` (4/4 passed, 100% Green).
- **Фронтенд (Zustand & ReactFlow)**:
  - Дія `syncObsidianBidirectional()` у `apps/web/store/nodeTasksStore.ts` з реактивним оновленням графа (`fetchGraph`).
  - Оновлено кнопку `🔄 2-Way Sync` у шапці канвасу (`NodeTaskGraphCanvas.tsx`), замінено `alert` на інформативний тост з переліком оновлених, імпортованих та експортованих нотаток.
  - 0 помилок у `tsc --noEmit`.
- **E2E Верифікація**:
  - Live перевірка в Chrome DevTools на `http://localhost:3000/tasks`: створено Markdown-нотатку `task-obsidian-roundtrip-test.md`, виконано `🔄 2-Way Sync`, вузол імпортовано на канвас, edge до `idea-remotion` побудовано, дані перевірено в Drawer.

---

## 3. Черга Послідовної Реалізації (Sequential Roadmap Queue)

1. **[НАСТУПНИЙ] Слайс 24.1 — Voice AI Live Audio Synthesis & Remotion Video Exporter**:
   - Задача: `TASK-DNK-REMOTION-20260906-010`
   - Підключення ElevenLabs / Whisper для автоматичного озвучення згенерованого `voiceover_script` та рендеринг фінального MP4 відео через Remotion CLI.
2. **Слайс 25.1 — Multi-Agent Parallel Autonomous Delegation & OCC Auto-Reconciliation**:
   - Паралельний запуск кількох агентів у ройовому режимі на різних вузлах графа із запобіганням конфліктам через OCC.

---

## 4. Зв'язки з іншими модулями (Cross-Links)
- [[022 CapCut and Stitch Visual Cabinet with Conversational Gerych Intake]]
- [[020 Node-Based Ideas and Task Cabinet with Obsidian Sync]]
- [[019 Task Forest and Canvas Spatial Architecture]]
- [[docs/plans/my_task/task_20260906_canvas_006_live_terminal_diff_inspector.md]]
- [[docs/plans/my_task/task_20260906_canvas_007_multitenant_project_switcher.md]]
- [[docs/plans/my_task/task_20260906_remotion_008_marketing_video_generator.md]]
- [[docs/plans/my_task/task_20260906_canvas_009_obsidian_bidirectional_sync.md]]


