---
id: flower_canvas_persistence
title: "🌸 Квітка: DNK Canvas Persistence (Phase 1)"
type: task_flower
plant_scale: flower
parent_id: bush_5_atom_canvas_Molecules
status: completed
verification_status: completed
tags:
  - dnk-task-forest
  - dnk-task-flower
  - canvas-persistence
---

# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tasks/05_Flowers/Flower_canvas_persistence.md"
# purpose: "Task Flower for implementing PostgreSQL and S3 persistence for DNK Canvas"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.3.0"
# updated_at: "2026-08-11"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# --- END DNK-MRH-HEADER ---

## 📌 Опис завдання

Реалізувати першу фазу (Phase 1) вбудованого DNK Canvas — ядро системи персистентності на бекенді (FastAPI + PostgreSQL) та інтеграцію редактора на фронтенді (Next.js 14 + Excalidraw).

Забезпечити надійне збереження сцени, версіонування змін, запобігання перетиранию даних (transaction-safe Optimistic Concurrency Control з row locks) та автоматичне збереження.

---

## ⚡ Чекліст імплементації (Checklist)

- [x] **1. База даних та Міграції (PostgreSQL & Alembic)**
  - [x] Створити Alembic міграцію для схеми `hub_memory` та таблиць `canvas_documents` і `canvas_revisions`.
  - [x] Налаштувати унікальний індекс на `(document_id, revision_number)`.
  - [x] Додати серверну валідацію SHA-256 чексуми для вхідних JSON-сцен.
- [x] **2. Core API (FastAPI)**
  - [x] Створити Pydantic схеми для вхідних та вихідних payload-ів.
  - [x] Створити роут `POST /api/v1/canvases` для ініціалізації документа.
  - [x] Створити роут `GET /api/v1/canvases/{canvas_id}` для отримання поточної сцени.
  - [x] Реалізувати роут `PUT /api/v1/canvases/{canvas_id}/scene` з транзакційним Optimistic Concurrency Control:
    - [x] Розпочати транзакцію та заблокувати рядок через `SELECT ... FOR UPDATE`.
    - [x] Перевірити, чи поточна `revision_number` в базі відповідає очікуваній.
    - [x] Якщо ні ➔ ROLLBACK та повернути `409 Conflict`.
    - [x] Якщо так ➔ записати новий рядок у `canvas_revisions` та оновити `canvas_documents` в єдиній транзакції.
  - [x] Заборонити звичайний `force-commit`; реалізувати його виключно через `force-commit` ендпоінт, захищений Supervisor Approval Gate.
- [x] **3. Frontend MVP (Next.js + Excalidraw)**
  - [x] Налаштувати динамічний імпорт (`ssr: false`) для `@excalidraw/excalidraw` у роуті `/workspace/[workspace_id]/canvas/[canvas_id]` з прямим підключенням до FastAPI.
  - [x] Додати індикатор збереження (Save / Last Saved).
  - [x] Налаштувати дебаунс автозбереження (3 секунди) з відстеженням брудного стану (dirty state).
  - [x] Реалізувати гарячу клавішу `cmd+s` / `ctrl+s` для негайного примусового збереження.
  - [x] Додати обробку конфлікту злиття (`409 Conflict`): показати вікно діалогу з можливістю завантажити серверний стан або надіслати запит на Supervisor Gate для примусового збереження.
- [x] **4. Експорт та Імпорт**
  - [x] Інтегрувати серіалізаційне API Excalidraw на клієнті для експорту в `.excalidraw`, PNG та SVG.
- [x] **5. Тестування (Unit & Integration)**
  - [x] Написати юніт-тести для `PUT /scene` на перевірку 409 Conflict під навантаженням (конкурентні запити).
  - [x] Написати інтеграційний тест для Alembic міграції.

---

## 🔗 Залежності та Зв'язки
- **Батьківський кущ**: `bush_5_atom_canvas_Molecules`
- **Виконавці**:
  - `dnk-dev-01` (glm-5.2) — Frontend UI, React інтеграція, Autosave, Conflict Modal.
  - `dnk_koder` (codestral-22b) — FastAPI роути, Alembic міграція, transaction locking, тестування.
  - `dnk_governance_companion` (gemma-4-31b) — Перевірка відповідності MRH, ліцензійний аудит.

---

## 🏁 Definition of Done (Критерії завершення)
- [x] Таблиці документів та ревізій успішно мігровані через Alembic в PostgreSQL.
- [x] Сцена відновлюється з бази після повного перезавантаження сторінки або очищення кешу браузера.
- [x] Спроба одночасного збереження двома клієнтами з однаковим `expected_revision` призводить до помилки `409 Conflict` для другого клієнта завдяки `SELECT FOR UPDATE`.
- [x] Кожна зміна сцени створює новий запис у `canvas_revisions` зі збільшеним `revision_number` та валідною чексумою.
- [x] Всі специфікаційні файли мають ліцензію "DNK-INTERNAL" та заголовок MRH.
- [x] Написані тести проходять успішно.
