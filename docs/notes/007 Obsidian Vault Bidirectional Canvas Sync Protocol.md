---
title: "007 Obsidian Vault Bidirectional Canvas Sync Protocol"
aliases:
  - "Obsidian Canvas Sync"
  - "Task Forest Obsidian Integration"
  - "Stage 11.3 Sync Protocol"
tags:
  - dnk-hub
  - obsidian
  - canvas
  - task-forest
  - architecture
  - synchronization
type: architecture-spec
status: active
created: 2026-09-04
updated: 2026-09-04
author: "Maksym Kuzmenko & Gerych Prime"
---

<!-- --- DNK-MRH-HEADER ---
mrh_id: "obsidian/DNK_HUB/007 Obsidian Vault Bidirectional Canvas Sync Protocol.md"
purpose: "Canonical Architecture, Data Contracts & Sync Engine Specification for Stage 11.3 Obsidian Vault & JSON Canvas Integration."
canonical_source: true
alters_files: []
triggers_tasks: []
status: "Active"
version: "1.0.0"
updated_at: "2026-09-04"
author: "DNK-e.com Maksym & Gerych Prime"
--- END DNK-MRH-HEADER -->

-->

# 🔄 007 Obsidian Vault Bidirectional Canvas Sync Protocol (Stage 11.3)

## 📌 1. Executive Summary & Context

В рамках розвитку просторового агентного інтерфейсу **DNK OS (Task Forest / Spatial Canvas HQ)** реалізовано двосторонню інтеграцію з локальною базою знань **Obsidian Vault** (`~/Documents/DNK_HUB My Notes/TaskForest`).

Цей протокол ліквідує розрив між візуальним мапуванням задач/агентів у Canvas та текстовим представленням у Markdown-сховищі Obsidian. Будь-який вузол просторового полотна транслюється у структурований Markdown-документ з YAML-метаданими та MRH-заголовками, а зв'язки (edges) — у стандартний формат Obsidian JSON Canvas (`.canvas`) та [[wikilinks]].

---

## 🏗️ 2. Архітектура двосторонньої синхронізації

```
+--------------------------------------------------------------------------+
|                        DNK OS Spatial Canvas (Web UI)                    |
|  [CanvasEngine] <-> [useCanvasStore] <-> [ObsidianSyncBar]               |
+------------------------------------+-------------------------------------+
                                     |
                          WebSocket RPC / Payload
                   (OBSIDIAN_SYNC_REQUEST / STATUS)
                                     |
+------------------------------------v-------------------------------------+
|                      DNK Canvas API (FastAPI Backend)                    |
|                        apps/api/routers/canvas_v3_ws.py                  |
+------------------------------------+-------------------------------------+
                                     |
                  +------------------+------------------+
                  |                                     |
       core/obsidian/export_canvas.py         core/obsidian/import_canvas.py
                  |                                     |
                  | [Export Pipeline]                   | [Import Pipeline]
                  v                                     v
+--------------------------------------------------------------------------+
|                  Local Obsidian Vault Storage Target                     |
|           ~/Documents/DNK_HUB My Notes/TaskForest/                       |
|   - {node_id}_{title}.md (YAML frontmatter + Markdown body)              |
|   - {canvas_id}.canvas   (Obsidian JSON Canvas spec)                     |
+--------------------------------------------------------------------------+
```

---

## 🧬 3. Компоненти системи

### 3.1. Бекенд експорту (`core/obsidian/export_canvas.py`)
1. **`export_node_to_markdown(node, output_dir)`**:
   - Формує валідний YAML frontmatter: `id`, `type`, `title`, `status`, `assigned_agent`, `tags`, `updated_at`.
   - Вбудовує DNK-MRH заголовок (`DNK-STD-0075`).
   - Генерує тіло нотатки з описами, метаданими, чеклістами та вихідними зв'язками `[[wikilinks]]`.
2. **`export_to_obsidian_canvas(nodes, edges, output_path)`**:
   - Конвертує вузли DNK Canvas у специфікацію Obsidian JSON Canvas (`nodes`: `id`, `type='file'|'text'`, `x`, `y`, `width`, `height`, `file`).
   - Конвертує зв'язки Canvas у Obsidian Canvas edges (`id`, `fromNode`, `toNode`, `label`, `toEnd='arrow'`).
3. **`export_canvas_bundle(nodes, edges, vault_dir, canvas_name)`**:
   - Атомарно записує як індивідуальні `.md` нотатки, так і зведений файл `{canvas_name}.canvas`.

### 3.2. Бекенд імпорту та парсингу (`core/obsidian/import_canvas.py`)
1. **`parse_canvas_file(canvas_source)`**:
   - Читає Obsidian JSON Canvas структуру, витягує координати, розміри, типи та зв'язки.
2. **`parse_markdown_file(file_path)`**:
   - Парсить YAML frontmatter, витягує статус, призначеного агента, тип нотатки та текстовий вміст.
