---
title: "036 OCC Structural Graph Mutation Resolver"
type: architecture-decision
date: 2026-09-05
tags:
  - occ
  - graph-merge
  - concurrency
  - task-forest
  - canvas
  - zero-waste
status: active
---

<!-- --- DNK-MRH-HEADER ---
mrh_id: "docs/notes/036 OCC Structural Graph Mutation Resolver.md"
purpose: "Architecture Decision Record for OCC 3-Way Structural Graph Mutation Resolver & Node Tasks"
canonical_source: true
alters_files: []
triggers_tasks: []
status: "Active"
version: "1.0.0"
updated_at: "2026-09-05"
author: "Antigravity (Mentor) & DNK-e.com Maksym & Gerych Prime"
--- END DNK-MRH-HEADER -->

# 🧬 036 OCC Structural Graph Mutation Resolver & Node Tasks

## 📌 Executive Summary
У межах реалізації **СЛАЙСУ 16.4** ("OCC Structural Graph Mutation Resolver & Node Tasks 100% Green", за планом `docs/plans/my_task/task_050926-2_occ_merge.md`) реалізовано повноцінний механізм оптимістичного контролю паралельності (OCC) та трьохстороннього злиття структурних мутацій графу (3-Way Graph Merge).

Це вирішує ключову проблему спільної одночасної роботи кількох користувачів та AI-агентів над полотном Canvas і DAG-графом завдань Task Forest:
1. Запобігання втраті даних (Zero Data Loss) при одночасних правках.
2. Автоматичне детерміністичне вирішення просторових конфліктів вузлів (Node Position Conflicts) через векторне зміщення (+20px) або LWW.
3. Безконфліктне злиття метаданих вузлів (об'єднання тегів через Set union, конкатенація описів).
4. Структурна валідація зв'язків (Edge Conflicts) із перевіркою відсутності циклів через DAG cycle detection та поверненням `HTTP 409 Conflict` при нерозв'язних структурних циклах.

---

## 🏗️ Ключові Компоненти та Контракти

```
           +---------------------------------------+
           |       Ancestor State (Base)           |
           +-------------------+-------------------+
                               |
                +--------------+--------------+
                |                             |
                v                             v
     +--------------------+        +--------------------+
     | Mine (Incoming/UI) |        | Theirs (Server/OCC)|
     +----------+---------+        +----------+---------+
                |                             |
                +--------------+--------------+
                               |
                               v
               +-------------------------------+
               |     OCCConcurrencyEngine      |
               |       (core/occ_merge.py)     |
               +---------------+---------------+
                               |
            [3-Way Structural Merge Algorithm]
            - Node diffs & concurrent additions
            - Position resolution (Vector shift +20px / LWW)
            - Tags set union & Description concatenation
            - Edge diffs & DAG cycle detection
                               |
             +-----------------+-----------------+
             |                                   |
    [No structural cycle]             [Cycle detected]
             v                                   v
    +------------------+              +--------------------+
    |  Merged Graph    |              |  HTTP 409 Conflict |
    |  Status: SUCCESS |              |  Status: CONFLICT  |
    +------------------+              +--------------------+
```

### 1. `core/occ_merge.py` (`OCCConcurrencyEngine` / `OCCGraphMergeResolver`)
- **Метод**: `merge_graph_state(base_state, current_state, incoming_state, position_strategy="shift") -> OCCMergeResult`.
- **Стратегії позицій**:
  - `shift`: Детерміністичне векторне зміщення паралельно переміщеного вузла на `(+20px, +20px)` для уникнення перекриття.
  - `last_write_wins` / `mine`: Пріоритет вхідної локальної позиції.
- **Дані вузлів**:
  - `tags`: Об'єднання множин `set(mine_tags) | set(theirs_tags)`.
  - `description`: Конкатенація обох описів через роздільник `\n---\n` у разі одночасної модифікації.
- **DAG Cycle Detection**:
  - Валідація через `DependencyGraph` (`core/task_forest/dependencies.py`) та `NodeTaskGraphEngine`.
  - Будь-яка спроба замкнути залежність у цикл фіксується як нерозв'язний структурний конфлікт `CYCLE_DETECTED`.

### 2. `apps/api/routers/node_tasks_router.py` (Endpoint `/merge`)
- **Маршрут**: `POST /api/v3/node_tasks/merge`
- **Запит**: `MergeGraphRequest(base_state, incoming_state, current_state=None, position_strategy="shift", save_to_persistence=True)`
- **Відповідь**:
  - `200 OK`: `OCCMergeResult` з об'єднаним графом, списком мутацій та резолюціями.
  - `409 Conflict`: Вичерпний опис циклічного конфлікту із забороною пошкодження топології.

---

## 📊 Верифікація та Метрики

- **Юніт-тести**: `tests/core/test_occ_merge.py` (7/7 passed).
- **Двигун графу**: `tests/core/test_node_task_graph_engine.py` (6/6 passed).
- **API-верифікація**: `tests/verification/test_node_tasks_router.py` (7/7 passed).
- **Master Quality Gate**: `bash scripts/verify_all.sh` — **1,752 passed, 0 failures, 35 skipped (100% Green)**.

## 🔗 Пов'язані Нотатки
- [[035 MCP Slim Guard Context Compression]]
- [[task-node-system]]
- [[task-occ-merge]]
