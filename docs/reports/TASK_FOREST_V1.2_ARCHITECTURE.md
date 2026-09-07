<!-- --- DNK-MRH-HEADER ---
mrh_id: "docs/reports/TASK_FOREST_V1.2_ARCHITECTURE.md"
purpose: "Canonical Architecture Report & Specification for Task Forest v1.2 Two-Way Canvas and Obsidian Vault Sync."
canonical_source: true
alters_files: []
triggers_tasks: []
status: "Active"
version: "1.2.0"
updated_at: "2026-09-04"
author: "DNK-e.com Maksym & Gerych Prime"
--- END DNK-MRH-HEADER --- -->

# Task Forest v1.2: Two-Way Sync Architecture

## 1. Overview
- **Мета**: Двостороння безшовна синхронізація просторового полотна Canvas (DNK OS Spatial Canvas / Task Forest) з локальною базою знань Obsidian Vault (`~/Documents/DNK_HUB My Notes/TaskForest`).
- **Ключові компоненти**:
  - `core/obsidian/export_canvas.py`: Експорт вузлів полотна у Markdown-нотатки з YAML frontmatter та генерація єдиного Obsidian JSON Canvas (`.canvas`).
  - `core/obsidian/import_canvas.py`: Парсинг `.canvas` та `.md` файлів з автоматичним розв'язанням колізій (Last-Write-Wins).
  - `apps/web/components/canvas/ObsidianSyncBar.tsx`: Компактна панель керування в React UI для ініціації експорту, імпорту та повного циклу синхронізації.
  - `apps/web/store/canvasStore.ts`: Стан полотна (Zustand) та RPC-виклик `syncToObsidian`.
  - `apps/api/routers/canvas_v3_ws.py`: FastAPI WebSocket обробник повідомлень синхронізації в реальному часі.
- **Протокол**: WebSocket RPC (`OBSIDIAN_SYNC_REQUEST` → `OBSIDIAN_SYNC_STATUS`).

---

## 2. Формати даних

### 2.1 Markdown з YAML Frontmatter
Кожна нода полотна за потреби експортується в окремий Markdown-файл у папці сховища Obsidian. Структура файлу містить повний набір метаданих для підтримки Dataview, Obsidian Graph View та семантичного пошуку.

- **Схема полів**:
  - `id` *(string)*: Унікальний ідентифікатор вузла (наприклад, `node-001` або `bd-arch.1.2`).
  - `title` *(string)*: Назва/лейбл вузла.
  - `type` *(string)*: Тип вузла (`task`, `decision`, `milestone`, `text`, `agent`, `file`).
  - `status` *(string, optional)*: Стан виконання (`pending`, `in_progress`, `completed`, `blocked`).
  - `priority` *(string | int, optional)*: Пріоритет вузла (`low`, `medium`, `high`, `critical` або числовий ранг 1..5).
  - `tags` *(list[string])*: Список тегів для категорізації.
  - `updated_at` *(float | int)*: UNIX timestamp останньої модифікації (SSOT для LWW).
  - `source_canvas` *(string, optional)*: Посилання на батьківський canvas-документ.

**Приклад ноди (`TaskForest/node-001.md`):**
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

Detailed implementation requirements for two-way synchronization between DNK OS Infinite Canvas and Obsidian Vault:
1. Pure Python parser and serializer without binary dependencies.
2. Last-Write-Wins conflict resolution algorithm.
3. Spatial coordinates preservation upon markdown updates.
```

---

### 2.2 JSON Canvas v1.0
Специфікація відповідає офіційному відкритому стандарту [JSON Canvas v1.0](https://jsoncanvas.org/), підтримуваному Obsidian Canvas.

- **Основні поля документа**:
  - `nodes`: Масив об'єктів вузлів.
    - `id` *(string)*: Ідентифікатор ноди.
    - `type` *(string)*: `"text"` | `"file"` | `"link"` | `"group"`.
    - `x`, `y` *(int / float)*: Координати розташування на нескінченному полотні.
    - `width`, `height` *(int / float)*: Розміри блоку.
    - `text` *(string, для type="text")*: Markdown-вміст або заголовок вузла.
    - `file` *(string, для type="file")*: Відносний шлях до `.md` нотатки у vault.
    - `color` *(string, optional)*: Колір вузла (`1`..`6` або hex `#6366f1`).
  - `edges`: Масив напрямлених зв'язків.
    - `id` *(string)*: Ідентифікатор ребра.
    - `fromNode`, `toNode` *(string)*: ID джерела та цілі.
    - `fromSide`, `toSide` *(string, optional)*: Точка кріплення (`"top"`, `"right"`, `"bottom"`, `"left"`).
    - `label` *(string, optional)*: Текстова мітка зв'язку (семантика відношення).
    - `color` *(string, optional)*: Колір зв'язку.

**Приклад `.canvas` файлу (`TaskForest/phase-11-mindmap.canvas`):**
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
      "text": "## Architecture Design\n\nInitial design specs for task forest"
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

