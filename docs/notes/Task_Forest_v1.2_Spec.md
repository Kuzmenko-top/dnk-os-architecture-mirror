---
title: "Task Forest v1.2: Двостороння синхронізація Canvas ↔ Obsidian Vault"
aliases:
  - "Task Forest v1.2 Spec"
  - "Obsidian Canvas Two-Way Sync"
  - "Task Forest Architecture Specification"
tags:
  - dnk-hub
  - task-forest
  - canvas
  - obsidian
  - sync
  - architecture
  - specification
type: specification
status: active
created: 2026-09-04
updated: 2026-09-04
author: "Maksym Kuzmenko & Gerych Prime"
---

<!-- --- DNK-MRH-HEADER ---
mrh_id: "obsidian/DNK_HUB/Task_Forest_v1.2_Spec.md"
purpose: "Canonical Specification and Architecture Protocol for Task Forest v1.2 Two-Way Canvas and Obsidian Vault Sync."
canonical_source: true
alters_files: []
triggers_tasks: []
status: "Active"
version: "1.2.0"
updated_at: "2026-09-04"
author: "DNK-e.com Maksym & Gerych Prime"
--- END DNK-MRH-HEADER -->

-->

# 🌲 Task Forest v1.2: Специфікація двосторонньої синхронізації (Canvas ↔ Obsidian Vault)

> **Пов'язані матеріали в Базі Знань:**
> - [[000 DNK HUB Index|🌌 000 Головний покажчик знань DNK HUB (MOC)]]
> - [[007 Obsidian Vault Bidirectional Canvas Sync Protocol|🔄 007 Архітектурний протокол двосторонньої синхронізації]]
> - [[002 DNK OS - Master System Architecture & Implementation Blueprint|🌌 002 Генеральна архітектура системи DNK OS]]
> - [[004 Gerych Task Specification Standard & Zero-Waste Protocol v2.5|📋 004 Стандарт постановки задач та MASE Protocol]]
> - [[Beads Task Forest Integration|🌲 Інтеграція Task Forest та графу залежностей]]

---

## 1. Overview (Загальний огляд)
**Task Forest v1.2** забезпечує безшовний двосторонній міст між візуальним нескінченним полотном **DNK OS Infinite Canvas** (на базі ReactFlow / Spatial Canvas) та локальною базою знань у форматі **Obsidian Vault**.

### 🎯 Ключові цілі та задачі
1. **Єдине джерело істини (SSOT)**: Будь-яка зміна статусу, опису чи пріоритету задачі в Obsidian Markdown автоматично відображається на візуальному полотні.
2. **Збереження топології (Spatial Layout Preservation)**: Зміна тексту всередині нотатки Obsidian не руйнує просторові координати $(x, y)$ та габарити вузла на візуальному полотні.
3. **Чистий Python без бінарних залежностей**: Модулі серіалізації та парсингу працюють виключно на стандартній бібліотеці Python (`json`, `re`, `pathlib`, `os`).
4. **WebSocket RPC у реальному часі**: Миттєва передача подій синхронізації між бекендом FastAPI та фронтендом React.

---

## 2. Формати даних та структура артефактів

### 2.1 Markdown з YAML Frontmatter
Всі вузли зберігаються у вигляді ізольованих Markdown-файлів із валідним метаданим заголовком YAML:

- **Ключові поля метаданих**:
  - `id`: Унікальний ідентифікатор вузла (`node-001`, `task-arch-01`).
  - `title`: Заголовок задачі/нотатки.
  - `type`: Семантичний тип вузла (`task`, `decision`, `milestone`, `text`, `agent`, `file`).
  - `status`: Стан виконання (`pending`, `in_progress`, `completed`, `blocked`).
  - `priority`: Ранг пріоритету (`low`, `medium`, `high`, `critical`).
  - `tags`: Масив класифікаційних міток для пошуку й Dataview.
  - `updated_at`: Часова мітка UNIX (використовується для детермінованого вирішення конфліктів).
  - `source_canvas`: Назва пов'язаного файлу полотна (`.canvas`).

#### 📝 Приклад нотатки вузла (`node-001.md`)
```markdown
---
id: node-001
type: task
title: Architecture Design
tags:
  - architecture
  - core
  - task-forest
updated_at: 1725478200.0
status: completed
priority: high
source_canvas: phase-11-mindmap.canvas
---

# Architecture Design

**Description:** Initial design specs for Task Forest bidirectional synchronization engine.

### Вимоги до реалізації:
1. Підтримка відкритого формату JSON Canvas v1.0.
2. Автоматичне злиття неконфліктуючих тегів.
3. Підтримка прямого виклику з UI панелі `ObsidianSyncBar.tsx`.
```

---

