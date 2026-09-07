---
title: "Graphify AST Engine Assimilation & Test Report"
tags: ["architecture", "ast", "canvas", "graphify", "sota", "assimilation"]
created_at: "2026-09-06"
status: "Completed"
---
<!-- --- DNK-MRH-HEADER ---
mrh_id: "docs/notes/014 Graphify Assimilation & Test Report.md"
purpose: "Technical report on Graphify extraction test on DNK_HUB and architectural assimilation plan."
canonical_source: false
alters_files: []
triggers_tasks: []
status: "Active"
version: "1.0.0"
updated_at: "2026-09-06"
author: "Gerych Prime (Hermes)"
--- END DNK-MRH-HEADER -->

# 🕸️ Звіт про тестування та асиміляцію Graphify в DNK_HUB

## 📌 1. Результати запуску на кодовій базі DNK_HUB
- **Обсяг аналізу**: 7,668 файлів коду (Python, TypeScript, Liquid, Rust, Astro тощо).
- **Побудований граф**:
  - **108,404 вузли** (класи, функції, інтерфейси, файли, методи).
  - **190,277 ребер** (95% `EXTRACTED` явних синтаксичних викликів, 5% `INFERRED` ланцюжкових).
  - **5,476 спільнот** (Leiden/Louvain кластеризація топології).
  - **0 витрачених токенів** — повністю локальний, миттєвий AST-парсинг через Tree-sitter.

## 🏛️ 2. Виявлені "God Nodes" (Архітектурні хаби кодової бази)
1. `startServer()` — 759 зв'язків
2. `useT()` — 319 зв'язків
3. `err()` — 307 зв'язків
4. `ProjectView()` — 290 зв'язків
5. `error()` — 280 зв'язків
6. `buffer` — 244 зв'язки
7. `workspaceProjectHeaders()` — 191 зв'язок

## ⚡ 3. Тест аналітичних запитів (Live Demos)

### 3.1. Blast Radius Analysis (`graphify affected "VisualCanvasControlEngine"`)
- За мілісекунди детерміновано повернуто повний радіус ураження при зміні класу: 27 залежних файлів та тестів (включно з `canvas_bridge.py`, `hermes_post_tool_hook.py`, `test_visual_canvas_control.py`).
- Це усуває сліпі плями під час рефакторингу без необхідності запускати дорогі LLM-сканування.

### 3.2. Найкоротший шлях викликів (`graphify path "VisualCanvasControlEngine" "AccountingEngine"`)
- Результат (4 хопи):
  `VisualCanvasControlEngine` $\to$ `canvas_bridge.py` $\to$ `api/main.py` $\to$ `swarm_ws.py` $\to$ `AccountingEngine`.

## 🎨 4. Згенеровані візуальні артефакти
1. **[[DNK_HUB_Core_Architecture.canvas]]**:
   - Полотно в стандартному форматі Obsidian JSON Canvas.
   - 4 згруповані кольорові кластери: *Core Orchestrator & Agents*, *Core Engines & RAG*, *FastAPI Backend & Routers*, *Other Subsystems*.
   - Топова сотня найбільш зв'язаних компонентів ядра з точним розташуванням та взаємними стрілками.
2. **`graphify-out/GRAPH_TREE.html`**:
   - Інтерактивне ієрархічне D3 v7 дерево файлів і символів (5.9 MB) для миттєвого дослідження в браузері.

## 🚀 5. План асиміляції за стандартом Track 1 (Apache 2.0)
1. **Інтеграція в `core/obsidian/export_canvas.py`**:
   - Впровадити математику автоматичного розрахунку сітки груп (`math.ceil(math.sqrt(n))`) для автоматичного перетворення будь-якого TaskDNA DAG у гарне структуроване полотно.
2. **Підсилення `scripts/system/repo_map.py`**:
   - Додати CLI-команди `path`, `affected` та `god-nodes` для автономних агентів перед початком модифікації коду.
3. **Adversarial Quality Gate (`gerych_auditor`)**:
   - Додати перевірку відсутності нових циклічних імпортів (`find_import_cycles`) перед комітами.