### 2.3 Bundle Structure
При комплексному експорті (`export_canvas_bundle`) створюється цілісна папка, сумісна з Obsidian:

```
TaskForest/
├── phase-11-mindmap.canvas          # Головне інтерактивне полотно Obsidian
├── node-001.md                     # Нотатка вузла 001 (Architecture Design)
├── node-002.md                     # Нотатка вузла 002 (Backend Sync Engine)
├── node-003.md                     # Нотатка вузла 003 (Frontend SyncBar UI)
├── node-004.md                     # Нотатка вузла 004 (Conflict Strategy Gate)
└── node-005.md                     # Нотатка вузла 005 (E2E Verification & Release)
```

---

## 3. Протокол синхронізації та вирішення колізій

### 3.1 Режими синхронізації
1. **`export` (Canvas ➔ Obsidian Vault)**:
   - Серіалізує поточний стан ReactFlow-полотна у JSON Canvas v1.0.
   - Опціонально генерує окремі Markdown-нотатки для кожного вузла.
   - Зберігає структуру безпосередньо у цільову директорію сховища Obsidian.
2. **`import` (Obsidian Vault ➔ Canvas)**:
   - Сканує вказану папку або файл `.canvas` та супутні `.md` нотатки.
   - Відновлює просторове розташування, розміри, типи та зв'язки (edges).
   - Застосовує розв'язання колізій до існуючих нод полотна.
3. **`sync` / `both` (Двосторонній обмін)**:
   - Здійснює запис поточних змін полотна у Vault.
   - Проводить зворотне зчитування з об'єднанням оновлень з Obsidian нотаток.

---

### 3.2 Стратегія вирішення конфліктів: Deterministic Last-Write-Wins (LWW)
При одночасному редагуванні вузла на веб-полотні та у Obsidian нотатці застосовується детермінований алгоритм **Last-Write-Wins** з багаторівневим tie-breaker на основі кортежу `(updated_at, revision, content_hash)`:
- **Крок 1: Порівняння міток часу (`updated_at`)**:
  - Якщо $t_{MD} > t_{Canvas}$: перемагає Markdown.
  - Якщо $t_{Canvas} > t_{MD}$: перемагає Canvas.
- **Крок 2: Tie-breaker за ревізією (`revision`)**:
  - Якщо мітки часу однакові ($t_{MD} == t_{Canvas}$), порівнюються цілочисельні ревізії (`revision`).
  - Версія з вищим номером ревізії перемагає.
- **Крок 3: Tie-breaker за гешем контенту (`content_hash`)**:
  - Якщо мітки часу та ревізії збігаються, порівнюється SHA-256 геш контенту у лексикографічному порядку (`hash_md > hash_canvas`).
  - Це усуває будь-яку недетермінованість при одночасних паралельних мутаціях.
- **Крок 4: Повна ідентичність**:
  - Якщо кортежі повністю збігаються, зберігається позиція полотна Canvas, а теги об'єднуються без дублікатів (`combined_tags = list(dict.fromkeys(c_tags + m_tags))`).

**Поведінка при перемозі**:
- **Markdown перемагає**: Текстовий вміст, заголовок, опис, теги та метадані оновлюються з Markdown. Просторові координати (`x`, `y`, `width`, `height`) залишаються непорушними з Canvas, щоб запобігти колапсу візуального макета.
- **Canvas перемагає**: Вміст Canvas має пріоритет. Неконфліктуючі теги об'єднуються.

---

### 3.3 Безпека шляхів: Canonical Vault Paths & Path Traversal Protection

Для захисту файлової системи хоста від атак виходу за межі сховища (Path Traversal) введено жорстке обмеження цільових директорій:

1. **Канонічні шляхи сховища**:
   - `canonical_vault_root`: `~/Documents/DNK_HUB My Notes` (налаштовується через env `DNK_OBSIDIAN_VAULT_ROOT` або `OBSIDIAN_VAULT_ROOT`).
   - `canonical_task_forest_dir`: `~/Documents/DNK_HUB My Notes/TaskForest` (налаштовується через env `DNK_OBSIDIAN_TASK_FOREST_DIR`).
2. **Path Traversal Shield (`validate_vault_path`)**:
   - Будь-який параметр `target_dir` або `folder_path`, переданий через WebSocket API чи локальні методи імпорту/експорту, проходить обов'язкову валідацію:
     `resolved_target.relative_to(canonical_vault_root)`
   - Якщо шлях намагається вийти за межі `canonical_vault_root` (використання `../`, абсолютні системні шляхи на кшталт `/etc`, `/tmp`, або сторонні каталоги), негайно генерується виняток:
     `ValueError: Path traversal forbidden: target_dir '<path>' is outside canonical Vault root '<root>'`
   - WebSocket негайно повертає клієнту подію помилки `OBSIDIAN_SYNC_STATUS` зі статусом `"error"` і кодом блокування.

---

### 3.4 WebSocket RPC протокол

