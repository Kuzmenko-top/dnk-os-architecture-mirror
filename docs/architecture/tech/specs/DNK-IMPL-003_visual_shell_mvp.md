<!-- --- DNK-MRH-HEADER ---
mrh_id: "docs_tech_specs_DNK-IMPL-003_visual_shell_mvp"
purpose: "Technical specification for the Visual Shell (Robochyi Kabinet) MVP"
author: "DNK-e.com Maksym"
license: "DNK-INTERNAL"
status: "Active"
version: "1.0.0"
updated_at: "2026-08-11"
--- END DNK-MRH-HEADER -->

# DNK-IMPL-003: Visual Shell (Robochyi Kabinet) — MVP

**Ціль:**
Реалізувати перший робочий кабінет (Visual Shell) з одним canvas-вікном і одним агентом, який оновлює артефакт.

---

### 1. Архітектура

#### Frontend (Next.js 14/15 + Tailwind v4)
- `apps/web/app/canvas/[canvasId]/page.tsx` — сторінка canvas, яка інтегрує компоненти CanvasEditor та ArtifactPanel.
- `apps/web/components/canvas/CanvasEditor.tsx` — редактор для візуалізації та зміни стану вузлів кавасу.
- `apps/web/components/canvas/ArtifactPanel.tsx` — панель перегляду згенерованого Markdown артефакту та можливістю ручного редагування.

#### Backend (FastAPI)
- `apps/api/routers/canvas.py` — CRUD для створення, отримання та оновлення кавасів.
- `apps/api/routers/agent.py` — запуск агентних флоу (Research -> Write -> Validate).
- `apps/api/routers/artifact.py` — перегляд та оновлення Markdown артефакту.

#### Agent Flow
- `core/flows/research_write_validate.py` — реалізує послідовність кроків (Research -> Write -> Validate) з інтеграцією в Timeline DB та Security Gate.

---

### 2. API Endpoints

- `POST /canvas` — створити новий canvas.
- `GET /canvas/{canvas_id}` — отримати поточний стан canvas.
- `PUT /canvas/{canvas_id}` — оновити стан canvas (ім'я, вузли тощо).
- `POST /agent/run` — запуск агентного флоу з параметрами `canvas_id`, `flow_type` та `query`.
- `GET /artifact/{canvas_id}` — отримати поточний артефакт для вказаного кавасу.
- `PUT /artifact/{canvas_id}` — оновити вміст артефакту (проходить через Security Gate).

---

### 3. Інтеграція з Timeline DB + Security Gate

#### Timeline DB
- Кожен крок виконання флоу записується в Postgres Timeline DB (з автоматичним gracefully деградуванням в in-memory лог, якщо база даних недоступна).
- Використовуються стандартні типи подій:
  - `flow_started`
  - `research_completed`
  - `write_completed`
  - `validate_completed`
  - `flow_completed`

#### Security Gate
- Оновлення вмісту артефакту (через API або ручне редагування) вважається ризиковою дією.
- Перед записом викликається `SecurityGateService.evaluate_policy` для перевірки відповідності політикам безпеки.
- Якщо політика повертає `allowed=False`, викидається виняток `SecurityGateDenied` та повертається статус-код `403 Forbidden` для API клієнтів.

---

### 4. Конфігурація

Файл `apps/api/config/visual_shell_config.py` містить наступні параметри:
- `VISUAL_SHELL_DEFAULT_FLOW` (str, default=`research_write_validate`).
- `VISUAL_SHELL_MAX_ARTIFACT_SIZE` (int, default=1MB).
- `VISUAL_SHELL_POLLING_INTERVAL` (int, default=5000ms).

---

### 5. Тестування

Створено повний набір автоматизованих тестів у файлі `tests/verification/test_visual_shell.py`, що охоплює:
1. `test_create_canvas` — створення canvas.
2. `test_get_canvas` — отримання canvas.
3. `test_update_canvas` — оновлення canvas.
4. `test_run_agent_flow` — запуск агентних флоу.
5. `test_artifact_update` — оновлення артефакту.
6. `test_security_gate_integration` — оновлення через Security Gate та перехоплення помилки.
7. `test_timeline_db_integration` — верифікація запису всіх 5 кроків у Timeline DB.