3. **`resolve_conflicts_last_write_wins(canvas_nodes, vault_nodes)`**:
   - Алгоритм вирішення конфліктів **Last-Write-Wins (LWW)** на базі міток часу `updated_at` / `mtime`.
   - Якщо версія у Vault новіша за версію у Canvas — оновлюються дані вузла в полотні.
4. **`import_canvas_and_markdown(canvas_path, markdown_dir, existing_nodes)`**:
   - Зводить файли полотна та нотатки в уніфікований масив вузлів та ребер для UI.

### 3.3. Фронтенд панель синхронізації (`apps/web/components/canvas/ObsidianSyncBar.tsx`)
- Інтерактивна плаваюча панель управління синхронізацією з Obsidian.
- Кнопки:
  - 📤 **Export to Vault**: миттєвий експорт поточного полотна в нотатки та `.canvas`.
  - 📥 **Import from Vault**: зчитування змін з файлової системи Vault.
  - 🔄 **Bidirectional Sync**: двостороннє узгодження з підсвіткою статусу (Idle / Syncing / Success / Error).
- Налаштування шляху до Vault (`~/Documents/DNK_HUB My Notes/TaskForest`).

### 3.4. Сховище стану (`apps/web/store/canvasStore.ts`)
- Додано стан: `obsidianSyncStatus`, `obsidianSyncMessage`, `lastObsidianSyncTime`.
- Метод `syncToObsidian(direction: 'export' | 'import' | 'bidirectional')`:
  - Відправляє RPC запит через WebSocket на `apps/api/routers/canvas_v3_ws.py`.
  - Обробляє події `OBSIDIAN_SYNC_STATUS` та автоматично оновлює стан полотна при імпорті.

---

## 🛡️ 4. Стратегія вирішення конфліктів (LWW)

```python
def resolve_conflicts_last_write_wins(
    canvas_nodes: List[Dict[str, Any]], 
    vault_nodes: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    # Для кожного співпадаючого ID порівнюється unix timestamp:
    # canvas_ts = canvas_node.get("data", {}).get("updated_at", 0)
    # vault_ts  = vault_node.get("data", {}).get("updated_at", mtime)
    # Переможець з більшим значенням оновлює властивості
```

- **Safety Guarantee**: Жодна нотатка не перезаписується без перевірки існування та валідації формату JSON.
- **Fail-Safe Fallback**: У разі пошкодження `.canvas` файлу дані вузлів відновлюються з індивідуальних `.md` файлів.

---

## 🧪 5. Верифікація та тестове покриття

Усі компоненти Stage 11.3 покриті комплексними юніт- та інтеграційними тестами:

1. `tests/core/test_obsidian_export_import.py`:
   - `test_sanitize_filename` — очищення назв файлів від спецсимволів.
   - `test_export_node_to_markdown` — валідність YAML frontmatter та MRH заголовків.
   - `test_export_to_obsidian_canvas` — валідність JSON Canvas специфікації.
   - `test_export_canvas_bundle` — атомарне створення пакету нотаток + канвасу.
   - `test_parse_canvas_file` — зчитування вузлів та стрілок зв'язків.
   - `test_parse_markdown_file` — витяг метаданих із frontmatter.
   - `test_resolve_conflicts_last_write_wins` — точність LWW арбітражу.
   - `test_import_canvas_and_markdown` — повний цикл регідрації.
   *(9/9 passed)*

2. `tests/canvas/test_obsidian_sync.py`:
   - `test_export_five_nodes_to_canvas` — експорт складного графу з 5 різнотипних вузлів.
   - `test_import_canvas_to_five_nodes` — точний зворотний імпорт зі збереженням зв'язків.
   - `test_conflict_resolution_last_write_wins` — сценарій паралельної модифікації.
   *(3/3 passed)*

**Загальний результат:** 12/12 Green (100%), загальний тест-сьют: 1568 passed.

---

## 🚀 6. Напрямки подальшого розвитку

1. **Файловий Watcher (FSEvents/inotify)**: автоматичний фоновий імпорт при збереженні нотаток безпосередньо в десктопному додатку Obsidian.
2. **CRDT / Yjs інтеграція**: повузловий merge замість грубого Last-Write-Wins для одночасного редагування складних описів.
3. **Task Forest Graph View**: автоматичне формування глобального MOC-індексу всіх активних полотен DNK OS.

---

## 🔗 Пов'язані документи
- [[000 DNK HUB Index|🌌 000 DNK HUB: Головний покажчик бази знань (MOC)]]
- [[001 Obsidian & DNK OS Documentation Standard|📐 001 Стандарт ведення нотаток DNK OS]]
- [[002 DNK OS - Master System Architecture & Implementation Blueprint|🏛️ 002 DNK OS - Master System Architecture]]
- [[004 Gerych Task Specification Standard & Zero-Waste Protocol v2.5|📋 004 Gerych Task Specification Standard]]
- [[005 ADR 0042 Canvas Runtime Bridge & WebSocket Integration|📡 005 ADR 0042 Canvas Runtime Bridge]]
