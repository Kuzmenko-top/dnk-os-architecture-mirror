---
title: "009 Task Forest Spatial HQ - 5-Scale LOD Navigation & Time-Travel Engine"
tags:
  - task-forest
  - spatial-canvas
  - lod-scaling
  - time-travel
  - swarm-orchestration
  - architecture
created_at: 2026-09-04
status: Active
author: Maksym Kuzmenko & Gerych Prime
---

<!-- --- DNK-MRH-HEADER ---
mrh_id: "docs_obsidian_009_task_forest_spatial_hq"
purpose: "Comprehensive Architectural Specification & Protocol for Task Forest Spatial HQ (5-Plant Scale LOD Navigation & Evolution Time-Travel Engine)"
canonical_source: true
alters_files: []
triggers_tasks: []
status: "Active"
version: "1.0.0"
updated_at: "2026-09-04"
author: "DNK-e.com Maksym & Gerych Prime"
license: "DNK-INTERNAL"
--- END DNK-MRH-HEADER -->

# 🌲 009 Task Forest Spatial HQ: 5-Scale LOD Navigation & Time-Travel Engine

## 📌 Огляд Архітектури (Executive Overview)
**Task Forest Spatial HQ** є ключовим просторовим ядром системи оркестрації задач DNK OS (Етап 11.4). Вона перетворює плоскі переліки завдань на живородну, ієрархічну біо-екосистему з 5 масштабів:
$$ \text{Field} \longrightarrow \text{Sector} \longrightarrow \text{Tree} \longrightarrow \text{Bush} \longrightarrow \text{Flower} $$

Система безшовно інтегрує просторове масштабування деталей (**LOD — Level of Detail**) на React Flow полотні зі збереженням журналізації мутацій стану (**Time-Travel State Engine**).

Споріднені документи в базі знань:
- [[000 DNK HUB Index]]
- [[001 Obsidian & DNK OS Documentation Standard]]
- [[002 DNK OS - Master System Architecture & Implementation Blueprint]]
- [[004 Gerych Task Specification Standard & Zero-Waste Protocol v2.5]]
- [[007 Obsidian Vault Bidirectional Canvas Sync Protocol]]
- [[008 Archify Spatial Diagram Engine - Autonomous Architecture & Workflow Assimilation Protocol]]

---

## 🧬 1. Таксономія 5 Біологічних Масштабів (Plant Scales)

| Масштаб | Біологічний аналог | Семантичний рівень у DNK OS | Приклад сутності |
|---|---|---|---|
| **Field** (🌾) | Поле / Екосистема | Стратегічний домен / Master Workspace | `DNK_HUB Master HQ` (88%–100%) |
| **Sector** (🏞️) | Сектор / Квартал | Велика підсистема / Сервісний блок | `AI Agent Orchestrator & Studio` |
| **Tree** (🌳) | Дерево / Гілка | Епік / Архітектурний модуль | `TASK-STUDIO-RELEASE-001` |
| **Bush** (🌿) | Кущ / Пагін | Функціональний підмодуль / Slice | `Task Forest Spatial LOD HQ` |
| **Flower** (🌸) | Квітка / Брунька | Атомарний таск / Одиниця коду | `LOD Spatial Node Component` |

---

## 🔍 2. Просторове LOD Масштабування (Level of Detail Zoom)

Компонент `apps/web/components/canvas/nodes/TaskForestSpatialNode.tsx` автоматично зчитує вектор масштабування полотна через хук `useViewport()` бібліотеки `@xyflow/react` і динамічно трансформує свій візуальний вигляд у 3 режими:

```
                  ┌────────────────────────────────────────────────────────┐
                  │                 React Flow useViewport()                │
                  └───────────────────────────┬────────────────────────────┘
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    ▼                         ▼                         ▼
            Zoom < 0.55x             0.55x ≤ Zoom < 1.8x           Zoom ≥ 1.8x
         🌾 Macro Heatmap            🌳 Meso Structural        🌸 Micro Execution
       (Domain Overview & KPI)     (Branches, Trees & Agents) (Code Diffs & Mutations)
```

