<!-- --- DNK-MRH-HEADER ---
mrh_id: "docs/architecture/UNIFIED_SPATIAL_CANVAS_SYSTEM_SYNTHESIS.md"
purpose: "Comprehensive System Analysis & Blueprint for Unifying All Dispersed Tools into One Spatial Master Canvas."
canonical_source: true
alters_files: ["apps/web/components/workspace/DNKStudioWorkspace.tsx", "apps/web/store/canvasStore.ts"]
triggers_tasks: ["TaskDNA-UNIFIED-CANVAS-CONVERGENCE"]
status: "Active"
version: "1.0.0"
updated_at: "2026-09-03"
author: "DNK-e.com Maksym & Gerych Prime"
--- END DNK-MRH-HEADER -->

# 🌐 DNK OS: Комплексний аналіз системи та архітектурний план Єдиного Робочого Полотна (Unified Spatial Canvas)

## 📌 1. Вступ та Стратегічна Мета
За попередні етапи розвитку DNK OS було створено потужний арсенал спеціалізованих модулів, вузлів та інтерфейсів (CapCut-подібний Canvas, Excalidraw Whiteboard, Stitch Prompt Dock, Launchpad Onboarding, Shopify AST Generator, Teleprompter Studio, Swarm Task Forest та PostgreSQL 16 Backend). 

Проте зараз ці компоненти функціонують на **розрізнених маршрутах** (`/canvas`, `/whiteboard`, `/teleprompter`, `/taskdna`, `/tasks`, `/launchpad`) та мають локальні або ізольовані стани.

**Головна мета:** Об'єднати всі напрацювання в **Одне Робоче Полотно (Single Working Canvas)** — безшовний просторовий хаб, де стратегія, генерація коду, маркетинг, візуальний дизайн, вільний скетчинг та координація рою агентів відбуваються в одному вікні в реальному часі.

---

## 🏛️ 2. Інвентаризація та Аудит Реалізованих Компонентів

### А. Просторові та Візуальні Інтерфейси (Frontend Layer)
1. **DNKStudioWorkspace (`apps/web/components/workspace/DNKStudioWorkspace.tsx`)**:
   - CapCut-натхненний темний UI (StudioDock, InspectorPanel, TopBar, Dot Grid).
   - *Фрикція:* Використовує локальний `useNodesState`/`useEdgesState` замість глобального реактивного сховища.
2. **ConnectedCanvasEngine & DNKCanvas (`apps/web/components/canvas/`)**:
   - Інтегровані з `useCanvasStore.ts`.
   - Підтримка експорту/імпорту стандартного Obsidian JSON Canvas (`.canvas`).
   - Гарячі клавіші Undo/Redo (`Cmd+Z`, `Cmd+Shift+Z`).
   - Набір із 12+ спеціалізованих типів нод (`StrategyMarkdownNode`, `DesignGalleryNode`, `ShopifyBuilderNode`, `SprintKanbanNode`, `VideoCreatorNode`, `SmartNoteNode`, `LiveWebPreviewNode`).
3. **Whiteboard Editor (`apps/web/components/canvas/WhiteboardEditor.tsx` / `/whiteboard`)**:
   - Інтеграція Excalidraw для ручного креслення та вільного малювання.
   - *Фрикція:* Існує як окрема сторінка, не накладається як шар на основне полотно.
4. **Stitch Co-Pilot & Prompt Dock (`StitchPromptDock.tsx`, `StitchLeftChatPanel.tsx`)**:
   - Док для швидкого введення промптів до Gemini 2.5 / Claude 3.5.
   - Стрімінг думок агента та логів виконання.
5. **Launchpad & Onboarding Wizard (`LaunchpadView.tsx`, `OnboardingWizard.tsx`)**:
   - 4-кроковий генератор Brand DNA (назва, ніша, цілі, палітра кольорів).
   - Бізнес-шаблони: E-Com DTC, UGC Video Funnel, SaaS Growth, Brand Identity.

### Б. Автономні Двигуни та Інтелектуальний Шар (Core & Swarm)
1. **Swarm Reactive Propagation (`swarmPropagation.ts`)**:
   - Автоматичний каскад змін: нода Стратегії оновлює Дизайн -> Дизайн оновлює Liquid AST -> Дизайн створює таски в Kanban.
2. **TaskDNA Engine (`core/taskdna/`)**:
   - Декомпозиція мети користувача на спрямований ациклічний граф (DAG) із призначенням на агентів (`gerych_builder`, `dnk_shopify`, `dnk_video_ai_creator`, `gerych_auditor`).
3. **SCONES Memory Engine (`core/scones/`)**:
   - L1 (Fast Context), L2 (Domain Knowledge), L3 (Vector Workspace Memory) у схемі PostgreSQL `hub_memory`.
