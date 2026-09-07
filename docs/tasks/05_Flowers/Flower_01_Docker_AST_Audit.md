# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tasks/05_Flowers/Flower_01_Docker_AST_Audit.md"
# purpose: "Canonical documentation and task tracking note"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-09"
# plant_scale: "flower"
# --- END DNK-MRH-HEADER ---

# 🌸 Квітка: Flower_01_Docker_AST_Audit

## 📋 Опис завдання
Повний аудит вихідного коду (codegraph) ядра системи Open Design за допомогою AST-парсеру всередині контейнера Docker з мапінгом усіх сутностей (файли, директорії, класи, функції, імпорти) в базу даних PostgreSQL.

## 🏁 Чек-лист реалізації (Checklist)
- [x] Повне очищення застарілих файлів Task Forest (`docs/tasks/`).
- [x] Відновлення низькорівневого DB модуля `core/dnk_os_memory/db.py` з системи контролю версій.
- [x] Налаштування середовища (інсталяція `psycopg2-binary` та `loguru`).
- [x] Верифікація роботи юніт-тестів `tests/verification/test_code_graph.py` (3 passed).
- [x] Запуск повного AST-сканування за допомогою `scripts/maintenance/generate_code_graph.py`.
- [x] Успішна ін'єкція **23,724 нод** та **31,316 зв'язків** у PostgreSQL базу даних `dnk_hub`.
- [x] Реєстрація та оновлення статусу таски в базі даних (ID завдання #70044 оновлено до `completed`).