### 🌾 Zoom < 0.55x — Macro LOD (Spatial Heatmap Card)
- **Призначення**: Огляд домену з висоти пташиного польоту (Field & Sector).
- **Візуалізація**: Компактна теплова картка без перевантаження деталями.
- **Елементи**:
  - Агрегований відсоток готовності (напр., `88% 🟢`).
  - Радіальний бейдж статусу та колірний градієнт.
  - Лічильники підлеглих сутностей: `🌳 N Trees`, `🌿 N Bushes`, `🌸 N Flowers`.

### 🌳 0.55x ≤ Zoom < 1.8x — Meso LOD (Structural Hierarchy Card)
- **Призначення**: Навігація архітектурою підсистем та епіків (Tree & Bush).
- **Візуалізація**: Структурна картка середньої щільності.
- **Елементи**:
  - Індикатор масштабу (`tree` / `bush`).
  - Бейдж відповідального агента (`assigned_agent: gerych_builder`).
  - Прогрес-бар виконання гілки з числовим відсотком.
  - Ідентифікатор вузла та контекст батьківської гілки.

### 🌸 Zoom ≥ 1.8x — Micro LOD (Deep Execution & Diff Inspection)
- **Призначення**: Безпосередня інспекція атомарних тасків (Flower).
- **Візуалізація**: Повноцінна картка розробника з інтерактивними елементами.
- **Елементи**:
  - **Git Diff Viewer**: Підсвічування коду та уніфікований дифф (`+` / `-`).
  - **DTO Contract**: JSON-схема вхідних та вихідних параметрів.
  - **Acceptance Criteria**: Інтерактивний чекліст критеріїв прийомки.
  - **Atomic Mutations**: Швидкі кнопки перемикання станів: `Todo ➔ In Progress ➔ Completed` з миттєвим викликом POST `/api/v3/task_forest/node/mutate`.

---

## ⏱️ 3. Time-Travel Scrubber Rail (Мутаційний Таймлайн)

Віджет `apps/web/components/canvas/TimeTravelRail.tsx` закріплений у нижній частині полотна і безперервно синхронізується з `/api/v3/task_forest/evolution_history`.

### Функціональні можливості:
1. **Інспекція кроків $T_k$**: Переміщення повзунка (Scrubber Slider) дозволяє переглянути стан екосистеми на будь-якому історичному етапі еволюції.
2. **Visual Mutation Pulse**: При виборі події, вузол на полотні, який зазнав змін, отримує динамічний бурштиновий пульс (`amber pulse highlight`), акцентуючи увагу оператора.
3. **Replay Auto-Play**: Режим автоматичного відтворення історії подій з можливістю паузи (`Play / Pause`).
4. **Return to Live Head**: Кнопка миттєвого повернення до актуального (Live) стану системи з очищенням підсвічування та оновленням графу.

---

## 🔄 4. Bottom-Up Каскадний Перерахунок Прогресу

Коли будь-який листовий вузол (Flower) змінює свій статус або прогрес, бекенд-роутер `apps/api/routers/task_forest_router.py` виконує каскадний перерахунок знизу-вгору:
$$ \text{Progress}(\text{Node}) = \frac{1}{N} \sum_{i=1}^{N} \text{Progress}(\text{Child}_i) $$
1. Перераховується батьківський **Bush**.
2. Перераховується батьківське **Tree**.
3. Перераховується батьківський **Sector**.
4. Оновлюється підсумковий прогрес стратегічного **Field**.
5. Кожна зміна фіксується як атомарний знімок в журналі `STATE_EVOLUTION_LOG`.

---

## 🧪 5. Верифікація та Інтеграційні Тести

Система покрита повним набором автоматизованих тестів:
- `tests/verification/test_task_forest_spatial_router.py`:
  - `test_get_task_forest_graph` (100% 🟢)
  - `test_node_mutation_and_bottom_up_rollup` (100% 🟢)
  - `test_add_new_node` (100% 🟢)
  - `test_evolution_history` (100% 🟢)
- `tests/verification/test_task_forest_spatial_ui.py`:
  - `test_task_forest_spatial_graph_endpoint` (100% 🟢)
  - `test_task_forest_evolution_history_endpoint` (100% 🟢)
  - `test_task_forest_node_mutation_cascade` (100% 🟢)
  - `test_spatial_component_files_exist` (100% 🟢)

Загальний результат верифікації: **8/8 тестів пройдено на 100% 🟢**.