#### Запит клієнта (`OBSIDIAN_SYNC_REQUEST`)
```json
{
  "type": "OBSIDIAN_SYNC_REQUEST",
  "direction": "export",
  "canvas_id": "phase-11-mindmap",
  "canvas_name": "phase-11-mindmap",
  "target_dir": "~/Documents/DNK_HUB My Notes/TaskForest",
  "export_individual_md": true,
  "link_as_file_nodes": false,
  "conflict_strategy": "last-write-wins",
  "nodes": [
    {
      "id": "node-001",
      "type": "task",
      "position": {"x": 100, "y": 100},
      "width": 260,
      "height": 140,
      "data": {
        "title": "Architecture Design",
        "description": "Initial design specs",
        "status": "completed",
        "tags": ["architecture", "core"]
      }
    }
  ],
  "edges": [
    {
      "id": "e1-2",
      "source": "node-001",
      "target": "node-002",
      "label": "enables"
    }
  ]
}
```

#### Відповідь сервера (`OBSIDIAN_SYNC_STATUS`)
```json
{
  "type": "OBSIDIAN_SYNC_STATUS",
  "event": "OBSIDIAN_SYNC_STATUS",
  "status": "success",
  "canvas_id": "phase-11-mindmap",
  "direction": "export",
  "result": {
    "canvas_path": "~/Documents/DNK_HUB My Notes/TaskForest/phase-11-mindmap.canvas",
    "markdown_files": [
      "~/Documents/DNK_HUB My Notes/TaskForest/node-001.md"
    ],
    "node_count": 1,
    "edge_count": 0
  },
  "timestamp": 1725478205.12
}
```

---

## 4. Огляд компонентів системи

| Компонент | Шлях | Призначення |
|-----------|------|-------------|
| **Export Canvas Engine** | `core/obsidian/export_canvas.py` | Чистий Python-серіалізатор для Markdown та JSON Canvas v1.0 з валідацією canonical Vault paths. |
| **Import Canvas Engine** | `core/obsidian/import_canvas.py` | Парсер `.canvas` і `.md` з детермінованим LWW tie-breaker `(updated_at, revision, content_hash)`. |
| **FastAPI WebSocket Router** | `apps/api/routers/canvas_v3_ws.py` | Асинхронний мультиплексор реального часу з захистом від Path Traversal та обробкою подій `OBSIDIAN_SYNC_*`. |
| **React UI Sync Bar** | `apps/web/components/canvas/ObsidianSyncBar.tsx` | Інтерфейсний віджет синхронізації з відображенням статусу та налаштуванням шляху. |
| **Zustand Canvas Store** | `apps/web/store/canvasStore.ts` | Управління клієнтським станом вузлів і з'єднань, RPC-диспетчеризація. |

---

## 5. Верифікація та тестові докази

Специфікація та реалізація повністю покриті автономними модульними та інтеграційними E2E-тестами:
- **Тестові модулі**:
  - `tests/core/test_obsidian_export_import.py` (15 тестів)
  - `tests/canvas/test_obsidian_sync.py` (5 тестів)
- **Команди перевірки**:
  - `./.venv/bin/pytest tests/core/test_obsidian_export_import.py tests/canvas/test_obsidian_sync.py`
  - `bash scripts/verify_all.sh`
- **Результати тестування**:
  - `test_export_five_nodes_to_canvas`: **PASSED** (Генерація коректної JSON Canvas v1.0 структури для 5 нод та 4 ребер).
  - `test_import_canvas_to_five_nodes`: **PASSED** (Зворотній парсинг .canvas з відновленням просторових координат і зв'язків).
  - `test_conflict_resolution_last_write_wins`: **PASSED** (Паралельна модифікація за LWW правилом).
  - `test_websocket_obsidian_sync_path_traversal_rejected`: **PASSED** (Блокування спроб виходу за межі сховища через `../` та абсолютні системні шляхи).
  - `test_websocket_obsidian_sync_canonical_vault_success`: **PASSED** (Успішний експорт/імпорт у межах канонічного Vault).
  - `test_canonical_vault_paths_and_env_overrides`: **PASSED** (Підтвердження канонічних шляхів та коректності перевизначення через змінні середовища).
  - `test_validate_vault_path_success`: **PASSED** (Валідація підкаталогів всередині Vault root).
  - `test_validate_vault_path_traversal_attacks`: **PASSED** (Запобігання та підтвердження `ValueError` для `../..`, `/etc/hosts` тощо).
  - `test_deterministic_lww_tie_breaker_revision`: **PASSED** (Детермінований вибір переможця за ревізією при однакових timestamps).
  - `test_deterministic_lww_tie_breaker_content_hash`: **PASSED** (Детермінований вибір переможця за SHA-256 гешем при однакових timestamps і revisions).
  - `test_export_import_with_revision_and_content_hash`: **PASSED** (Серіалізація та десеріалізація ревізій та гешу у YAML frontmatter).
- **Підсумок**: **20/20 PASSED (100% Green)**.
