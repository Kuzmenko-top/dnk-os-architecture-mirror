---
title: "062 Task Forest Swarm Autonomy and TaskDNA Integration"
tags: ["task_forest", "swarm_autonomy", "task_dna", "dag", "react_flow", "obsidian_sync"]
status: "Active"
author: "DNK-e.com Maksym & Gerych Prime"
created: 2026-09-05
updated: 2026-09-05
---

<!-- --- DNK-MRH-HEADER ---
mrh_id: "docs/notes/062 Task Forest Swarm Autonomy and TaskDNA Integration.md"
purpose: "Architecture & Integration Specification for Swarm Agent Autonomy and TaskDNA DAG generation in Task Forest."
canonical_source: true
alters_files: []
triggers_tasks: []
status: "Active"
version: "1.0.0"
updated_at: "2026-09-05"
author: "DNK-e.com Maksym"
--- END DNK-MRH-HEADER -->

# 🌲 Task Forest: Swarm Autonomy & TaskDNA Integration (Variant A)

## 📌 Executive Summary
Впроваджено модуль **Swarm Autonomy** (Варіант A) для системи [[021 Node Based Task and Ideas DAG System Architecture|Task Forest]].
Тепер вузли завдань можуть призначатися на спеціалізованих агентів ройового інтелекту DNK OS, запускатися в один клік прямо з полотна ReactFlow, а також трансформувати структуровані DAG-дерева [[TaskDNA]] безпосередньо у візуальні вузли із топологічним розміщенням.

---

## 🏗️ Ключові Компоненти Реалізації

### 1. Backend Core (`core/task_forest/`)
- **`TaskNode` розширено полями Swarm-агентів**:
  - `assigned_agent`: ID агента (наприклад, `gerych_builder`, `dnk_dev_fullstack`, `gerych_researcher`, `gerych_auditor`, `dnk_shopify`, `dnk_video_ai_creator`, `herich_librarian`).
  - `agent_status`: `idle` | `running` | `completed` | `failed`.
  - `agent_run_id`: ID запуску або телеметрії.
- **`TaskForest` API**:
  - `assign_agent(node_id, agent_name)`: збереження призначення та виставлення стану `idle`.
  - `dispatch_agent(node_id, mode="direct")`: перевірка готовності, переведення стадії завдання `BACKLOG` ➔ `PLANNED` ➔ `IN_PROGRESS`, та передача задачі агенту.
  - `import_from_task_dna(dna_data, base_x, base_y)`: автоматичне створення вузлів за топологічними шарами глибини залежностей (рівні X: +320px) з маппінгом рівнів ризику на пріоритети (`low`, `medium`, `high`, `critical`).

### 2. Frontend & Zustand Store (`apps/web/store/taskForestStore.ts`)
- Додано `assignedAgent`, `agentStatus`, `agentRunId` до `TaskNodeData`.
- Методи стану:
  - `assignAgent(nodeId, agent)`
  - `dispatchAgent(nodeId)`: асинхронний диспатч у `/api/swarm/dispatch`, переведення ноди в `in_progress` та `review`.
  - `loadFromTaskDNA(dna)`: конвертер вхідного TaskDNA JSON у вузли та ребра з розрахунком глибини залежностей.

### 3. Інтерактивні Компоненти (`apps/web/components/canvas/`)
- **`TaskForestNode.tsx`**:
  - Індикатор Swarm-агента з бейджем статусу (`Running...`, `Done`, `Fail`, `Ready`).
  - Кнопка **«⚡ Dispatch»** для запуску закріпленого робітника.
  - Поповер швидкого вибору агента з переліку 7 спеціалізованих воркерів DNK OS.
- **`TaskForestCanvas.tsx`**:
  - Кнопка **«Import TaskDNA»** на тулбарі полотна.
  - Швидка генерація DAG дерева за довільною метою користувача з автоматичною розстановкою залежностей.

---

## 🧪 Верифікація та Тести
- **Unit & Integration Suite**: `tests/core/test_task_forest.py`
  - `TestSwarmAgentIntegration::test_swarm_agent_assignment_and_dispatch` (100% Passed).
  - `TestSwarmAgentIntegration::test_import_from_task_dna` (100% Passed).
- **Core Regression**: `tests/core/` — 176 passed in 33.62s (100% Green).

---

## 🔗 Зв'язки
- [[021 Node Based Task and Ideas DAG System Architecture]]
- [[016 Unified Swarm Control Plane Architecture and Engine Consolidation]]
- [[009 Task Forest Spatial HQ - 5-Scale LOD Navigation & Time-Travel Engine]]
