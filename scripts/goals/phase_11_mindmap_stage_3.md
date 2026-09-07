<!-- --- DNK-MRH-HEADER ---
mrh_id: "scripts/goals/phase_11_mindmap_stage_3.md"
purpose: "Execution Plan v1.1 for Phase 11 Stage 3 (Obsidian Vault Sync - Task Forest)"
canonical_source: true
alters_files: []
triggers_tasks: []
status: "Completed"
version: "1.2.0"
updated_at: "2026-09-04"
author: "DNK-e.com Maksym & Antigravity Mentor"
--- END DNK-MRH-HEADER --- -->

# ЕТАП 11.3: Obsidian Vault Sync (Task Forest) [COMPLETED]

## МЕТА
Двосторонній синхронізм між Mind Map canvas та Obsidian Vault (`~/Documents/DNK_HUB My Notes/TaskForest/`).
**СТАТУС: ВСІ СЛАЙСИ (3.1, 3.2, 3.3) ПОВНІСТЮ РЕАЛІЗОВАНО ТА ВЕРИФІКОВАНО.**

---

### 🎯 СЛАЙС 3.1: Бекенд експорту/імпорту [STATUS: COMPLETED]

## 📌 ЦІЛЬОВА ДИРЕКТИВА
Створити бекенд-модулі для експорту нод у Markdown + `.canvas` формат та імпорту з `.canvas` → ноди. ВИКОНУЙ НЕГАЙНО.

## 📁 ЦІЛЬОВІ ФАЙЛИ
- [NEW] `core/obsidian/export_canvas.py`
- [NEW] `core/obsidian/import_canvas.py`
- [MODIFY] `apps/api/routers/canvas_v3_ws.py`

## 📋 ТЕХНІЧНІ ВИМОГИ
1. **export_canvas.py:**
   - Експорт нод у Markdown (кожна нода → окремий `.md` файл)
   - Експорт у `.canvas` формат (Obsidian Canvas JSON)
   - Збереження у `~/Documents/DNK_HUB My Notes/TaskForest/`
2. **import_canvas.py:**
   - Парсинг `.canvas` файлів → ноди (position, data, type)
   - Імпорт Markdown файлів → metadata (tags, description)
   - Conflict resolution: last-write-wins
3. **canvas_v3_ws.py:**
   - WebSocket подія `OBSIDIAN_SYNC_REQUEST` → запуск експорту/імпорту
   - Відповідь `OBSIDIAN_SYNC_STATUS` (success/error)

## ✅ DEFINITION OF DONE (DoD)
- ✅ 2 модулі створено (`export_canvas.py`, `import_canvas.py`)
- ✅ WebSocket інтегровано (`canvas_v3_ws.py`)
- ✅ Експорт/імпорт працює на тестових даних
- ✅ `uv run pytest tests/core/test_obsidian_export_import.py` → 100% Green

## 🔍 КОМАНДА ВЕРИФІКАЦІЇ
```bash
./.venv/bin/pytest tests/core/test_obsidian_export_import.py
```

## 🚀 РЕЖИМ ВИКОНАННЯ
**Жодних розмов, одразу код через `write_to_file`.** Після завершення запусти перевірку.

---

### 🎯 СЛАЙС 3.2: Фронтенд синхронізації [STATUS: COMPLETED]

## 📌 ЦІЛЬОВА ДИРЕКТИВА
Створити UI компонент для синхронізації з Obsidian Vault. ВИКОНУЙ НЕГАЙНО.

## 📁 ЦІЛЬОВІ ФАЙЛИ
- [NEW] `apps/web/components/canvas/ObsidianSyncBar.tsx`
- [MODIFY] `apps/web/store/canvasStore.ts`
- [MODIFY] `apps/web/components/canvas/CanvasEngine.tsx`

## 📋 ТЕХНІЧНІ ВИМОГИ
1. **ObsidianSyncBar.tsx:**
   - Кнопки "Export to Obsidian" + "Import from Obsidian"
   - Індикатор статусу (syncing, success, error)
   - Toast-сповіщення після синхронізації
2. **canvasStore.ts:**
   - Action `syncToObsidian(direction: 'export' | 'import')`
   - WebSocket комунікація з бекендом
3. **CanvasEngine.tsx:**
   - Інтеграція `ObsidianSyncBar` у canvas UI (нижня панель)

## ✅ DEFINITION OF DONE (DoD)
- ✅ `ObsidianSyncBar.tsx` створено
- ✅ `canvasStore.ts` action `syncToObsidian` працює
- ✅ `CanvasEngine.tsx` інтегровано SyncBar
- ✅ `npx --prefix apps/web tsc --noEmit` → 0 помилок

## 🔍 КОМАНДА ВЕРИФІКАЦІЇ
```bash
npx --prefix apps/web tsc --project apps/web/tsconfig.json --noEmit
```

## 🚀 РЕЖИМ ВИКОНАННЯ
**Жодних розмов, одразу код.** Після завершення запусти перевірку.

---

### 🎯 СЛАЙС 3.3: E2E тести + верифікація [STATUS: COMPLETED]

## 📌 ЦІЛЬОВА ДИРЕКТИВА
Створити E2E тести для синхронізації з Obsidian та верифікувати Master Quality Gate. ВИКОНУЙ НЕГАЙНО.

## 📁 ЦІЛЬОВІ ФАЙЛИ
- [NEW] `tests/canvas/test_obsidian_sync.py`
- [MODIFY] `scripts/goals/phase_11_mindmap_stage_3.md`

## 📋 ТЕХНІЧНІ ВИМОГИ
1. **test_obsidian_sync.py:**
   - Тест експорту: 5 нод → `.canvas` файл → перевірка JSON
   - Тест імпорту: `.canvas` файл → 5 нод → перевірка position/data
   - Тест conflict resolution: зміни в canvas + зміни в Obsidian → last-write-wins
2. **phase_11_mindmap_stage_3.md:**
   - Оновити статус слайсів (completed)
3. **Master Quality Gate:**
   - Запустити `bash scripts/verify_all.sh`

## ✅ DEFINITION OF DONE (DoD)
- ✅ `test_obsidian_sync.py` створено (3 тести)
- ✅ Всі тести проходять (100% Green)
- ✅ `bash scripts/verify_all.sh` → 100% Green

## 🔍 КОМАНДА ВЕРИФІКАЦІЇ
```bash
bash scripts/verify_all.sh
```

## 🚀 РЕЖИМ ВИКОНАННЯ
**Жодних розмов, одразу код.** Після завершення запусти `verify_all.sh`.
