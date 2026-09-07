---
id: flower_canvas_research_links
title: "🌸 Квітка: DNK Canvas Research Integration (Phase 2) [COMPLETED PHASE 2]"
type: task_flower
plant_scale: flower
parent_id: bush_5_atom_canvas_Molecules
status: completed
verification_status: completed
tags:
  - dnk-task-forest
  - dnk-task-flower
  - canvas-research-links
---

# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tasks/05_Flowers/Flower_canvas_research_links.md"
# purpose: "Task Flower for implementing competitor, flower, and evidence linking inside DNK Canvas"
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

Реалізувати другу фазу (Phase 2) вбудованого DNK Canvas — бізнес-інтеграцію з конкурентним аналізом та Task Forest.

Забезпечити можливість пов'язувати окремі вузли (nodes через `element_id` з partial index унікальністю) або цілі полотна з профілями конкурентів, завантажувати скріншоти доказів у глобальну бібліотеку активів `canvas_assets` + `canvas_asset_links` (з урахуванням унікальних часткових індексів та ізоляції воркспейсів), та інтегрувати посилання на інсайти, ADR та квітки завдань.

*Увага*: Ця задача перебуває в статусі **WAIT** і фактично розпочнеться після повного успішного завершення та інтеграційного пробігу Phase 1 (Persistence MVP).

---

## ⚡ Чекліст імплементації (Checklist)

- [x] **1. Модель зв'язків та Сховище Активів (Database & S3)**
  - [x] Створити Alembic міграцію для таблиць `canvas_links`, `canvas_assets` та `canvas_asset_links` у схемі `hub_memory`.
  - [x] Налаштувати таблицю `canvas_assets` з ізольованим унікальним індексом `UNIQUE (workspace_id, sha256)` для гарантії tenant isolation та запобігання між-воркспейсним витокам файлів.
  - [x] Налаштувати життєвий цикл статусів активу: `pending_upload ➔ uploaded ➔ verifying ➔ verified` (відхилені завантаження переводяться в `rejected`).
  - [x] Реалізувати унікальність зв'язків у `canvas_asset_links` за допомогою двох часткових індексів для `element_id IS NULL` та `element_id IS NOT NULL` (для усунення багів унікальності `NULL` в PostgreSQL).
  - [x] Створити FastAPI роути для генерації препідписаних посилань `POST /api/v1/canvases/{canvas_id}/assets/presign`:
    - [x] Якщо `sha256` вже присутній у базі для цього воркспейсу зі статусом `verified`, одразу створювати запис у `canvas_asset_links` та повертати існуючий `asset_id` (без повторного завантаження).
  - [x] Реалізувати роут `POST /api/v1/canvases/{canvas_id}/assets/{asset_id}/commit` для фіксації завантаженого активу, переходу через стан `verifying` та валідації розмірів, воркспейс-авторизації і SHA-256 на сервері перед виставленням `verified`.
- [x] **2. Роути зв'язування сутностей (Entity Linking API)**
  - [x] Додати роути `POST /api/v1/canvases/{canvas_id}/links` та `DELETE /api/v1/canvases/{canvas_id}/links/{link_id}`.
  - [x] Реалізувати валідацію `entity_type` (competitor, screenshot, insight, flower, adr, agent_run) та підтримку `element_id`.
  - [x] Створити два часткових унікальних індекси (partial unique indexes) на базі `element_id` (`IS NOT NULL` та `IS NULL`) у `canvas_links` для правильної обробки унікальності лінків у PostgreSQL.
  - [x] Захистити видалення лінків від імені агентів: інтегрувати **Supervisor Approval Gate** для `DELETE /links/{link_id}`, повертати `202 Accepted` у разі очікування підтвердження.
- [x] **3. Інтерфейс інтеграції (Frontend Link Panel & Sidebar)**
  - [x] Додати бічну панель (Sidebar) у Next.js для відображення існуючих зв'язків Canvas.
  - [x] Створити модальне вікно або меню швидкого додавання зв'язків для виділеного елементу (`element_id`) на Excalidraw.
  - [x] Реалізувати візуальне завантаження файлів зображень (Drag-and-Drop скріншотів):
    - [x] Отримати pre-signed URL з бекенду або дублікат-інформацію.
    - [x] Завантажити файл безпосередньо в S3/MinIO, якщо це унікальний файл у воркспейсі.
    - [x] Додати зображення на Excalidraw-сцену, використовуючи посилання на серверну копію (без вбудовування base64).
- [x] **4. Тестування та Верифікація**
  - [x] Написати тести на дублювання document-level лінків скріншотів (спроба завантажити однаковий хендл).
  - [x] Написати тест-кейси на tenant isolation: перевірити, що скріншот з воркспейсу А не може бути отриманий за запитом воркспейсу Б.
  - [x] Перевірити безпеку завантаження файлів (блокування небезпечних MIME-типів на бекенді).

---

## 🔗 Залежності та Зв'язки
- **Батьківський кущ**: `bush_5_atom_canvas_Molecules`
- **Попередні завдання**: `flower_canvas_persistence` (Phase 1)
- **Виконавці**:
  - `dnk-dev-01` (glm-5.2) — Frontend Drag-and-Drop, Sidebar сутностей, Element ID linking UI.
  - `dnk_koder` (codestral-22b) — FastAPI S3 integration with statuses, Link API with element_id, Supervisor Approval Gate.

---

## 🏁 Definition of Done (Критерії завершення)
- [x] Будь-який скріншот завантажується безпосередньо в S3/MinIO за препідписаним URL і рендериться на Canvas.
- [x] Розмір JSON-документа сцени при завантаженні зображень не зростає на розмір файлу (base64 відсутній).
- [x] Елементи з конкретними `element_id` успішно лінкуються з сутностями, зв'язки відображаються у бічній панелі.
- [x] Спроба завантажити однаковий файл повторно у воркспейсі використовує існуючий `storage_key` завдяки SHA-256 перевірці.
- [x] Всі файли відповідають стандартам MRH та мають ліцензію "DNK-INTERNAL".