4. **Shopify AST & Theme Sync (`services/dnk_shopify`)**:
   - Двосторонній транслятор Liquid AST <-> Canvas Node.
   - Валідація секцій та інжекція в теми Shopify OS 2.0.
5. **Video AI Creator & Teleprompter (`services/dnk_video_ai_creator`, `/teleprompter`)**:
   - Генерація розкадровок, скриптів для рилз/тікток, телесуфлер із таймінгом.

### В. Серверна Інфраструктура (Docker & Backend)
1. **FastAPI Spatial API (`services/dnk_canvas_api`, порт 8000)**:
   - CRUD полотен, ревізій, просторових елементів.
   - Валідація через заголовок `X-Workspace-Id` (UUID).
2. **PostgreSQL 16 (`dnk_canvas`, порт 5432)**:
   - Схема `hub_memory` з підтримкою збереження топології вузлів та історії версій.
3. **Redis 7 (порт 6379)**:
   - Pub/Sub для синхронізації дій користувачів та агентів у реальному часі.

---

## 🎯 3. Концепція Єдиного Робочого Полотна (The Unified Canvas)

Замість перемикання між 6 різними сторінками, ми об'єднуємо всі інструменти в **єдине тривимірне середовище**:

```
+---------------------------------------------------------------------------------------+
|  TOP BAR: [Проєкт: Brand Launch] [Режим: Graph / Sketch / Preview] [AI Model] [Share] |
+-----------+---------------------------------------------------------------+-----------+
| LEFT DOCK |                      ЦЕНТРАЛЬНИЙ КАНВАС                       | RIGHT     |
| (Інструм.)|                                                               | PANEL     |
|           |  [Strategy Node] ----(DataFlow)----> [Design Gallery Node]     |           |
| [⚡ Prompt] |         |                                   |            | [Властив. |
| [📁 Ноди]   |    (ControlFlow)                     (DataFlow)          |  ноди]    |
| [🎨 White- |         v                                   v            |           |
|   board]  |  [Kanban Sprint Node]               [Shopify Liquid Node]    | [AI Co-   |
| [🎬 Video] |                                             |            |  Pilot]   |
| [🛒 Shop]  |                                       (Live Preview)      |           |
|           |                                             v             | [SCONES   |
|           |                                    [Live Preview Node]    |  Пам'ять] |
+-----------+---------------------------------------------------------------+-----------+
| BOTTOM BAR: [Stitch Prompt Dock: "Геричу, згенеруй Hero-секцію..."] [Undo] [Zoom 100%]|
+---------------------------------------------------------------------------------------+
```

---

## 🚀 4. План Дій: 4 Етапи Об'єднання (Actionable Convergence Plan)

### Етап 1: Єдине Джерело Правди (Single State Convergence)
- **Файл:** `apps/web/components/workspace/DNKStudioWorkspace.tsx`
- **Дія:** Підключити `DNKStudioWorkspace` до `useCanvasStore.ts`.
- **Результат:** Коли користувач обирає шаблон на Launchpad або вводить новий Brand DNA в Onboarding Wizard, канвас миттєво відкривається з відповідними нодами, зв'язками та активним станом.

### Етап 2: Режим "Dual-Layer" (Graph + Freehand Whiteboard)
- **Компонент:** `apps/web/components/canvas/WhiteboardOverlay.tsx`
- **Дія:** Інтегрувати Excalidraw як прозорий шар (або спліт-режим) прямо на полотні за гарячою клавішею `W` або перемикачем у лівому тулбарі.
- **Результат:** Можливість малювати стрілки від руки прямо поверх структурованих нод ReactFlow або швидко робити скетчі поряд із кодом.

### Етап 3: Інжекція Stitch Prompt Dock у робоче полотно
- **Компонент:** `apps/web/components/canvas/StitchPromptDock.tsx`
- **Дія:** Закріпити Floating Dock у нижній частині канвасу.
- **Результат:** Користувач вводить запит ("Додай ноду з аналізом конкурентів"), і TaskDNA / Swarm автоматично створює нові ноди та з'єднує їх зв'язками на полотні.

### Етап 4: Пряма синхронізація з PostgreSQL 16 API
- **Клієнт:** `apps/web/src/canvas/storage/storage.service.ts`
- **Дія:** Забезпечити автозбереження стану канвасу через `POST /api/v1/canvases/{id}/revisions` на порті 8000 з автоматичним відновленням при перезавантаженні сторінки.

---

## 🛡️ 5. Відповідність Стандартам Якості та Безпеки
1. **100% Green Quality Gate**: Кожна зміна валідується через `bash scripts/verify_all.sh` (1457 тестів, перевірка шляхів та синтаксису).
2. **Zero Leaks**: Жодних токенів чи паролів у фронтенд-коді. Всі виклики моделей здійснюються через захищений шлюз.
3. **JSON Canvas 1.0 Compliance**: Повне збереження сумісності з форматом Obsidian Canvas для локального володіння даними.