### 2.2 JSON Canvas v1.0
Формат інтерактивного полотна повністю сумісний з офіційною специфікацією **[JSON Canvas v1.0](https://jsoncanvas.org/)**:

```json
{
  "nodes": [
    {
      "id": "node-001",
      "x": 100,
      "y": 100,
      "width": 260,
      "height": 140,
      "type": "text",
      "color": "1",
      "text": "## Architecture Design\n\nInitial design specs for Task Forest"
    },
    {
      "id": "node-002",
      "x": 450,
      "y": 100,
      "width": 260,
      "height": 140,
      "type": "text",
      "color": "4",
      "text": "## Backend Sync Engine\n\nPython modules for export and import"
    }
  ],
  "edges": [
    {
      "id": "e1-2",
      "fromNode": "node-001",
      "toNode": "node-002",
      "fromSide": "right",
      "toSide": "left",
      "label": "enables",
      "color": "1"
    }
  ]
}
```

---

### 2.3 Структура бандлу (Bundle Directory Layout)
Експорт бандлу генерує самодостатній каталог, готовий для відкриття в Obsidian:

```
TaskForest/
├── phase-11-mindmap.canvas          # Інтерактивне полотно Obsidian Canvas
├── node-001.md                     # Вузол: Архітектура та протоколи
├── node-002.md                     # Вузол: Бекенд-двигун синхронізації
├── node-003.md                     # Вузол: UI віджет ObsidianSyncBar
├── node-004.md                     # Вузол: Алгоритм Last-Write-Wins
└── node-005.md                     # Вузол: E2E Тестові шлюзи якості
```

---

## 3. Протокол синхронізації та вирішення конфліктів

```
┌─────────────────────────┐               ┌─────────────────────────┐
│     ReactFlow UI        │               │     FastAPI WebSocket   │
│  (ObsidianSyncBar.tsx)  │               │   (canvas_v3_ws.py)     │
└────────────┬────────────┘               └────────────┬────────────┘
             │                                         │
             │ 1. OBSIDIAN_SYNC_REQUEST                │
             ├────────────────────────────────────────►│
             │    (direction, canvas_name, nodes)      │
             │                                         │ 2. resolve_conflicts()
             │                                         │    export_canvas_bundle()
             │                                         │    LWW Strategy
             │                                         ▼
             │                              ┌──────────────────────┐
             │                              │   Obsidian Vault     │
             │                              │  (.canvas + .md)     │
             │                              └──────────────────────┘
             │                                         │
             │ 3. OBSIDIAN_SYNC_STATUS                 │
             │◄────────────────────────────────────────┤
             │    (status: success, nodes, stats)      │
             ▼                                         ▼
```

### 3.1 Алгоритм Last-Write-Wins (LWW)
1. **Зіставлення за ID**: Для кожного вузла з Canvas шукається відповідний файл Markdown у Vault.
2. **Аналіз часових міток**:
   - $t_{MD} = \max(\text{yaml.updated\_at}, \text{file.mtime})$
   - $t_{Canvas} = \text{node.data.updated\_at}$
3. **Об'єднання властивостей**:
   - Якщо $t_{MD} \ge t_{Canvas}$: Заголовок, опис, статус та теги оновлюються з Markdown. Просторове положення $(x, y, w, h)$ зберігається з Canvas.
   - Якщо $t_{Canvas} > t_{MD}$: Дані полотна мають пріоритет, теги дедуплікуються та зливаються.

---

## 4. Карта компонентів кодової бази

| Компонент | Локальний шлях | Роль у системі |
|-----------|----------------|----------------|
| **Export Engine** | `core/obsidian/export_canvas.py` | Експорт нод, ребер, генерація YAML frontmatter та .canvas файлів |
| **Import Engine** | `core/obsidian/import_canvas.py` | Парсинг markdown/canvas, алгоритм вирішення конфліктів LWW |
| **WebSocket Router** | `apps/api/routers/canvas_v3_ws.py` | Прийом та трансляція повідомлень `OBSIDIAN_SYNC_*` |
| **UI Sync Bar** | `apps/web/components/canvas/ObsidianSyncBar.tsx` | Інтерфейсний віджет синхронізації у робочому просторі |
| **Canvas Store** | `apps/web/store/canvasStore.ts` | Керування реактивним станом полотна та RPC-командами |

---

## 5. Докази верифікації (Master Quality Gate)

Усі сценарії верифіковано в автономному тестовому оточенні:
- **Команда**: `.venv/bin/pytest tests/canvas/test_obsidian_sync.py`
- **Результат**: **3 passed in 0.12s (100% Green)**
- **Сценарії**:
  - `test_export_five_nodes_to_canvas`: Перевірено коректність формування `.canvas` формату для топології 5 вузлів / 4 ребра.
  - `test_import_canvas_to_five_nodes`: Підтверджено повне відновлення координат та зв'язків при імпорті з диска.
  - `test_conflict_resolution_last_write_wins`: Підтверджено роботу алгоритму Last-Write-Wins при конкурентному оновленні нотаток.
