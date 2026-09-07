---
title: "058 Visual Canvas Control Panel Architecture"
aliases: ["Visual Canvas Control Panel", "TaskDNA Obsidian Canvas Sync", "Swarm Visual Dashboard"]
tags: ["#architecture", "#canvas", "#taskdna", "#swarm", "#obsidian", "#zero-waste"]
version: "1.0.0"
date: "2026-09-06"
status: "Active"
author: "DNK-e.com Maksym & Gerych Prime"
---
<!-- --- DNK-MRH-HEADER ---
mrh_id: "docs/notes/058_Visual_Canvas_Control_Panel_Architecture.md"
purpose: "Architecture specification for Vector 5: Visual Control Panel on Canvas (TaskDNA to Obsidian Canvas sync, HUD, Swarm badges, bi-directional lifecycle)."
canonical_source: true
alters_files: []
triggers_tasks: []
status: "Active"
version: "1.0.0"
updated_at: "2026-09-06"
author: "DNK-e.com Maksym & Gerych Prime"
--- END DNK-MRH-HEADER -->

# 🎛️ 017. Візуальний Пульт Керування на Canvas (TaskDNA ➔ Obsidian Canvas Synchronizer)

## 📌 1. Контекст та Призначення (Vector 5)
У межах комплексної програми прискорення розробки DNK OS реалізовано 5 векторів оптимізації продуктивності:
1. [[013_Zero_Touch_Inception_Gateway_Architecture|Zero-Touch Inception Gateway]] — автотрансляція запитів у TaskDNA.
2. [[028 Anti-Loop and AST Fast-Path Architecture|Anti-Loop Guard & AST Fast-Path]] — захист від циклічного читання та churn.
3. [[015_GitHub_MCP_Fast_Path_and_CI_Evidence_Architecture|GitHub MCP Fast-Path & CI Gate]] — нативний аудит PR без клонування.
4. [[056_Two_Track_SOTA_Repository_Assimilation_Architecture|Two-Track SOTA Repository Assimilation]] — ліцензійний аудит та чисті кімнати.
5. **Візуальний Пульт Керування на Canvas** — інтерактивна двостороння синхронізація DAG-дерев [[009_Task_Forest_and_TaskDNA|TaskDNA]] з форматом полотна **Obsidian Canvas** (`.canvas` JSON).

Пульт перетворює абстрактні задачі терміналу та бекенду на просторову інтерактивну карту в реальному часі, дозволяючи Максиму та ройовим агентам одночасно контролювати прогрес, ризики та використання інструментів.

---

## 🏛️ 2. Архітектура Двигуна (`core/orchestrator/visual_canvas_control.py`)

```
 ┌─────────────────────────────────────────────────────────────┐
 │                TaskDNA DAG / TaskForest                    │
 │  (id, stage, dependencies, assigned_agent, budget, risk)    │
 └──────────────────────────────┬──────────────────────────────┘
                                │
                                ▼
 ┌─────────────────────────────────────────────────────────────┐
 │           VisualCanvasControlEngine (Core Synchronizer)    │
 ├─────────────────────────────────────────────────────────────┤
 │ 1. Topological Layout Engine (depth columns & level rows)   │
 │ 2. Markdown Card Styler (Badges, Checkboxes, Risk, MASE)    │
 │ 3. Swarm Status HUD Generator (Summary Metrics & Progress)   │
 │ 4. Dynamic Grouping (Phases & Execution Stages)             │
 │ 5. Bi-directional Conflict Resolver (Spatial preservation)   │
 └──────────────────────────────┬──────────────────────────────┘
                                │
                                ▼
 ┌─────────────────────────────────────────────────────────────┐
 │              Obsidian Canvas (.canvas JSON)                 │
 │  - control_panel_hud (HUD Status Card: 📈 Progress, Gate)   │
 │  - Stage Groups (Backlog, Parallel Swarm, Quality Gate)     │
 │  - Task Nodes (Color 1..6, Checklist, Swarm Agent Badges)  │
 │  - Directional Edges (depends_on, green if dep completed)   │
 └─────────────────────────────────────────────────────────────┘
```

---

## 🎨 3. Стандарти Кольорів та Семантика Obsidian Canvas

Формат Obsidian Canvas підтримує кольорові ідентифікатори (`"1"` .. `"6"`). Двигун строго дотримується єдиної семантичної матриці:

| Колір Canvas | Назва / Відтінок | Статус Задачі | Семантичне Значення |
| :---: | :---: | :---: | :--- |
| `"4"` | **Зелений (Green)** | `done`, `completed` | Завдання верифіковано 100% Green, слайс зафіксовано в git. |
| `"5"` | **Ціан (Cyan/Blue)** | `in_progress`, `running` | Агент активно виконує роботу над слайсом (MASE bound). |
| `"6"` | **Пурпуровий (Purple)** | `review`, `audit` | Стадія змагального аудиту (`gerych_auditor`) або PR review. |
| `"3"` | **Жовтий (Yellow)** | `backlog`, `planned` | Завдання в черзі, очікує завершення залежностей. |
| `"1"` | **Червоний (Red)** | `blocked`, `failed` | Заблоковано помилкою, порушенням бюджету або Sentinel Alert. |
| `"2"` | **Помаранчевий (Orange)** | `high_risk` | Завдання з високим архітектурним ризиком або зміною ядерних модулів. |

---

## 🤖 4. Swarm Agent Badges (Бейджі Агентів)

Кожен вузол полотна автоматично отримує візуальну плашку виконавця:
- `👑 Gerych Prime` — генеральний координатор та архітектор.
- `🧠 Antigravity (Mentor)` — наставник, архітектурний нагляд та інцепція.
- `🛠️ Gerych Builder` — генерація React/Canvas компонентів та UI.
- `⚡ DNK Fullstack` — FastAPI бекенд, SQLAlchemy та ORM роутери.
- `🛡️ Gerych Auditor` — змагальний рев'юер, pre-commit ворота, перевірка тестів.
- `🎬 Video AI Creator` — Remotion/FrameCN відеокомпозиції та аудіосинтез.
- `🛍️ Shopify Engine` — Liquid шаблони, Checkout UI та розширення магазину.
- `🔒 Security Guard` — брандмауер, фільтрація токенів та секретів.
- `📚 Herich Librarian` — каталогізація знань, ADR та Obsidian нотатки.

---

## 📊 5. Master Control HUD (Інформаційне Табло)

У верхньому лівому куті полотна (`x: 40, y: 80, width: 340, height: 380`) автоматично монтується контрольне табло:

```markdown
# 🎛️ DNK OS Swarm Control Panel
**Goal**: Build Obsidian Canvas Visual Control Panel
---
- 📈 **Progress**: [██████████░░░░░░░░░░] **50%**
- 🎯 **Milestones**: **2** / **4** completed
- ⏳ **Active Tasks**: **1** in progress
- 🐝 **Active Swarm Workers**:
  - 🛠️ Gerych Builder
- 🛡️ **Quality Gate**: **VERIFIED GREEN** (Zero-Waste MASE <= 25 tools)
- ⏱️ **Updated**: 2026-09-06 14:30:00
```

---

## 🔄 6. Двостороння Синхронізація (Bi-directional Synchronization)

Двигун забезпечує безконфліктну двосторонню синхронізацію:
1. **TaskDNA ➔ Canvas**:
   - При виклику `engine.generate_canvas_from_task_dna()` або зміні статусу воркера полотно автоматично оновлює кольори, стан чекбоксів (`- [ ]` ➔ `- [x]`) та кольори залежних ребер.
2. **Canvas ➔ TaskForest**:
   - При редагуванні полотна в Obsidian користувачем (зміна положення вузлів, позначення виконаного чекбокса) функція `engine.sync_canvas_to_forest()` зчитує змінені координати `x`, `y` та статус задачі, оновлюючи стан у `TaskForest` без втрати авторського просторового групування.

---

## 🚀 7. Команди CLI Runner (`scripts/system/visual_canvas_control_runner.py`)

```bash
# 1. Генерація інтерактивного полотна з цілі
python3 scripts/system/visual_canvas_control_runner.py \
  --goal "Build Canvas Engine and Shopify Checkout" \
  --output ./docs/notes/017_Swarm_TaskDNA_Control_Panel.canvas

# 2. Оновлення статусу завдання в реальному часі агентом
python3 scripts/system/visual_canvas_control_runner.py \
  --update-node task_2 \
  --stage done \
  --notes "Unit tests 100% Green, commit sealed"

# 3. Перегляд телеметрії активного полотна
python3 scripts/system/visual_canvas_control_runner.py --status

# 4. Двостороння синхронізація полотна з TaskForest
python3 scripts/system/visual_canvas_control_runner.py --sync-forest
```

---

## 🔗 Пов'язані матеріали
- [[009_Task_Forest_and_TaskDNA|Task Forest & TaskDNA Architecture]]
- [[013_Zero_Touch_Inception_Gateway_Architecture|Вектор 1: Zero-Touch Inception Gateway]]
- [[028 Anti-Loop and AST Fast-Path Architecture|Вектор 2: Anti-Loop & AST Fast-Path]]
- [[015_GitHub_MCP_Fast_Path_and_CI_Evidence_Architecture|Вектор 3: GitHub MCP Fast-Path]]
- [[056_Two_Track_SOTA_Repository_Assimilation_Architecture|Вектор 4: Two-Track SOTA Repository Assimilation]]
- [[011_Obsidian_Dynamic_Bidirectional_Sync_Architecture|Obsidian Dynamic Bidirectional Sync Architecture]]
